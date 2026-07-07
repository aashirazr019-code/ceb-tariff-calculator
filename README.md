# Ceylon Electricity Board (CEB) Tariff Calculator

A modern, interactive Python Web Application built with **Streamlit** to calculate, visualize, and optimize electricity bills according to the Ceylon Electricity Board (CEB) tariff guidelines.

## 🚀 Features

- **Multi-Category Billing Support**:
  - **Domestic**: Telescopic energy slab charges (1-30, 31-60, 61-90, 91-120, 121-180, 181+) and single fixed standing charges based on monthly units.
  - **Commercial**: Energy slab charges, fixed charges, and Maximum Demand (MD) charges for bulk connections (>42 kVA).
  - **Industrial**: Energy slabs, fixed charges, Maximum Demand charges, and dynamic **Power Factor (PF)** adjustment (surcharges/penalties for PF < 0.90, discounts for PF > 0.90).
- **Interactive KPI Cards**: Real-time display of Total Bill, Energy Charges, Fixed Charges, and Demand/PF adjustments.
- **Detailed Slab-wise Breakdown**: Telescopic breakdown table showing exact units consumed, rate, and cost per slab.
- **Cost Contribution Visualization**: Interactive donut chart showing the share of each cost component.
- **Bill Growth Curve**: Graph depicting how your bill scales as units increase from 0 to 1.5x your current usage, highlighting your current consumption point.
- **Energy Optimization Projections**: Auto-calculates potential savings if you reduce your electricity consumption by 10% or 20%.

## 🛠️ Tech Stack

- **Python** (Core Logic)
- **Streamlit** (Web UI Framework)
- **Pandas** (Data Formatting)
- **Plotly** (Interactive Visualizations)

## 🏃 Getting Started

### Prerequisites

Make sure you have Python installed on your machine.

### Installation

1. Clone this repository (or copy the files):
   ```bash
   git clone <your-repository-url>
   cd <repository-directory>
   ```

2. Install the required Python packages:
   ```bash
   pip install streamlit pandas plotly
   ```

### Running the Application

Launch the Streamlit local development server:
```bash
streamlit run app.py
```
Streamlit will automatically open the app in your default browser at `http://localhost:8501`.

## 📈 Slab Tariffs Overview

### Domestic Tariffs

| Unit Block | Energy Rate (LKR/unit) | Fixed Charge (LKR) |
| :--- | :--- | :--- |
| **0 – 30** | 8.00 | 150.00 |
| **31 – 60** | 10.00 | 400.00 |
| **61 – 90** | 16.00 | 500.00 |
| **91 – 120** | 30.00 | 1,000.00 |
| **121 – 180** | 38.00 | 1,500.00 |
| **Above 180** | 55.00 | 2,000.00 |

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
