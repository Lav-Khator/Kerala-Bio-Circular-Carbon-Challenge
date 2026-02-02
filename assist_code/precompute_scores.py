import pandas as pd
import numpy as np
import math
import os
import json

"""
ASSIST SCRIPT: Score Pre-Computer
=================================
Purpose:
- Re-runs the full physics scoring engine on the final `solution.csv`.
- Generates `data/daily_scores.json` which maps every single date to the cumulative score.
- This ensures the dashboard graph is pixel-perfect accurate to the Python scoring logic.
"""

# Constants
N_CONTENT = 25.0
EARTH_RADIUS = 6371.0

def haversine(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS * c

def generate_daily_scores(base_dir):
    print("Loading data for pre-computation...")
    
    # Load Solution
    sol_path = os.path.join(base_dir, 'solution', 'solution.csv')
    sol_df = pd.read_csv(sol_path)
    sol_df['date'] = pd.to_datetime(sol_df['date'])
    sol_df = sol_df[sol_df['tons_delivered'] > 0]
    
    # Load Reference Data
    farms_df = pd.read_csv(os.path.join(base_dir, 'data', 'farm_locations.csv')).set_index('farm_id')
    stps_df = pd.read_csv(os.path.join(base_dir, 'data', 'stp_registry.csv')).set_index('stp_id')
    demand_df = pd.read_csv(os.path.join(base_dir, 'data', 'daily_n_demand.csv'))
    demand_df['date'] = pd.to_datetime(demand_df['date'])
    
    # Initialize State
    cumulative_score = 0.0
    daily_scores = []
    stp_storage = {stp_id: 0.0 for stp_id in stps_df.index}
    
    # Group solution by date for faster access
    sol_by_date = sol_df.groupby('date')
    dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    
    print(f"Processing {len(dates)} days...")
    
    for date in dates:
        day_score = 0.0
        date_str = date.strftime('%Y-%m-%d')
        
        # 1. Process Deliveries (Credits & Transport)
        if date in sol_by_date.groups:
            day_deliveries = sol_by_date.get_group(date)
            
            # Get Demand for this date
            demand_row = demand_df[demand_df['date'] == date]
            
            for _, row in day_deliveries.iterrows():
                tons = row['tons_delivered']
                farm_id = row['farm_id']
                stp_id = row['stp_id']
                
                # A. Soil Credit
                day_score += tons * 200
                
                # B. Nitrogen & Leaching
                if not demand_row.empty and farm_id in demand_row.columns:
                    demand_kg_ha = demand_row[farm_id].values[0]
                    # Important: Parse float in case of string/whitespace issues, though pandas usually handles if clean
                    if pd.notna(demand_kg_ha):
                        farm_area = farms_df.loc[farm_id, 'area_ha']
                        total_demand_kg = demand_kg_ha * farm_area
                        
                        n_applied_kg = tons * N_CONTENT
                        n_uptake_kg = min(n_applied_kg, total_demand_kg)
                        
                        # N Credit
                        day_score += n_uptake_kg * 5.0
                        
                        # Leaching Penalty
                        limit_kg = total_demand_kg * 1.1
                        excess_n = max(0, n_applied_kg - limit_kg)
                        day_score -= excess_n * 10.0
                
                # C. Transport Cost
                farm = farms_df.loc[farm_id]
                stp = stps_df.loc[stp_id]
                dist = haversine(farm['lat'], farm['lon'], stp['lat'], stp['lon'])
                trucks = math.ceil(tons / 10.0)
                transport_cost = dist * 0.9 * trucks
                day_score -= transport_cost
        
        # 2. Process STP Storage & Overflow
        # Add daily output
        for stp_id, stp in stps_df.iterrows():
            stp_storage[stp_id] += stp['daily_output_tons']
            
        # Subtract deliveries
        if date in sol_by_date.groups:
            day_deliveries = sol_by_date.get_group(date)
            for _, delivery in day_deliveries.iterrows():
                stp_storage[delivery['stp_id']] -= delivery['tons_delivered']
        
        # Check overflow
        daily_overflow = 0.0
        for stp_id, stp in stps_df.iterrows():
            if stp_storage[stp_id] > stp['storage_max_tons']:
                overflow = stp_storage[stp_id] - stp['storage_max_tons']
                daily_overflow += overflow * 1000.0
                stp_storage[stp_id] = stp['storage_max_tons'] # Reset
        
        day_score -= daily_overflow
        
        # Accumulate
        cumulative_score += day_score
        
        # Store rounded for JSON compactness
        daily_scores.append({
            'date': date_str,
            'score': round(cumulative_score, 2)
        })
        
    final_score = daily_scores[-1]['score']
    print(f"Final Calculated Score: {final_score:,.2f}")
    
    # Save to JSON
    output_path = os.path.join(base_dir, 'data', 'daily_scores.json')
    with open(output_path, 'w') as f:
        json.dump(daily_scores, f)
    
    print(f"Saved daily scores to {output_path}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generate_daily_scores(base_dir)
