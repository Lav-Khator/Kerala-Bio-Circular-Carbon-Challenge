"""
ASSIST SCRIPT: KPI Analyzer
===========================
Performance Metrics Calculator for Biosolids Delivery Solution

This script calculates four key performance indicators to evaluate the quality
and effectiveness of the biosolids delivery optimization:

1. NET CARBON CREDITS: Total environmental impact (kg CO₂)
   - Combines all benefits (soil carbon, nitrogen offset) minus all costs
   - Lower (more negative) is better
   
2. NITROGEN PRECISION: How well nitrogen supply matches demand (%)
   - Measures efficiency of nutrient delivery
   - Target: ~100% (meeting demand without excess)
   
3. LOGISTICS EFFICIENCY: Delivery productivity (tons/km)
   - Higher values indicate better route optimization
   - Measures tons delivered per kilometer traveled
   
4. RAIN-LOCK RESILIENCE: Ability to operate during monsoon (%)
   - Percentage of deliveries made during monsoon months (Jun-Sep)
   - Higher values show better weather adaptation

All calculations are independent and based solely on the solution CSV file.
"""

import pandas as pd
import numpy as np
import math
import os
import sys

# Physical and economic constants from problem specification
N_CONTENT = 25.0  # Nitrogen content: 25 kg N per ton of biosolids (2.5%)
EARTH_RADIUS = 6371.0  # Earth radius in km for distance calculations

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using haversine formula"""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS * c

def calculate_metrics(base_dir, solution_path):
    """Calculate all performance metrics"""
    
    print("=" * 60)
    print("PERFORMANCE METRICS ANALYSIS")
    print("=" * 60)
    
    # Load data
    print("\nLoading data...")
    sol_df = pd.read_csv(solution_path)
    sol_df['date'] = pd.to_datetime(sol_df['date'])
    sol_df = sol_df[sol_df['tons_delivered'] > 0]  # Only actual deliveries
    
    farms_df = pd.read_csv(os.path.join(base_dir, 'data', 'farm_locations.csv')).set_index('farm_id')
    stps_df = pd.read_csv(os.path.join(base_dir, 'data', 'stp_registry.csv')).set_index('stp_id')
    demand_df = pd.read_csv(os.path.join(base_dir, 'data', 'daily_n_demand.csv'))
    demand_df['date'] = pd.to_datetime(demand_df['date'])
    weather_df = pd.read_csv(os.path.join(base_dir, 'data', 'daily_weather_2025.csv'))
    weather_df['date'] = pd.to_datetime(weather_df['date'])
    
    # ========================================
    # METRIC 1: Net Carbon Credits
    # ========================================
    # This metric calculates the total environmental impact by combining:
    # BENEFITS: Soil carbon sequestration + Synthetic fertilizer offset
    # COSTS: Transportation emissions + Nitrogen leaching + STP overflow
    print("\n" + "=" * 60)
    print("1. NET CARBON CREDITS")
    print("=" * 60)
    
    # Initialize accumulators for each component
    total_credits = 0.0      # Positive: carbon sequestration + N offset
    total_transport = 0.0    # Negative: truck emissions
    total_leaching = 0.0     # Negative: excess nitrogen penalty
    total_overflow = 0.0     # Negative: STP overflow penalty
    
    # Calculate credits and penalties for each delivery
    for _, row in sol_df.iterrows():
        tons = row['tons_delivered']
        farm_id = row['farm_id']
        stp_id = row['stp_id']
        date = row['date']
        
        # BENEFIT 1: Soil organic carbon gain (200 kg CO₂ per ton biosolids)
        soil_credit = tons * 200
        total_credits += soil_credit
        
        # BENEFIT 2: Synthetic nitrogen fertilizer offset
        # Biosolids provide nitrogen, reducing need for synthetic fertilizer
        demand_row = demand_df[demand_df['date'] == date]
        if not demand_row.empty and farm_id in demand_row.columns:
            demand_kg_ha = demand_row[farm_id].values[0]
            farm_area = farms_df.loc[farm_id, 'area_ha']
            total_demand_kg = demand_kg_ha * farm_area
            
            # Calculate nitrogen applied (biosolids contain 25 kg N per ton)
            n_applied_kg = tons * N_CONTENT
            # Calculate nitrogen actually used by crops (capped at demand)
            n_uptake_kg = min(n_applied_kg, total_demand_kg)
            # Credit: 5 kg CO₂ saved per kg N (synthetic fertilizer avoided)
            n_credit = n_uptake_kg * 5.0
            total_credits += n_credit
            
            # PENALTY 1: Nitrogen leaching (excess nitrogen pollutes groundwater)
            # Allow 10% buffer above demand before penalizing
            limit_kg = total_demand_kg * 1.1
            excess_n = max(0, n_applied_kg - limit_kg)
            # Penalty: 10 kg CO₂ per kg excess nitrogen
            leaching_penalty = excess_n * 10.0
            total_leaching += leaching_penalty
        
        # PENALTY 2: Transportation cost (truck emissions)
        farm = farms_df.loc[farm_id]
        stp = stps_df.loc[stp_id]
        # Calculate distance using haversine formula (great circle distance)
        dist = haversine(farm['lat'], farm['lon'], stp['lat'], stp['lon'])
        # Calculate number of trucks needed (10-ton capacity per truck)
        trucks = math.ceil(tons / 10.0)
        # Cost: 0.9 kg CO₂ per km per truck
        transport_cost = dist * 0.9 * trucks
        total_transport += transport_cost
    
    # PENALTY 3: STP overflow (storage capacity exceeded)
    # Simulate daily STP storage levels to calculate overflow penalties
    print("\nSimulating STP storage to calculate overflow...")
    stp_storage = {stp_id: 0.0 for stp_id in stps_df.index}
    total_overflow = 0.0
    
    # Process each day of the year
    dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    sol_by_date = sol_df.groupby('date')
    
    for date in dates:
        # Step 1: Add daily biosolids production at each STP
        for stp_id, stp in stps_df.iterrows():
            stp_storage[stp_id] += stp['daily_output_tons']
        
        # Step 2: Subtract deliveries made this day
        if date in sol_by_date.groups:
            day_deliveries = sol_by_date.get_group(date)
            for _, delivery in day_deliveries.iterrows():
                stp_storage[delivery['stp_id']] -= delivery['tons_delivered']
        
        # Step 3: Calculate overflow penalty if storage exceeds capacity
        for stp_id, stp in stps_df.iterrows():
            if stp_storage[stp_id] > stp['storage_max_tons']:
                overflow = stp_storage[stp_id] - stp['storage_max_tons']
                # Penalty: 1000 kg CO₂ per ton of overflow
                total_overflow += overflow * 1000
                # Reset storage to max to prevent accumulation
                stp_storage[stp_id] = stp['storage_max_tons']    
    net_carbon_credits = total_credits - total_transport - total_leaching - total_overflow
    
    print(f"Synthetic N Offset + SOC Gain:  {total_credits:,.2f} kg CO₂")
    print(f"Transport Cost:                 -{total_transport:,.2f} kg CO₂")
    print(f"Leaching Penalty:               -{total_leaching:,.2f} kg CO₂")
    print(f"Overflow Penalty:               -{total_overflow:,.2f} kg CO₂")
    print(f"\n{'─' * 60}")
    print(f"NET CARBON CREDITS:             {net_carbon_credits:,.2f} kg CO₂")
    
    # ========================================
    # METRIC 2: Nitrogen Precision
    # ========================================
    # Measures how well nitrogen delivery matches biological demand
    # Target: 100% (meeting all demand without excess waste)
    print("\n" + "=" * 60)
    print("2. NITROGEN PRECISION")
    print("=" * 60)
    
    # Calculate total nitrogen delivered through biosolids
    # (Biosolids contain 2.5% nitrogen = 25 kg N per ton)
    total_n_delivered = sol_df['tons_delivered'].sum() * N_CONTENT
    
    # Calculate total biological nitrogen demand across ALL farms for entire year
    # This represents what crops actually need for optimal growth
    total_n_demand = 0.0
    for _, demand_row in demand_df.iterrows():
        for farm_id in farms_df.index:
            if farm_id in demand_row.index:
                demand_kg_ha = demand_row[farm_id]
                if pd.notna(demand_kg_ha):
                    farm_area = farms_df.loc[farm_id, 'area_ha']
                    n_demand = demand_kg_ha * farm_area
                    total_n_demand += n_demand
    
    # Calculate precision ratio
    # <100%: Under-application (demand not met)
    # ~100%: Optimal (demand perfectly matched)
    # >100%: Over-application (excess nitrogen wasted/pollutes)
    nitrogen_precision = total_n_delivered / total_n_demand if total_n_demand > 0 else 0
    
    print(f"Total N Delivered:              {total_n_delivered:,.2f} kg")
    print(f"Total Biological N Demand:      {total_n_demand:,.2f} kg")
    print(f"  (All farms, all 365 days)")
    print(f"\n{'─' * 60}")
    print(f"NITROGEN PRECISION:             {nitrogen_precision:.4f} ({nitrogen_precision*100:.2f}%)")
    
    if nitrogen_precision < 0.5:
        print(f"  ⚠️  Under-application: Only {nitrogen_precision*100:.1f}% of demand met")
    elif nitrogen_precision > 1.1:
        print(f"  ⚠️  Over-application: {(nitrogen_precision-1)*100:.1f}% excess nitrogen")
    else:
        print(f"  ✓  Well-matched to demand")
    
    # ========================================
    # METRIC 3: Logistics Efficiency
    # ========================================
    # Measures delivery productivity: tons delivered per kilometer traveled
    # Higher values indicate better route optimization and fuel efficiency
    print("\n" + "=" * 60)
    print("3. LOGISTICS EFFICIENCY")
    print("=" * 60)
    
    total_tons_delivered = sol_df['tons_delivered'].sum()
    total_distance = 0.0
    
    # Calculate total round-trip distance for all deliveries
    for _, row in sol_df.iterrows():
        farm_id = row['farm_id']
        stp_id = row['stp_id']
        
        farm = farms_df.loc[farm_id]
        stp = stps_df.loc[stp_id]
        dist = haversine(farm['lat'], farm['lon'], stp['lat'], stp['lon'])
        
        # Round trip distance (STP → Farm → STP)
        total_distance += dist * 2
    
    logistics_efficiency = total_tons_delivered / total_distance if total_distance > 0 else 0
    
    print(f"Total Tons Delivered:           {total_tons_delivered:,.2f} tons")
    print(f"Total Round-trip Distance:      {total_distance:,.2f} km")
    print(f"\n{'─' * 60}")
    print(f"LOGISTICS EFFICIENCY:           {logistics_efficiency:.4f} tons/km")
    
    # ========================================
    # METRIC 4: Rain-Lock Resilience
    # ========================================
    # Measures ability to maintain operations during monsoon season
    # Higher percentage shows better weather adaptation and planning
    print("\n" + "=" * 60)
    print("4. RAIN-LOCK RESILIENCE")
    print("=" * 60)
    
    # Kerala monsoon season: June-September (months 6-9)
    monsoon_months = [6, 7, 8, 9]
    
    total_deliveries = len(sol_df)
    monsoon_deliveries = len(sol_df[sol_df['date'].dt.month.isin(monsoon_months)])
    
    # Calculate percentage of deliveries made during challenging monsoon period
    rain_lock_resilience = monsoon_deliveries / total_deliveries if total_deliveries > 0 else 0
    
    print(f"Deliveries During Monsoon:      {monsoon_deliveries:,}")
    print(f"Total Annual Deliveries:        {total_deliveries:,}")
    print(f"\n{'─' * 60}")
    print(f"RAIN-LOCK RESILIENCE:           {rain_lock_resilience:.4f} ({rain_lock_resilience*100:.2f}%)")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("SUMMARY OF ALL METRICS")
    print("=" * 60)
    print(f"1. Net Carbon Credits:          {net_carbon_credits:,.2f} kg CO₂")
    print(f"2. Nitrogen Precision:          {nitrogen_precision:.4f} ({nitrogen_precision*100:.2f}%)")
    print(f"3. Logistics Efficiency:        {logistics_efficiency:.4f} tons/km")
    print(f"4. Rain-Lock Resilience:        {rain_lock_resilience:.4f} ({rain_lock_resilience*100:.2f}%)")
    print("=" * 60)
    
    return {
        'net_carbon_credits': net_carbon_credits,
        'nitrogen_precision': nitrogen_precision,
        'logistics_efficiency': logistics_efficiency,
        'rain_lock_resilience': rain_lock_resilience
    }

if __name__ == '__main__':
    # Get base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Use command-line argument if provided, otherwise default
    if len(sys.argv) > 1:
        solution_path = sys.argv[1]
    else:
        solution_path = os.path.join(base_dir, 'solution', 'solution.csv')
    
    print(f"Analyzing solution: {solution_path}\n")
    
    metrics = calculate_metrics(base_dir, solution_path)
