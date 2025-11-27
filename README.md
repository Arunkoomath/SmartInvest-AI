# SmartInvest AI: Risk-Based Portfolio & Product Recommendation System

> Academic project – AI-powered investment allocator for Indian retail investors (Equity Index Funds, Mutual Funds, Gold ETFs/SGB, Gilt Funds, FDs, Liquid Funds).

---

## 🔍 Project Overview

**Goal:**  
Build a web app where an Indian retail investor can enter:

- Age  
- Investment amount  
- Investment horizon (years)  
- Goal (Short-term / Wealth creation / Retirement)  
- Income level  
- Existing investments  
- Risk questionnaire answers  

…and get:

- 📊 **Asset allocation** across Equity, Debt (Gilt/Bonds), Gold, FD/Liquid funds  
- 🎯 **Specific products** (e.g., Nifty 50 index fund, gold ETF, gilt fund, etc.)  
- 📈 **Expected return range & risk** (based on historical data)  
- 📉 **Backtest** of the allocation over the last 5 years  
- 🧠 **Dynamic tilt** based on market valuation (Nifty PE, gold levels, etc.)

> ⚠️ **Disclaimer:** This is an academic / educational project.  
> It is **not** registered investment advice and should not be used for real-money decisions.

---

## 👥 Target User

- Indian retail investor
- Basic understanding of SIPs / mutual funds
- Wants simple, rule-based recommendations with transparent logic (not black-box magic)

---

## 🧠 Core Features

### 1. User Profile & Questionnaire

- Signup/Login (email + password)
- Store basic profile: name, age, income level, typical risk score
- Questionnaire:
  - Age
  - Investment amount (lump sum, and later SIP/monthly)
  - Horizon: `<1`, `1–3`, `3–5`, `5+` years
  - Goal: Short-term / Wealth creation / Retirement
  - Income: Low / Medium / High
  - Existing allocation: % in Equity / Debt / Gold / Cash
  - 5–10 risk questions → **risk score (0–100)**

From this, compute:

- **Risk profile:** Conservative / Moderate / Aggressive  
- **Time profile:** Short / Medium / Long-term

---

### 2. Rule-Based Asset Allocation Engine

Basic rules (examples):

- **Low risk, horizon < 3 years**
  - 20% Equity Index
  - 20% Balanced/Hybrid MF
  - 30% Gilt / Govt bonds
  - 30% FD / Liquid funds

- **Medium risk, horizon 3–7 years**
  - 50–60% Equity (Index/ETF + diversified MF)
  - 20–25% Gilt / Bonds
  - 15–20% Gold
  - 5–10% FD / Liquid

- **High risk, horizon ≥ 7 years**
  - 70–80% Equity
  - 10–15% Gold
  - 5–10% Gilt
  - 0–5% FD

#### Dynamic Market Tilt

Use valuation signals like:

- Nifty 50 PE vs historical average  
- Gold price vs 1-year average

Rules (examples):

- If Nifty PE > avg + 1σ → reduce equity by ~10%, add to gold/gilt  
- If Nifty PE < avg – 1σ → increase equity by ~10%, reduce gold/gilt  
- If gold near 1-year high → cut gold slightly, add to equity/gilt  

This gives a **“smart” & real-time-aware allocation**.

---

### 3. ML-Based Product Ranking (Inside Asset Classes)

Use ML/scoring only for **ranking products**, not for the whole portfolio.

Example: **Equity Index Funds**

Features:

- 1Y, 3Y, 5Y returns
- Expense ratio
- Volatility
- AUM size

Approach:

- Start with a **custom score**:  
  `score = 0.4 * 5Y_return + 0.3 * 3Y_return - 0.2 * volatility - 0.1 * expense_ratio`
- Optionally upgrade to **RandomForestRegressor** to predict a “risk-adjusted score”.

Similar for:

- **Gold ETFs:** tracking error, expense ratio, liquidity  
- **Gilt Funds:** consistency, drawdown, volatility

Flow:

> Rule-based layer decides:  
> “40% in Equity Index funds”  

> ML/scoring layer picks **top 2–3 specific funds/ETFs** to fill that 40%.

---

### 4. Recommendation Screen (UI)

Example output:

- **40% – Nifty 50 Index Fund – Direct Plan (Equity)**
- **20% – Nifty Next 50 Index Fund – Direct Plan**
- **15% – Gold ETF – XYZ AMC**
- **15% – Gilt Fund – ABC AMC**
- **10% – Bank FD / Liquid fund**

For each product:

- Name  
- Category (Equity Index / Gold / Gilt / Liquid / FD)  
- Expense ratio  
- 1Y / 3Y / 5Y returns  
- Risk tag: Low / Medium / High  
- “Why chosen?” explanation

Extra insights:

- **Expected return range:** e.g. “Historically 8–11% p.a.”
- **Risk:** “Max historical drawdown around –18%”
- Explanation text based on risk + horizon.

---

### 5. Backtesting Module

Given:

- Portfolio allocation (e.g., 40% Fund A, 30% Fund B, 20% Gold ETF, 10% Gilt Fund)  
- Time period: last 5 years  
- Initial amount: ₹1,00,000  

Steps:

1. Download historical NAV/price for all products  
2. Simulate investing allocation% × initial amount  
3. Track portfolio value over time  

Outputs:

- Final value and CAGR  
- Max drawdown  
- Compare vs:
  - Nifty 50 only
  - FD-only scenario  
- Line chart: Time vs Portfolio value (using `pandas + matplotlib`)

---

## 🏗️ Tech Stack & Architecture

### Option A – Simple Stack (Streamlit)

- **Frontend:** Streamlit (Python)
- **Backend logic:** Python (pandas, scikit-learn, yfinance)
- **Database:** SQLite/PostgreSQL

Flow:

1. User visits Streamlit app  
2. Completes questionnaire  
3. Backend:
   - Computes risk score & base allocation
   - Pulls latest market data (Nifty, Gold, fund NAVs)
   - Applies valuation tilts
   - Ranks products and builds portfolio
   - Runs backtest  
4. UI shows:
   - Allocation breakdown
   - Product list
   - Backtest chart
   - Explanation text

### Option B – Full Web App (Future)

- **Frontend:** React  
- **Backend:** FastAPI / Flask  
- **DB:** PostgreSQL  
- **APIs (example):**
  - `POST /recommendation`
  - `GET /user/portfolio`

---

## 🗃️ Database Design (Draft Schema)

- **users**
  - user_id (PK)
  - name, email, password_hash, age, created_at

- **user_profiles**
  - user_id (FK)
  - income_level, risk_score, goal_type, horizon_years

- **asset_classes**
  - asset_class_id (PK)
  - name (Equity Index, Gold ETF, Gilt Fund, FD, etc.)

- **products**
  - product_id (PK)
  - name, asset_class_id (FK)
  - symbol/code (for API)
  - expense_ratio, category, risk_level

- **product_metrics_daily**
  - id
  - product_id (FK)
  - date
  - nav_or_price
  - return_1y, return_3y, return_5y
  - volatility, max_drawdown

- **user_recommendations**
  - recommendation_id
  - user_id (FK)
  - created_at
  - total_amount
  - expected_return_min, expected_return_max
  - risk_label

- **user_recommendation_items**
  - id
  - recommendation_id (FK)
  - product_id (FK)
  - allocation_percent
  - allocation_amount

---

## 📊 Data Sources

For **educational use only**, planned data sources:

- Yahoo Finance / `yfinance` for:
  - Nifty 50 index data
  - Gold ETF prices
  - Govt bond ETFs
- Mutual fund NAV data:
  - Public MF info portals (scraped or CSV)
- FD / liquid funds:
  - Static data manually entered for demo

> In the report/README:  
> “Real-time and historical data is sourced from public APIs / finance data providers like Yahoo Finance. Used only for academic purposes.”

---

## 🚀 Roadmap (Phases)

**Phase 1 – Core Logic (Offline)**  
- Implement risk scoring  
- Rule-based asset allocation  
- Simple hard-coded product list  
- Backtest using local CSV data  

**Phase 2 – Data Integration**  
- Integrate `yfinance` / other APIs  
- Automatically fetch Nifty, Gold, and NAV history  

**Phase 3 – Product Ranking (ML)**  
- Build dataset of funds with features  
- Implement weighted scoring  
- Optional: RandomForestRegressor for ranking  

**Phase 4 – Web App (Streamlit)**  
- Login/Signup  
- Questionnaire form  
- Recommendation page  
- Backtesting page  
- “My saved plans” page  

---

## 📌 Status

- [ ] Project setup  
- [ ] Core rule-based engine  
- [ ] Data integration  
- [ ] ML-based ranking  
- [ ] Streamlit UI  
- [ ] Backtesting charts  
- [ ] Documentation & final report  

---

## ⚠️ Disclaimer

This project is for **academic and learning purposes only**.  
It is **not** SEBI-registered financial advice and should not be used to make real investment decisions.
