import pandas as pd
import numpy as np
import math
import os
import json

"""
ASSIST SCRIPT: Summary JSON Generator
=====================================
Purpose:
- Calculates high-level metrics (Optimization Score, Logistics Efficiency, Resilience).
- Exports these metrics to `solution/summary_metrics.json`.
- This JSON is consumed by the Dashboard HTML to display the "Big Number" KPIs.
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

def generate_summary(base_dir):
    print("Calculating metrics for summary JSON...")
    
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
    
    # Initialize Accumulators
    total_soil_credit = 0.0
    total_n_credit = 0.0
    total_transport_cost = 0.0
    total_leaching_penalty = 0.0
    total_overflow_penalty = 0.0
    total_overflow_tons = 0.0
    
    stp_storage = {stp_id: 0.0 for stp_id in stps_df.index}
    
    # Group solution by date
    sol_by_date = sol_df.groupby('date')
    dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    
    for date in dates:
        # 1. Process Deliveries
        if date in sol_by_date.groups:
            day_deliveries = sol_by_date.get_group(date)
            demand_row = demand_df[demand_df['date'] == date]
            
            for _, row in day_deliveries.iterrows():
                tons = row['tons_delivered']
                farm_id = row['farm_id']
                stp_id = row['stp_id']
                
                # Credits
                total_soil_credit += tons * 200
                
                if not demand_row.empty and farm_id in demand_row.columns:
                    demand_kg_ha = demand_row[farm_id].values[0]
                    if pd.notna(demand_kg_ha):
                        farm_area = farms_df.loc[farm_id, 'area_ha']
                        total_demand_kg = demand_kg_ha * farm_area
                        n_applied_kg = tons * N_CONTENT
                        n_uptake_kg = min(n_applied_kg, total_demand_kg)
                        total_n_credit += n_uptake_kg * 5.0
                        
                        limit_kg = total_demand_kg * 1.1
                        excess_n = max(0, n_applied_kg - limit_kg)
                        total_leaching_penalty += excess_n * 10.0
                
                # Transport
                farm = farms_df.loc[farm_id]
                stp = stps_df.loc[stp_id]
                dist = haversine(farm['lat'], farm['lon'], stp['lat'], stp['lon'])
                trucks = math.ceil(tons / 10.0)
                transport_cost = dist * 0.9 * trucks
                total_transport_cost += transport_cost
        
        # 2. Process STP Storage & Overflow
        for stp_id, stp in stps_df.iterrows():
            stp_storage[stp_id] += stp['daily_output_tons']
            
        if date in sol_by_date.groups:
            day_deliveries = sol_by_date.get_group(date)
            for _, delivery in day_deliveries.iterrows():
                stp_storage[delivery['stp_id']] -= delivery['tons_delivered']
        
        for stp_id, stp in stps_df.iterrows():
            if stp_storage[stp_id] > stp['storage_max_tons']:
                overflow = stp_storage[stp_id] - stp['storage_max_tons']
                total_overflow_tons += overflow
                total_overflow_penalty += overflow * 1000.0
                stp_storage[stp_id] = stp['storage_max_tons']
    
    total_net_score = (total_soil_credit + total_n_credit) - total_transport_cost - total_leaching_penalty - total_overflow_penalty
    total_penalty = total_transport_cost + total_leaching_penalty + total_overflow_penalty
    total_biosolids = sol_df['tons_delivered'].sum()
    
    metrics = {
        "total_net_carbon_score": round(total_net_score, 2),
        "total_credits_gained": round(total_soil_credit + total_n_credit, 2),
        "total_penalty": round(total_penalty, 2),
        "total_emissions_penalty": round(total_transport_cost, 2),
        "total_operational_penalties": round(total_leaching_penalty + total_overflow_penalty, 2),
        "total_biosolids_delivered_tons": round(total_biosolids, 2),
        "total_stp_overflow_tons": round(total_overflow_tons, 2)
    }
    
    # Save
    output_path = os.path.join(base_dir, 'solution', 'summary_metrics.json')
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=4)
        
    print(f"Updated {output_path}")
    print(json.dumps(metrics, indent=4))

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generate_summary(base_dir)
