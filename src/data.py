import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
from src.utils import haversine_distance, load_config

@dataclass
class Farm:
    id: str
    zone: str
    area_ha: float
    lat: float
    lon: float
    
    # Pre-calculated distances to each STP (stp_id -> km)
    distances: Dict[str, float] = None 

@dataclass
class STP:
    id: str
    daily_output: float
    max_storage: float
    lat: float
    lon: float
    
    # State
    current_storage: float = 0.0

class DataManager:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.config = load_config(f"{data_dir}/config.json")
        
        # Load Raw Data
        self.stp_df = pd.read_csv(f"{data_dir}/stp_registry.csv")
        self.farm_df = pd.read_csv(f"{data_dir}/farm_locations.csv")
        self.weather_df = pd.read_csv(f"{data_dir}/daily_weather_2025.csv")
        self.n_demand_df = pd.read_csv(f"{data_dir}/daily_n_demand.csv")
        
        # Processed Objects
        self.stps: Dict[str, STP] = {}
        self.farms: Dict[str, Farm] = {}
        
        self._initialize_objects()
        
    def _initialize_objects(self):
        # Initialize STPs
        for _, row in self.stp_df.iterrows():
            self.stps[row['stp_id']] = STP(
                id=row['stp_id'],
                daily_output=row['daily_output_tons'],
                max_storage=row['storage_max_tons'],
                lat=row['lat'],
                lon=row['lon']
            )
            
        # Initialize Farms
        radius = self.config['logistics_constants']['haversine_earth_radius_km']
        for _, row in self.farm_df.iterrows():
            farm = Farm(
                id=row['farm_id'],
                zone=row['zone'],
                area_ha=row['area_ha'],
                lat=row['lat'],
                lon=row['lon'],
                distances={}
            )
            
            # Pre-calc distances
            for stp_id, stp in self.stps.items():
                dist = haversine_distance(stp.lat, stp.lon, farm.lat, farm.lon, radius)
                farm.distances[stp_id] = dist
                
            self.farms[row['farm_id']] = farm

    def get_weather_forecast(self, date: str, zone: str, lookahead_days: int = 5) -> List[float]:
        """
        Returns rain list for [date, date+lookahead-1].
        If date is beyond data, assumes 0.0 (or handles gracefully).
        """
        # We need to find the index of the date
        try:
            start_idx = self.weather_df[self.weather_df['date'] == date].index[0]
            # Slices are exclusive at the end for python lists, but this is a dataframe index slice?
            # actually iloc includes start, excludes end.
            # We want 'lookahead_days' rows potentially.
            # e.g. if lookahead is 5, we want idx, idx+1, idx+2, idx+3, idx+4
            
            rainfall = self.weather_df.iloc[start_idx : start_idx + lookahead_days][zone].tolist()
            
            # Pad with 0.0 if we hit the end of the year
            if len(rainfall) < lookahead_days:
                rainfall += [0.0] * (lookahead_days - len(rainfall))
                
            return rainfall
        except IndexError:
            # Date not found
            return [0.0] * lookahead_days

    def get_daily_demand_per_ha(self, date: str) -> Dict[str, float]:
        """
        Returns {farm_id: n_demand_kg_per_ha} for the specific date.
        """
        try:
            row = self.n_demand_df[self.n_demand_df['date'] == date]
            if row.empty:
                return {}
            
            # Convert row to dict, dropping 'date'
            demands = row.iloc[0].to_dict()
            del demands['date']
            return demands
        except Exception as e:
            print(f"Error getting demand for {date}: {e}")
            return {}
