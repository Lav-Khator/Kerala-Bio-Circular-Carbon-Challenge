# Kerala Biosolids Logistics Dashboard 🌿

## Overview
This interactive dashboard visualizes the optimal biosolids delivery solution for Kerala's 4 STPs and 250 farms. It runs a day-by-day simulation of the 2025 logistics plan, tracking carbon credits, storage levels, and truck movements.

## 🚀 Quick Start
**Windows:**
1.  Go to the project root folder.
2.  Double-click **`run_dashboard.bat`**.
3.  The dashboard will open automatically in your browser.

**Mac/Linux:**
1.  Open terminal in project root.
2.  Run `python -m http.server 8000`.
3.  Open `http://localhost:8000/dashboard_website/dashboard_beautiful.html`.

---

## 📊 Features & Legend

### Key Indicators
*   **Net Carbon Credits:** The primary metric (-1.3M kg CO₂ Target).
*   **STP Storage:** Visual gauge showing current capacity usage.
*   **Rain-Lock Status:** Real-time tracking of monsoon constraints.

### Visual Legend
| Symbol | Meaning |
|:---:|---|
| 🔺 | **STP (Red Triangle):** Sewage Treatment Plant |
| 🟢 | **Farm (Green Dot):** Active farm ready for delivery |
| ⚫ | **Rain-Locked (Grey Dot):** Farm unavailable due to heavy rain (>30mm) |
| 🔵 | **Delivery Route (Blue Line):** Truck in transit (Thickness = Load Size) |

---

## 🛠️ Controls
*   **▶ Play / ⏸ Pause:** Control the simulation flow.
*   **Speed Slider:** Adjust from 1x (Real-time) to 10x (Fast Forward).
*   **Step Next:** Advance one day at a time for detailed analysis.
*   **Reset:** Jump back to Jan 1st.

## Troubleshooting
*   **Blank Map?** Ensure you are running via `run_dashboard.bat` or a local server. Opening the HTML file directly (file://) will block data loading due to browser security.
*   **Data Missing?** Verify `solution/solution.csv` and `data/daily_scores.json` exist.

---
*Generated for Kerala Carbon Challenge 2025*
