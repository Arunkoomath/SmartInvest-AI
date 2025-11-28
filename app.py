import streamlit as st
from core.risk_scoring import compute_risk_score, classify_risk
from core.allocation_engine import base_allocation, adjust_for_valuation
from core.data_fetcher import is_equity_overvalued, is_gold_overvalued, get_market_summary
from core.product_ranking import get_recommended_products, format_product_display

st.set_page_config(page_title="SmartInvest AI", layout="wide")


def main():

    st.title("💰 SmartInvest AI")
    st.caption("Educational investment recommendation tool (not financial advice).")

    # --- Sidebar Form ---
    st.sidebar.header("📌 Enter Your Details")
    
    age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=25)
    horizon = st.sidebar.number_input("Investment Horizon (years)", 1, 30, 5)
    amount = st.sidebar.number_input("Investment Amount (₹)", min_value=1000, value=50000, step=1000)
    
    goal = st.sidebar.selectbox(
        "Investment Goal",
        ["Short-term", "Wealth Creation", "Retirement", "No Specific Goal"]
    )

    st.sidebar.subheader("📊 Risk Tolerance Questions")

    q1 = st.sidebar.slider("How comfortable are you with short-term loss?", 0, 10, 5)
    q2 = st.sidebar.slider("Would you stay invested during market crash?", 0, 10, 5)
    q3 = st.sidebar.slider("Do you prefer higher returns over stability?", 0, 10, 5)

    answers = {"q1": q1, "q2": q2, "q3": q3}

    # --- Action Button ---
    if st.sidebar.button("Get Recommendation"):

        # Risk Score Calculation
        risk_score = compute_risk_score(answers)
        risk_level = classify_risk(risk_score)

        st.success(f"📌 Risk Score: **{risk_score}** → Profile: **{risk_level} Investor**")

        # Base Allocation
        base_alloc = base_allocation(risk_level, horizon)
        
        # Get market conditions
        with st.spinner("Analyzing current market conditions..."):
            market_data = get_market_summary()
            equity_over = is_equity_overvalued()
            gold_over = is_gold_overvalued()
        
        # Adjust allocation based on market conditions
        final_alloc = adjust_for_valuation(base_alloc, equity_over, gold_over)
        
        # Display Market Conditions
        st.subheader("📊 Current Market Conditions")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Nifty 50 P/E", 
                f"{market_data['nifty_pe']:.1f}",
                delta=f"Avg: {market_data['nifty_avg_pe']:.1f}"
            )
            st.caption(f"Status: **{market_data['equity_status']}**")
        
        with col2:
            st.metric(
                "Gold Price (USD)", 
                f"${market_data['gold_price']:.0f}",
                delta=f"Avg: ${market_data['gold_avg']:.0f}"
            )
            st.caption(f"Status: **{market_data['gold_status']}**")

        # Display Allocations
        st.subheader("📈 Recommended Asset Allocation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Base Allocation** (before market adjustment):")
            for asset, pct in base_alloc.items():
                st.write(f"- {asset.title()}: {pct}%")
        
        with col2:
            st.write("**Final Allocation** (market-adjusted):")
            for asset, pct in final_alloc.items():
                change = pct - base_alloc[asset]
                emoji = "🔼" if change > 0 else "🔽" if change < 0 else "➖"
                st.write(f"- {asset.title()}: {pct}% {emoji}")
        
        # Calculate investment amounts
        st.subheader("💰 Investment Breakdown (₹)")
        st.write(f"Total Investment: **₹{amount:,}**")
        
        for asset, pct in final_alloc.items():
            amt = (pct / 100) * amount
            st.write(f"- {asset.title()}: ₹{amt:,.0f} ({pct}%)")

        # Product Recommendations
        st.subheader("🎯 Recommended Products")
        st.write("Based on historical performance, expense ratios, and ratings:")
        
        recommended = get_recommended_products(final_alloc, top_n=2)
        
        for asset_class, products in recommended.items():
            with st.expander(f"📊 {asset_class.title()} - Top Recommendations", expanded=True):
                for i, product in enumerate(products, 1):
                    st.markdown(f"### Option {i}")
                    st.markdown(format_product_display(product))
                    
                    # Calculate investment for this product
                    allocation_pct = final_alloc[asset_class]
                    product_amount = (allocation_pct / 100) * amount
                    st.info(f"💵 Suggested investment in this product: **₹{product_amount:,.0f}**")
                    st.markdown("---")

        st.markdown("""
        ---

        ### 📝 Interpretation  
        """)
        
        # Dynamic explanation based on adjustments
        if equity_over and gold_over:
            st.info("⚠️ Both equity and gold appear overvalued. Allocation tilted toward gilt/debt for safety.")
        elif equity_over:
            st.info("⚠️ Equity markets appear overvalued. Reduced equity allocation, increased gilt/gold.")
        elif gold_over:
            st.info("⚠️ Gold at recent peak. Reduced gold allocation, increased equity/gilt.")
        else:
            st.success("✅ Market conditions are favorable. Allocation follows your risk profile.")
        
        st.write(f"""
        **Your Profile:** {risk_level} risk, {horizon}-year horizon  
        **Goal:** {goal}  
        **Strategy:** This allocation balances your risk tolerance with current market valuations.
        
        **Next Steps:**
        - Diversify within each asset class
        - Review and rebalance quarterly
        - Stay invested for your full time horizon
        """)

    else:
        st.info("➡ Fill details in sidebar and click **Get Recommendation**")


if __name__ == "__main__":
    main()

