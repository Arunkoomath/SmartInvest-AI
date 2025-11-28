"""
Main Application with Authentication
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from core.risk_scoring import compute_risk_score, classify_risk
from core.allocation_engine import base_allocation, adjust_for_valuation
from core.data_fetcher import is_equity_overvalued, is_gold_overvalued, get_market_summary
from core.product_ranking import get_recommended_products, format_product_display
from core.backtesting import compare_strategies
from core.database import (
    create_user, authenticate_user, save_recommendation, 
    get_user_recommendations, update_user_profile, get_user_profile
)

st.set_page_config(page_title="SmartInvest AI", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .info-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-left: 4px solid #ffc107;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-left: 4px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #145a8c;
    }
</style>
""", unsafe_allow_html=True)


def create_risk_gauge(risk_score, risk_level):
    """Create a gauge chart for risk score visualization"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Risk Profile: {risk_level}", 'font': {'size': 20}},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 35], 'color': '#90EE90'},
                {'range': [35, 70], 'color': '#FFD700'},
                {'range': [70, 100], 'color': '#FF6347'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'size': 14}
    )
    
    return fig


def create_allocation_pie(allocation, title):
    """Create a pie chart for asset allocation"""
    labels = [asset.title() for asset in allocation.keys()]
    values = list(allocation.values())
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textfont=dict(size=14),
        hovertemplate='<b>%{label}</b><br>Allocation: %{percent}<br>Value: %{value}%<extra></extra>'
    )])
    
    fig.update_layout(
        title=title,
        height=400,
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        font={'size': 12}
    )
    
    return fig


def show_login_page():
    """Display login/signup page"""
    st.title("💰 SmartInvest AI")
    st.caption("Risk-Based Portfolio & Product Recommendation System")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("🔐 Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username and password:
                    success, message, user_id = authenticate_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("📝 Create New Account")
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email (optional)")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_username and new_password:
                    if new_password == confirm_password:
                        success, message, user_id = create_user(new_username, new_password, new_email)
                        if success:
                            st.success(message + " Please login now.")
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords don't match!")
                else:
                    st.warning("Please enter username and password")
    
    st.markdown("---")
    st.info("💡 **Guest Mode:** You can also continue without login, but your recommendations won't be saved.")
    if st.button("Continue as Guest"):
        st.session_state.logged_in = False
        st.session_state.guest_mode = True
        st.rerun()


def show_recommendation_page():
    """Main recommendation page"""
    
    # Header with logout/account info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("💰 SmartInvest AI")
        st.caption("Educational investment recommendation tool (not financial advice).")
    with col2:
        if st.session_state.get('logged_in'):
            st.write(f"👤 **{st.session_state.username}**")
            if st.button("Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            st.caption("Guest Mode")
            if st.button("Login"):
                st.session_state.guest_mode = False
                st.rerun()
    
    # --- Sidebar Form ---
    st.sidebar.header("📌 Enter Your Details")
    
    # Load saved profile if logged in
    saved_profile = None
    if st.session_state.get('logged_in'):
        saved_profile = get_user_profile(st.session_state.user_id)
    
    age = st.sidebar.number_input("Age", min_value=18, max_value=100, 
                                   value=saved_profile['age'] if saved_profile else 25)
    horizon = st.sidebar.number_input("Investment Horizon (years)", 1, 30, 
                                       value=saved_profile['horizon'] if saved_profile else 5)
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

        st.markdown("---")
        
        # Risk Profile Visualization
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.plotly_chart(create_risk_gauge(risk_score, risk_level), use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Your Risk Profile")
            st.success(f"**Risk Score:** {risk_score}/100")
            st.info(f"**Risk Level:** {risk_level} Risk Investor")
            
            if risk_level == "Low":
                st.markdown("""
                **Low Risk Profile:**
                - ✅ Prefers stability over high returns
                - ✅ Comfortable with modest gains
                - ✅ Lower volatility exposure
                - ⚠️ Lower potential returns
                """)
            elif risk_level == "Medium":
                st.markdown("""
                **Medium Risk Profile:**
                - ✅ Balanced risk-return approach
                - ✅ Can handle moderate volatility
                - ✅ Diversified across asset classes
                - 📈 Moderate to good returns potential
                """)
            else:
                st.markdown("""
                **High Risk Profile:**
                - ✅ Growth-focused strategy
                - ✅ Can tolerate high volatility
                - ✅ Higher equity allocation
                - 🚀 Higher returns potential
                """)
        
        st.markdown("---")

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

        # Display Allocations with Pie Charts
        st.subheader("📈 Recommended Asset Allocation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_allocation_pie(base_alloc, "Base Allocation"), use_container_width=True)
            st.caption("📊 Rule-based allocation based on your risk profile")
        
        with col2:
            st.plotly_chart(create_allocation_pie(final_alloc, "Market-Adjusted Allocation"), use_container_width=True)
            st.caption("📊 Adjusted for current market valuations")
        
        # Show changes
        st.markdown("#### 📊 Allocation Changes")
        changes_col1, changes_col2, changes_col3, changes_col4 = st.columns(4)
        
        cols = [changes_col1, changes_col2, changes_col3, changes_col4]
        for idx, (asset, pct) in enumerate(final_alloc.items()):
            change = pct - base_alloc[asset]
            with cols[idx]:
                delta_color = "normal" if change == 0 else "inverse" if change < 0 else "normal"
                st.metric(
                    label=asset.title(),
                    value=f"{pct}%",
                    delta=f"{change:+.0f}%" if change != 0 else "No change"
                )
        
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

        # Backtesting Section
        st.subheader("📊 Historical Performance Analysis (5-Year Backtest)")
        st.write("See how your recommended portfolio would have performed over the past 5 years:")
        
        with st.spinner("Running backtest simulation..."):
            backtest_results = compare_strategies(final_alloc, initial_amount=amount, years=5)
        
        # Performance Comparison Table
        st.write("**Performance Metrics Comparison:**")
        
        metrics_data = []
        for strategy_name, results in backtest_results.items():
            metrics_data.append({
                'Strategy': strategy_name,
                'Final Value (₹)': f"{results['final_value']:,.0f}",
                'Total Return': f"{results['total_return']:.2f}%",
                'CAGR': f"{results['cagr']:.2f}%",
                'Max Drawdown': f"{results['max_drawdown']:.2f}%",
                'Sharpe Ratio': f"{results['sharpe_ratio']:.2f}"
            })
        
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True)
        
        # Portfolio Growth Chart
        st.write("**Portfolio Growth Over Time:**")
        
        fig = go.Figure()
        
        colors = {'Recommended Portfolio': '#2E86AB', 'Nifty 50 Only': '#A23B72', 'Fixed Deposit Only': '#F18F01'}
        
        for strategy_name, results in backtest_results.items():
            portfolio_series = results['portfolio_series']
            fig.add_trace(go.Scatter(
                x=portfolio_series.index,
                y=portfolio_series.values,
                mode='lines',
                name=strategy_name,
                line=dict(color=colors.get(strategy_name, '#333333'), width=2)
            ))
        
        fig.update_layout(
            title='Portfolio Value Over Time (5-Year Backtest)',
            xaxis_title='Date',
            yaxis_title='Portfolio Value (₹)',
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Key Insights
        recommended_cagr = backtest_results['Recommended Portfolio']['cagr']
        nifty_cagr = backtest_results['Nifty 50 Only']['cagr']
        fd_cagr = backtest_results['Fixed Deposit Only']['cagr']
        
        if recommended_cagr > nifty_cagr and recommended_cagr > fd_cagr:
            st.success(f"✅ Your recommended portfolio outperformed both Nifty 50 and FD with {recommended_cagr:.2f}% CAGR!")
        elif recommended_cagr > fd_cagr:
            st.info(f"📈 Your portfolio achieved {recommended_cagr:.2f}% CAGR, beating FD but with better risk management than 100% equity.")
        else:
            st.warning(f"⚠️ Lower volatility comes with moderate returns ({recommended_cagr:.2f}% CAGR), but safer than pure equity exposure.")

        # Save recommendation if logged in
        if st.session_state.get('logged_in'):
            save_success, save_msg = save_recommendation(
                st.session_state.user_id,
                amount,
                goal,
                risk_level,
                risk_score,
                base_alloc,
                final_alloc,
                market_data,
                recommended
            )
            update_user_profile(st.session_state.user_id, age, horizon, risk_level, risk_score)
            
            if save_success:
                st.success("💾 Recommendation saved to your account!")

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


def show_saved_plans_page():
    """Display saved recommendations history"""
    st.title("📁 My Saved Investment Plans")
    
    if not st.session_state.get('logged_in'):
        st.warning("Please login to view saved plans")
        if st.button("Go to Login"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
    st.write(f"**Account:** {st.session_state.username}")
    
    recommendations = get_user_recommendations(st.session_state.user_id, limit=20)
    
    if not recommendations:
        st.info("No saved recommendations yet. Generate your first recommendation!")
        return
    
    st.write(f"**Total Saved Plans:** {len(recommendations)}")
    st.markdown("---")
    
    for idx, rec in enumerate(recommendations, 1):
        with st.expander(f"📌 Plan #{idx} - {rec['created_at'][:10]} | ₹{rec['amount']:,.0f} | {rec['risk_level']} Risk", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Date:** {rec['created_at']}")
                st.write(f"**Amount:** ₹{rec['amount']:,.0f}")
                st.write(f"**Goal:** {rec['goal']}")
                st.write(f"**Risk Profile:** {rec['risk_level']} (Score: {rec['risk_score']})")
            
            with col2:
                st.write("**Final Allocation:**")
                for asset, pct in rec['final_allocation'].items():
                    amt = (pct / 100) * rec['amount']
                    st.write(f"- {asset.title()}: {pct}% (₹{amt:,.0f})")
            
            st.write("**Market Conditions at Time of Recommendation:**")
            mc = rec['market_conditions']
            st.write(f"- Nifty P/E: {mc.get('nifty_pe', 'N/A')} ({mc.get('equity_status', 'N/A')})")
            st.write(f"- Gold Price: ${mc.get('gold_price', 'N/A')} ({mc.get('gold_status', 'N/A')})")


def main():
    """Main application logic"""
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    
    # Page routing
    if st.session_state.logged_in or st.session_state.guest_mode:
        # Show navigation in sidebar
        page = st.sidebar.radio(
            "Navigation",
            ["🏠 Get Recommendation", "📁 My Saved Plans"] if st.session_state.logged_in else ["🏠 Get Recommendation"]
        )
        
        if page == "🏠 Get Recommendation":
            show_recommendation_page()
        elif page == "📁 My Saved Plans":
            show_saved_plans_page()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
