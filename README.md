# Kerala Carbon Challenge

A comprehensive solution for optimizing carbon management in Kerala's wastewater treatment system, featuring an interactive dashboard for visualization and analysis.

## 🌟 Features

- **Optimized Solver Algorithm**: Intelligent carbon allocation strategy for wastewater treatment plants
- **Interactive Dashboard**: Beautiful web-based visualization of daily scores and metrics
- **Real-time Analytics**: Track carbon flow, biosolids application, and STP performance
- **Automated Workflow**: One-click solution generation and visualization

## 🚀 Quick Start (Windows)

1. **Double-click** `run_dashboard.bat`
2. The dashboard will automatically open in your browser

## 🛠️ Manual Setup & Running

### Prerequisites

- Python 3.7 or higher
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/kerala_carbon_challenge.git
   cd kerala_carbon_challenge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Dashboard

**Option 1: Simple HTTP Server**
```bash
python -m http.server 8000
```
Then open your browser to: `http://localhost:8000/dashboard_website/dashboard_beautiful.html`

**Option 2: Windows Batch File**
```bash
run_dashboard.bat
```

### Re-running the Solver (Optional)

To regenerate the solution with the optimization algorithm:
```bash
python algorithm_code/run.py
```
This will update `solution/solution.csv` with the optimized carbon allocation strategy.

## 📂 Project Structure

```
kerala_carbon_challenge/
├── algorithm_code/       # Core solver implementation
│   ├── run.py           # Main solver entry point
│   └── ...
├── assist_code/         # Helper scripts and utilities
│   ├── generate_summary_json.py
│   └── ...
├── dashboard_website/   # Interactive web dashboard
│   ├── dashboard_beautiful.html
│   └── ...
├── data/                # Input data and configuration
│   ├── config.json
│   ├── daily_scores.json
│   └── ...
├── solution/            # Generated solutions and metrics
│   ├── solution.csv
│   └── summary_metrics.json
├── src/                 # Source code modules
├── requirements.txt     # Python dependencies
├── run_dashboard.bat    # Windows launcher script
└── README.md           # This file
```

## 📊 How It Works

1. **Data Input**: The system reads configuration and input data from the `data/` directory
2. **Optimization**: The solver algorithm (`algorithm_code/run.py`) computes optimal carbon allocation
3. **Solution Output**: Results are saved to `solution/solution.csv`
4. **Visualization**: The dashboard reads the solution and displays interactive charts and metrics

## 🎯 Key Components

### Solver Algorithm
The optimization engine that determines the best strategy for:
- Carbon allocation across treatment plants
- Biosolids application timing and quantities
- STP (Sewage Treatment Plant) overflow management

### Dashboard
An interactive web interface featuring:
- Daily score tracking
- Carbon flow visualization
- Performance metrics
- Historical trends

## 📧 Contact

For questions or feedback, please open an issue on GitHub.
