import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# Page Configuration & Aesthetics
# ============================================================
st.set_page_config(
    page_title="Ceylon Electricity Board Tariff Calculator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI CSS styling injection
st.markdown("""
    <style>
    .main {
        background-color: #f4f6f9;
    }
    .metric-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid #eef2f5;
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        margin-top: 5px;
    }
    .metric-label {
        font-size: 14px;
        color: #718096;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# Core Constants & Configurations
# ============================================================

# --- 1. DOMESTIC ---
DOMESTIC_ENERGY_BLOCKS = [
    (30,          8.00),    # units 1-30      -> Rs 8.00 per unit
    (60,          10.00),   # units 31-60     -> Rs 10.00 per unit
    (90,          16.00),   # units 61-90     -> Rs 16.00 per unit
    (120,         30.00),   # units 91-120    -> Rs 30.00 per unit
    (180,         38.00),   # units 121-180   -> Rs 38.00 per unit
    (float("inf"), 55.00),  # units 181+      -> Rs 55.00 per unit
]

DOMESTIC_FIXED_CHARGE = [
    (30,          150.00),
    (60,          400.00),
    (90,          500.00),
    (120,         1000.00),
    (180,         1500.00),
    (float("inf"), 2000.00),
]

# --- 2. COMMERCIAL ---
COMMERCIAL_ENERGY_BLOCKS = [
    (100,          25.00),    # Units 1-100
    (300,          35.00),    # Units 101-300
    (500,          45.00),    # Units 301-500
    (float("inf"), 55.00),    # Units 501+
]

COMMERCIAL_FIXED_CHARGE = [
    (100,          500.00),
    (300,          1000.00),
    (500,          1500.00),
    (float("inf"), 2500.00),
]

# --- 3. INDUSTRIAL ---
INDUSTRIAL_ENERGY_BLOCKS = [
    (500,          22.00),    # Units 1-500
    (1000,         28.00),    # Units 501-1000
    (5000,         35.00),    # Units 1001-5000
    (float("inf"), 42.00),    # Units 5001+
]

INDUSTRIAL_FIXED_CHARGE = [
    (500,          1500.00),
    (1000,         3000.00),
    (5000,         5000.00),
    (float("inf"), 8000.00),
]

# --- POWER FACTOR PARAMETERS ---
PF_REFERENCE = 0.90          # Required minimum PF
PF_PENALTY_PER_0_01 = 0.01   # 1% surcharge for every 0.01 below 0.90
PF_BONUS_PER_0_01 = 0.005    # 0.5% discount for every 0.01 above 0.90
MAX_PF_DISCOUNT = 0.05       # Maximum 5% discount
MAX_PF_PENALTY = 0.20        # Maximum 20% surcharge

# ============================================================
# Calculator Functions
# ============================================================

def get_fixed_charge(units, fixed_charge_slabs):
    """
    Finds the single fixed charge based on total units.
    Non-telescopic calculation: uses the charge corresponding to the slab.
    """
    for limit, charge in fixed_charge_slabs:
        if units <= limit:
            return charge
    return 0.0

def calculate_running_charge(units, energy_blocks):
    """
    Telescopic Running Charge Calculation.
    Splits the consumption into slabs and calculates cost for each portion.
    """
    breakdown = []
    total_running_charge = 0.0
    remaining_units = units
    previous_limit = 0

    for limit, rate in energy_blocks:
        if remaining_units <= 0:
            breakdown.append({
                "Slab Range": f"{previous_limit + 1} - {limit if limit != float('inf') else '+'}",
                "Units in Slab": 0.0,
                "Rate (LKR)": rate,
                "Cost (LKR)": 0.0
            })
            continue

        slab_size = limit - previous_limit
        units_in_slab = min(remaining_units, slab_size)
        cost = units_in_slab * rate
        total_running_charge += cost

        breakdown.append({
            "Slab Range": f"{previous_limit + 1} - {limit if limit != float('inf') else 'Above'}",
            "Units in Slab": units_in_slab,
            "Rate (LKR)": rate,
            "Cost (LKR)": cost
        })

        remaining_units -= units_in_slab
        previous_limit = limit

    return total_running_charge, breakdown

def calculate_pf_adjustment(total_bill, pf):
    """
    Power factor adjustments - surcharge if PF < 0.90, discount if PF > 0.90.
    """
    if pf < PF_REFERENCE:
        difference = PF_REFERENCE - pf
        penalty = (difference / 0.01) * PF_PENALTY_PER_0_01
        penalty = min(penalty, MAX_PF_PENALTY)
        adjustment = total_bill * penalty
        return adjustment, penalty, "Penalty"

    elif pf > PF_REFERENCE:
        difference = pf - PF_REFERENCE
        discount = (difference / 0.01) * PF_BONUS_PER_0_01
        discount = min(discount, MAX_PF_DISCOUNT)
        adjustment = -(total_bill * discount)
        return adjustment, discount, "Discount"

    return 0.0, 0.0, "None"

# ============================================================
# Main App Layout
# ============================================================

st.title("⚡ Ceylon Electricity Board (CEB) Tariff Calculator")
st.markdown("Calculate, visualize, and optimize electricity bills based on CEB guidelines.")

# Sidebar Selection
st.sidebar.header("🔌 Calculator Inputs")
category = st.sidebar.selectbox("Select Customer Category", ["Domestic", "Commercial", "Industrial"])
units = st.sidebar.number_input("Monthly Units Consumed (kWh)", min_value=0, max_value=50000, value=150, step=10)

# Set category parameters
if category == "Domestic":
    fixed_charge = get_fixed_charge(units, DOMESTIC_FIXED_CHARGE)
    running_charge, breakdown = calculate_running_charge(units, DOMESTIC_ENERGY_BLOCKS)
    max_demand_charge = 0.0
    pf_adjustment = 0.0
    pf_percentage = 0.0
    pf_status = "None"
    
elif category == "Commercial":
    fixed_charge = get_fixed_charge(units, COMMERCIAL_FIXED_CHARGE)
    running_charge, breakdown = calculate_running_charge(units, COMMERCIAL_ENERGY_BLOCKS)
    
    # Commercial Bulk inputs
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏢 Commercial Bulk Details")
    is_bulk_comm = st.sidebar.checkbox("Is Bulk Connection? (>42 kVA)", value=False)
    
    if is_bulk_comm:
        max_demand = st.sidebar.number_input("Maximum Demand (kVA)", min_value=0.0, value=15.0, step=1.0)
        max_demand_rate = st.sidebar.number_input("Max Demand Charge Rate (LKR/kVA)", min_value=0.0, value=1000.0, step=50.0)
        max_demand_charge = max_demand * max_demand_rate
    else:
        max_demand_charge = 0.0
        
    pf_adjustment = 0.0
    pf_percentage = 0.0
    pf_status = "None"

elif category == "Industrial":
    fixed_charge = get_fixed_charge(units, INDUSTRIAL_FIXED_CHARGE)
    running_charge, breakdown = calculate_running_charge(units, INDUSTRIAL_ENERGY_BLOCKS)
    
    # Industrial Bulk inputs
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏭 Industrial Bulk & PF Details")
    
    max_demand = st.sidebar.number_input("Maximum Demand (kVA)", min_value=0.0, value=50.0, step=5.0)
    max_demand_rate = st.sidebar.number_input("Max Demand Charge Rate (LKR/kVA)", min_value=0.0, value=1000.0, step=50.0)
    max_demand_charge = max_demand * max_demand_rate
    
    power_factor = st.sidebar.slider("Power Factor (PF)", min_value=0.50, max_value=1.00, value=0.90, step=0.01)
    
    # Calculate PF adjustment based on (Fixed + Running + Demand)
    base_bill = fixed_charge + running_charge + max_demand_charge
    pf_adjustment, pf_percentage, pf_status = calculate_pf_adjustment(base_bill, power_factor)

# Total bill calculation
total_bill = fixed_charge + running_charge + max_demand_charge + pf_adjustment

# ============================================================
# Main Panel View
# ============================================================

# KPI Blocks
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">TOTAL ESTIMATED BILL</div>
            <div class="metric-value" style="color: #e53e3e;">LKR {total_bill:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">RUNNING CHARGES</div>
            <div class="metric-value" style="color: #2b6cb0;">LKR {running_charge:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">FIXED CHARGES</div>
            <div class="metric-value" style="color: #4a5568;">LKR {fixed_charge:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with c4:
    if category == "Domestic":
        charge_label = "OTHER ADJUSTMENTS"
        charge_val = "LKR 0.00"
        text_color = "#718096"
    elif category == "Commercial":
        charge_label = "MAX DEMAND CHARGE"
        charge_val = f"LKR {max_demand_charge:,.2f}"
        text_color = "#319795"
    else: # Industrial
        charge_label = f"DEMAND + PF ADJ ({pf_status})"
        charge_val = f"LKR {max_demand_charge + pf_adjustment:,.2f}"
        text_color = "#dd6b20" if pf_status == "Penalty" else "#319795" if pf_status == "Discount" else "#4a5568"
        
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{charge_label}</div>
            <div class="metric-value" style="color: {text_color};">{charge_val}</div>
        </div>
    """, unsafe_allow_html=True)

# Main Grid (Left: breakdown table, Right: pie chart)
col_table, col_pie = st.columns([3, 2])

with col_table:
    st.subheader("📋 Telescopic Slabs Billing Breakdown")
    df = pd.DataFrame(breakdown)
    df["Rate (LKR)"] = df["Rate (LKR)"].apply(lambda x: f"LKR {x:,.2f}")
    df["Cost (LKR)"] = df["Cost (LKR)"].apply(lambda x: f"LKR {x:,.2f}")
    st.dataframe(df, use_container_width=True, hide_index=True)

with col_pie:
    st.subheader("🍩 Cost Contribution")
    
    # Donut Chart Data preparation
    pie_labels = ["Running Charges", "Fixed Charges"]
    pie_values = [running_charge, fixed_charge]
    
    if max_demand_charge > 0:
        pie_labels.append("Max Demand Charge")
        pie_values.append(max_demand_charge)
        
    if pf_adjustment != 0:
        if pf_adjustment > 0:
            pie_labels.append("PF Penalty")
            pie_values.append(pf_adjustment)
        else:
            st.caption(f"✨ Note: You received a LKR {abs(pf_adjustment):,.2f} ({pf_percentage*100:.1f}%) Power Factor discount.")

    fig_pie = px.pie(
        names=pie_labels,
        values=pie_values,
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250)
    st.plotly_chart(fig_pie, use_container_width=True)

# Row 3: Growth Trend and Savings Suggestions
st.markdown("---")
col_trend, col_savings = st.columns([3, 2])

with col_trend:
    st.subheader("📈 Bill Growth Curve (under selected category)")
    
    # Calculate line points
    trend_units = list(range(0, int(units * 1.5) + 100, max(20, int(units * 1.5 // 50))))
    trend_bills = []
    
    # Choose config
    if category == "Domestic":
        blocks = DOMESTIC_ENERGY_BLOCKS
        f_charge_slabs = DOMESTIC_FIXED_CHARGE
    elif category == "Commercial":
        blocks = COMMERCIAL_ENERGY_BLOCKS
        f_charge_slabs = COMMERCIAL_FIXED_CHARGE
    else:
        blocks = INDUSTRIAL_ENERGY_BLOCKS
        f_charge_slabs = INDUSTRIAL_FIXED_CHARGE
        
    for tu in trend_units:
        ec, _ = calculate_running_charge(tu, blocks)
        fc = get_fixed_charge(tu, f_charge_slabs)
        tc_before_pf = ec + fc + max_demand_charge
        
        if category == "Industrial":
            adj, _, _ = calculate_pf_adjustment(tc_before_pf, power_factor)
            bill_val = tc_before_pf + adj
        else:
            bill_val = tc_before_pf
        trend_bills.append(bill_val)

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=trend_units, 
        y=trend_bills, 
        mode='lines', 
        name='Tariff Bill Amount',
        line=dict(color='#d9534f' if category == "Domestic" else '#319795', width=3)
    ))
    fig_line.add_trace(go.Scatter(
        x=[units], 
        y=[total_bill], 
        mode='markers', 
        name='Current Usage',
        marker=dict(color='orange', size=12, symbol='star')
    ))
    fig_line.update_layout(
        xaxis_title="Units Consumed (kWh)",
        yaxis_title="Estimated Bill (LKR)",
        height=320,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    st.plotly_chart(fig_line, use_container_width=True)

with col_savings:
    st.subheader("💡 Bill Optimization Suggestions")
    
    # Calculate savings
    u_10 = int(units * 0.9)
    u_20 = int(units * 0.8)
    
    ec_10, _ = calculate_running_charge(u_10, blocks)
    fc_10 = get_fixed_charge(u_10, f_charge_slabs)
    base_10 = ec_10 + fc_10 + max_demand_charge
    
    ec_20, _ = calculate_running_charge(u_20, blocks)
    fc_20 = get_fixed_charge(u_20, f_charge_slabs)
    base_20 = ec_20 + fc_20 + max_demand_charge
    
    if category == "Industrial":
        adj_10, _, _ = calculate_pf_adjustment(base_10, power_factor)
        adj_20, _, _ = calculate_pf_adjustment(base_20, power_factor)
        bill_10 = base_10 + adj_10
        bill_20 = base_20 + adj_20
    else:
        bill_10 = base_10
        bill_20 = base_20
        
    s_10 = total_bill - bill_10
    s_20 = total_bill - bill_20
    
    st.markdown(f"""
    * **Reduce consumption by 10% ({u_10} units):**
      * New Bill: **LKR {bill_10:,.2f}** (Saves **LKR {s_10:,.2f}**)
    * **Reduce consumption by 20% ({u_20} units):**
      * New Bill: **LKR {bill_20:,.2f}** (Saves **LKR {s_20:,.2f}**)
    """)
    
    if category == "Industrial":
        st.warning("""
        **⚡ Power Factor Alert:**
        Your current Power Factor is **{:.2f}**. 
        If you raise your PF above **0.90** (e.g. using capacitor banks), you can receive up to **5% discount** on your entire base bill. If it falls below **0.90**, you pay a **1% surcharge per 0.01 drop**!
        """.format(power_factor))
    else:
        st.info("""
        **💡 Simple Saving Tip:**
        Ceylon Electricity Board (CEB) billing rates are highly progressive (higher slabs charge much more per unit). Staying in a lower unit slab (e.g., below 90 units or 120 units) significantly reduces both running charges and fixed charges!
        """)

# ============================================================
# Footer Watermark
# ============================================================
st.markdown("""
    <hr style="border-top: 1px solid #e2e8f0; margin-top: 50px; margin-bottom: 20px;">
    <div style="text-align: center; color: #718096; font-size: 14px; font-weight: 500;">
        ⚡ CEB Tariff Calculator | Developed with ❤️ by <a href="https://github.com/aashirazr019-code" target="_blank" style="color: #319795; font-weight: bold; text-decoration: none;">Aashir</a>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
    <br><br><hr style="border-top: 1px dashed #cbd5e0; margin: 20px 0;">
    <div style="text-align: center; color: #a0aec0; font-size: 12px;">
        Made by <b>Aashir</b> | v1.0
    </div>
""", unsafe_allow_html=True)
