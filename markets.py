import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Set Streamlit layout and title
st.set_page_config(page_title="Fixed Income Strategy Viewer", layout="wide")
# ⬇️ Auto-refresh every 20 seconds
st_autorefresh(interval=20 * 1000, key="auto_refresh")
#st.title("📈 Fixed Income Strategy Curves")
st.markdown(
    """
    <h1 style='text-align: center; color: #0072C6;'>
        📈 Explore Fixed Income Strategy Curves
    </h1>
    <h4 style='text-align: center; color: grey; font-weight: normal;'>
        Compare strategies across markets like SOFR, SONIA, and EURIBOR
    </h4>
    """,
    unsafe_allow_html=True
)

# Theme selector
theme = st.radio("Select Theme:", ["Dark", "Light"], horizontal=True)

# File uploader
uploaded_file = st.file_uploader("Upload the strategy Excel file", type=["xlsx"])

if uploaded_file:
    # Load Excel and get sheet names (markets)
    xls = pd.ExcelFile(uploaded_file)
    markets = xls.sheet_names

    # Display market checkboxes horizontally
    st.markdown("### Select Markets:")
    market_cols = st.columns(len(markets))
    selected_markets = []

    for i, market in enumerate(markets):
        with market_cols[i]:
            if st.checkbox(market, key=f"market_{market}"):
                selected_markets.append(market)

    # Loop over each selected market and show strategy analysis
    for selected_market in selected_markets:
        st.header(f"📊{selected_market} Charts")
        df = pd.read_excel(xls, sheet_name=selected_market)

        # Get all strategy labels
        contracts = df['StrategyLabel'].tolist()

        # Create a dictionary of base prices
        price_dict = {
            row['StrategyLabel']: row['Price']
            for _, row in df[df['StrategyType'] == 'Outright'].iterrows()
        }

        # Helper to clean contract names
        def short(label):
            if label.startswith("SR3"):
                return label[3:].lstrip('_ ').strip()
            return label

        # Prepare data buckets for each strategy type
        strategy_data = {
            "Outright": [],
            "3M Spread": [],
            "6M Spread": [],
            "12M Spread": [],
            "3M Butterfly": [],
            "6M Butterfly": [],
            "12M Butterfly": []
        }

        # Calculate strategies based on contract list
        for i in range(len(contracts)):
            base = contracts[i]
            label = short(base)

            if base in price_dict:
                strategy_data["Outright"].append((label, price_dict[base]))

            if i + 1 < len(contracts):
                leg2 = contracts[i + 1]
                if base in price_dict and leg2 in price_dict:
                    strategy_data["3M Spread"].append((label, price_dict[base] - price_dict[leg2]))

            if i + 2 < len(contracts):
                leg2 = contracts[i + 2]
                if base in price_dict and leg2 in price_dict:
                    strategy_data["6M Spread"].append((label, price_dict[base] - price_dict[leg2]))

            if i + 4 < len(contracts):
                leg2 = contracts[i + 4]
                if base in price_dict and leg2 in price_dict:
                    strategy_data["12M Spread"].append((label, price_dict[base] - price_dict[leg2]))

            if i + 2 < len(contracts):
                mid, tail = contracts[i + 1], contracts[i + 2]
                if all(k in price_dict for k in [base, mid, tail]):
                    strategy_data["3M Butterfly"].append((label, price_dict[base] - 2 * price_dict[mid] + price_dict[tail]))

            if i + 4 < len(contracts):
                mid, tail = contracts[i + 2], contracts[i + 4]
                if all(k in price_dict for k in [base, mid, tail]):
                    strategy_data["6M Butterfly"].append((label, price_dict[base] - 2 * price_dict[mid] + price_dict[tail]))

            if i + 6 < len(contracts):
                mid, tail = contracts[i + 4], contracts[i + 6]
                if all(k in price_dict for k in [base, mid, tail]):
                    strategy_data["12M Butterfly"].append((label, price_dict[base] - 2 * price_dict[mid] + price_dict[tail]))

        # Two-row strategy checkboxes
        st.markdown("### Select Strategy Types:")
        strategy_names = list(strategy_data.keys())
        half = len(strategy_names) // 2

        row1 = st.columns(4)
        row2 = st.columns(4)
        selected_strategies = []

        for i in range(half):
            with row1[i]:
                if st.checkbox(strategy_names[i], key=f"{selected_market}_chk_{strategy_names[i]}"):
                    selected_strategies.append(strategy_names[i])

        for i in range(half, len(strategy_names)):
            with row2[i - half]:
                if st.checkbox(strategy_names[i], key=f"{selected_market}_chk_{strategy_names[i]}"):
                    selected_strategies.append(strategy_names[i])

        # Plotting function
        def plot_strategy(name, data):
            if not data:
                st.warning(f"No data for {name}")
                return

            x_vals, y_vals = zip(*data)
            text_colors = ['red' if val < 0 else 'white' for val in y_vals]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines+markers+text',
                name=name,
                text=[f"{val:.2f}" for val in y_vals],
                textposition="top center",
                textfont=dict(size=12, color=text_colors),
                marker=dict(color='rgba(0, 102, 204, 0.8)', size=5),
                line=dict(color='rgba(0, 102, 204, 0.6)', width=2.5)
            ))

            fig.update_layout(
                title=dict(
                    text=f"<b>{name} Strategy Curve - {selected_market}</b>",
                    x=0.5,
                    xanchor='center',
                    font=dict(size=18)
                ),
                xaxis_title="Contract",
                yaxis_title="Price",
                template="plotly_dark" if theme == "Dark" else "plotly_white",
                height=500,
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False)
            )

            st.plotly_chart(fig, use_container_width=True, key=f"{selected_market}_{name}")

        # Display selected strategies
        for name in selected_strategies:
            plot_strategy(name, strategy_data[name])
