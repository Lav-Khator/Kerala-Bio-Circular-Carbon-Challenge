import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import os
import json

"""
ASSIST SCRIPT: Dashboard GIF Generator
======================================
Purpose: 
- Analyzes daily scores to identify the "Most Efficient Month".
- Generates a visual GIF animation (`dashboard_preview.gif`) of truck movements for that month.
- Used for creating preview assets for the project documentation.
"""

# Allow running from src/ or root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import DataManager

def create_dashboard(data_dir: str, solution_path: str, output_path: str):
    print("Loading data for dashboard...")
    dm = DataManager(data_dir)
    
    # Load "solution.csv" directly as requested
    df = pd.read_csv(solution_path)
         
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['tons_delivered'] > 0] # Visualize actual movements
    
    print("Identifying Best Month based on Efficiency (Score Delta)...")
    
    # Load daily scores
    scores_path = os.path.join(data_dir, 'daily_scores.json')
    if os.path.exists(scores_path):
        with open(scores_path, 'r') as f:
            scores_data = json.load(f)
        
        scores_df = pd.DataFrame(scores_data)
        scores_df['date'] = pd.to_datetime(scores_df['date'])
        scores_df['month'] = scores_df['date'].dt.to_period('M')
        
        # Calculate monthly delta: Last Day Score - First Day Score
        # Actually, simpler: Monthly Gain = (Score at end of month) - (Score at end of prev month)
        # We can just take the diff of the cumulative score series?
        # But let's just do: For each month, get min/max date, take diff.
        
        monthly_gains = {}
        for period, group in scores_df.groupby('month'):
            start_val = group['score'].iloc[0]
            end_val = group['score'].iloc[-1]
            gain = end_val - start_val
            monthly_gains[period] = gain
            
        # Find max gain
        best_month_period = max(monthly_gains, key=monthly_gains.get)
        print(f"Best Month: {best_month_period} (Net Change: {monthly_gains[best_month_period]:,.2f})")
        
    else:
        print("daily_scores.json not found, falling back to volume...")
        df['month'] = df['date'].dt.to_period('M')
        monthly_stats = df.groupby('month')['tons_delivered'].sum()
        best_month_period = monthly_stats.idxmax()
    
    print(f"Visualizing: {best_month_period.strftime('%B %Y')}")
    
    mask = (df['date'].dt.month == best_month_period.month)
    month_data = df.loc[mask]
    
    # Force full month range
    start_date = best_month_period.start_time
    end_date = best_month_period.end_time
    # Ensure end date doesn't exceed 2025-12-31 if it's Dec
    if end_date.year > 2025: end_date = pd.Timestamp('2025-12-31')
    
    days = pd.date_range(start=start_date, end=end_date)
    
    # Setup Plot (Dark Mode)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 12))
    fig.patch.set_facecolor('#0a1929')
    ax.set_facecolor('#0a1929')
    
    # Kerala Bounds (Dynamic based on Farm AND STP locations)
    f_lats = [f.lat for f in dm.farms.values()]
    f_lons = [f.lon for f in dm.farms.values()]
    
    s_lats = [s.lat for s in dm.stps.values()]
    s_lons = [s.lon for s in dm.stps.values()]
    
    all_lats = f_lats + s_lats
    all_lons = f_lons + s_lons
    
    pad = 0.2 
    ax.set_xlim(min(all_lons)-pad, max(all_lons)+pad)
    ax.set_ylim(min(all_lats)-pad, max(all_lats)+pad)
    
    ax.set_title(f"Logistics Flow - {best_month_period.strftime('%B %Y')}\n(Most Active Month)", color='white', pad=20)
    ax.set_xlabel("Longitude", color='gray')
    ax.set_ylabel("Latitude", color='gray')
    ax.grid(True, linestyle='--', alpha=0.1, color='gray')
    ax.tick_params(colors='gray')
    
    # Plot Farms (Green dots)
    ax.scatter(f_lons, f_lats, c='#4CAF50', s=15, alpha=0.7, label='Farms', edgecolors='none')
    
    # Plot STPs (Red Triangles)
    s_lats = [s.lat for s in dm.stps.values()]
    s_lons = [s.lon for s in dm.stps.values()]
    ax.scatter(s_lons, s_lats, c='#f44336', marker='^', s=150, label='STPs', zorder=10, edgecolors='white', linewidth=1)
    
    # Dynamic Elements
    lines = []
    # Date Text with dark background styling
    date_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, 
                        color='white', bbox=dict(facecolor='#1e293b', alpha=0.9, edgecolor='#334155', boxstyle='round,pad=0.5'))
    
    def init():
        return lines + [date_text]
        
    def update(frame_date):
        # Clear previous lines
        for line in lines:
            line.remove()
        lines.clear()
        
        date_str = frame_date.strftime('%Y-%m-%d')
        day_rows = month_data[month_data['date'] == frame_date]
        
        total_tons = day_rows['tons_delivered'].sum()
        date_text.set_text(f"{date_str}")
        
        # Draw lines
        for _, row in day_rows.iterrows():
            stp = dm.stps[row['stp_id']]
            farm = dm.farms[row['farm_id']]
            
            # Width = Load Size (Thinner as requested)
            # Old: 0.5 to 3.0
            # New: 0.3 to 1.5
            lw = 0.3 + (row['tons_delivered'] / 10.0) * 1.2
            
            # Color alpha
            alpha = 0.4 + (row['tons_delivered'] / 20.0)
            
            # Blue lines to match dashboard
            line, = ax.plot([stp.lon, farm.lon], [stp.lat, farm.lat], 
                            c='#2196F3', alpha=alpha, linewidth=lw)
            lines.append(line)
            
        return lines + [date_text]

    print("Generating Animation (this may take a minute)...")
    ani = animation.FuncAnimation(fig, update, frames=days, init_func=init, blit=False, repeat=False)
    
    # Save
    writer = animation.PillowWriter(fps=2) # Faster per day
    ani.save(output_path, writer=writer)
    print(f"Dashboard saved to {output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir) 
    
    data_dir = os.path.join(root_dir, 'data')
    solution_file = os.path.join(root_dir, 'solution', 'solution.csv')
    output_file = os.path.join(root_dir, 'solution', 'dashboard_preview.gif')
    
    create_dashboard(data_dir, solution_file, output_file)
