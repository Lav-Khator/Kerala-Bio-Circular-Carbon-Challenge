import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import DataManager
from src.simulator import BiosolidSimulator
from corrected_solver import CorrectedSolver

"""
MAIN SIMULATION HARNESS
=======================
This script acts as the central execution engine for the Kerala Carbon Challenge 2025 solution.

Workflow:
1.  **Initialize Environment**: Loads DataManager (Farms/STPs), Simulator (Physics Engine), and Solver (Optimization Logic).
2.  **Temporal Loop**: Iterates through every day of 2025 (Jan 1 - Dec 31).
    - Checks daily weather and demand constraints.
    - Executes the solver's `solve_day` logic to determine optimal truck movements.
    - Updates simulator state (tank levels, farm N saturation).
3.  **Result Aggregation**: Compiles a CSV submission file spanning all 250 farms x 365 days.

Output: `solution/solution.csv` (The final submission artifact)
"""

def run_simulation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    output_dir = os.path.join(base_dir, 'solution')
    os.makedirs(output_dir, exist_ok=True)
    
    dm = DataManager(data_dir)
    sim = BiosolidSimulator(dm)
    solver = CorrectedSolver(dm, sim)
    
    year = 2025
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    curr_date = start_date
    daily_actions = {}
    
    print(f"Running CORRECTED Solver (Fixed Soil Credit Bug)...")
    
    farm_closest_stp = {}
    for farm_id, farm in dm.farms.items():
        closest = sorted(farm.distances.items(), key=lambda x: x[1])[0][0]
        farm_closest_stp[farm_id] = closest

    while curr_date <= end_date:
        date_str = curr_date.strftime("%Y-%m-%d")
        actions = solver.solve_day(date_str)
        daily_actions[date_str] = actions
        sim.run_day(date_str, actions)
        
        if curr_date.day == 1:
            print(f"Processing {date_str}...")
            
        curr_date += timedelta(days=1)
        
    output_path = os.path.join(output_dir, "solution.csv")
    print(f"Saving to {output_path}...")
    
    action_map = {}
    for date_str, action_list in daily_actions.items():
        for action in action_list:
            action_map[(date_str, action.farm_id)] = (action.stp_id, action.amount_tons)

    all_rows = []
    all_dates = []
    d = date(year, 1, 1)
    while d <= end_date:
        all_dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
        
    sorted_farm_ids = sorted(dm.farms.keys())
    
    for farm_id in sorted_farm_ids:
        closest_stp = farm_closest_stp.get(farm_id, "STP_TVM")
        for date_str in all_dates:
            key = (date_str, farm_id)
            if key in action_map:
                stp_id, amount = action_map[key]
                all_rows.append({'date': date_str, 'stp_id': stp_id, 'farm_id': farm_id, 'tons': amount})
            else:
                all_rows.append({'date': date_str, 'stp_id': closest_stp, 'farm_id': farm_id, 'tons': 0.0})

    with open(output_path, "w") as f:
        f.write("id,date,stp_id,farm_id,tons_delivered\n")
        row_id = 0
        for row in all_rows:
            f.write(f"{row_id},{row['date']},{row['stp_id']},{row['farm_id']},{row['tons']:.2f}\n")
            row_id += 1
                
    print(f"Done! Generated {row_id} rows.")

if __name__ == "__main__":
    run_simulation()
