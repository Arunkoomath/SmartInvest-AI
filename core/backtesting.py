"""
Backtesting Module
Simulates historical portfolio performance and compares strategies
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta


def fetch_historical_data(years=5):
    """
    Fetch historical price data for representative assets
    Returns: dict with DataFrames for each asset class
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    try:
        # Nifty 50 ETF as equity proxy
        nifty = yf.download("^NSEI", start=start_date, end=end_date, progress=False)['Adj Close']
        
        # Gold ETF proxy
        gold = yf.download("GC=F", start=start_date, end=end_date, progress=False)['Adj Close']
        
        # 10-year bond yield proxy (inverted for gilt fund simulation)
        # Using a constant 7% annual return as proxy for Indian gilt funds
        gilt_dates = nifty.index
        gilt = pd.Series(index=gilt_dates, data=100)
        for i in range(1, len(gilt)):
            days_elapsed = (gilt_dates[i] - gilt_dates[0]).days
            gilt.iloc[i] = 100 * (1.07 ** (days_elapsed / 365))
        
        # Debt/liquid fund proxy - 6% annual return
        debt = pd.Series(index=gilt_dates, data=100)
        for i in range(1, len(debt)):
            days_elapsed = (gilt_dates[i] - gilt_dates[0]).days
            debt.iloc[i] = 100 * (1.06 ** (days_elapsed / 365))
        
        return {
            'equity': nifty,
            'gold': gold,
            'gilt': gilt,
            'debt': debt
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        # Return dummy data as fallback
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        return {
            'equity': pd.Series(index=dates, data=np.linspace(100, 180, len(dates))),
            'gold': pd.Series(index=dates, data=np.linspace(100, 140, len(dates))),
            'gilt': pd.Series(index=dates, data=np.linspace(100, 140, len(dates))),
            'debt': pd.Series(index=dates, data=np.linspace(100, 134, len(dates)))
        }


def simulate_portfolio(allocation, historical_data, initial_amount=100000):
    """
    Simulate portfolio performance based on allocation
    
    Args:
        allocation: dict with percentages for equity, gold, gilt, debt
        historical_data: dict with price series for each asset class
        initial_amount: starting investment amount
    
    Returns:
        pandas Series with portfolio value over time
    """
    # Align all data to common dates
    df = pd.DataFrame(historical_data)
    df = df.dropna()
    
    # Normalize to start at 100
    for col in df.columns:
        df[col] = (df[col] / df[col].iloc[0]) * 100
    
    # Calculate portfolio value
    portfolio_value = pd.Series(index=df.index, data=0.0)
    
    for asset_class, pct in allocation.items():
        if asset_class in df.columns and pct > 0:
            portfolio_value += (pct / 100) * df[asset_class]
    
    # Scale to initial amount
    portfolio_value = (portfolio_value / 100) * initial_amount
    
    return portfolio_value


def calculate_cagr(start_value, end_value, years):
    """Calculate Compound Annual Growth Rate"""
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def calculate_max_drawdown(portfolio_series):
    """Calculate maximum drawdown percentage"""
    cummax = portfolio_series.cummax()
    drawdown = (portfolio_series - cummax) / cummax * 100
    return drawdown.min()


def calculate_sharpe_ratio(portfolio_series, risk_free_rate=0.06):
    """Calculate Sharpe ratio (assuming 6% risk-free rate)"""
    returns = portfolio_series.pct_change().dropna()
    excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
    
    if excess_returns.std() == 0:
        return 0.0
    
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)


def run_backtest(allocation, years=5, initial_amount=100000):
    """
    Run complete backtest for a given allocation
    
    Returns:
        dict with portfolio_series, cagr, max_drawdown, sharpe_ratio, final_value
    """
    historical_data = fetch_historical_data(years)
    portfolio_series = simulate_portfolio(allocation, historical_data, initial_amount)
    
    start_value = portfolio_series.iloc[0]
    end_value = portfolio_series.iloc[-1]
    actual_years = (portfolio_series.index[-1] - portfolio_series.index[0]).days / 365
    
    cagr = calculate_cagr(start_value, end_value, actual_years)
    max_dd = calculate_max_drawdown(portfolio_series)
    sharpe = calculate_sharpe_ratio(portfolio_series)
    
    return {
        'portfolio_series': portfolio_series,
        'cagr': cagr,
        'max_drawdown': max_dd,
        'sharpe_ratio': sharpe,
        'final_value': end_value,
        'initial_value': start_value,
        'total_return': ((end_value - start_value) / start_value) * 100
    }


def compare_strategies(recommended_allocation, initial_amount=100000, years=5):
    """
    Compare recommended allocation vs benchmark strategies
    
    Returns:
        dict with results for recommended, nifty_only, fd_only
    """
    # Recommended portfolio
    recommended_results = run_backtest(recommended_allocation, years, initial_amount)
    
    # 100% Equity (Nifty 50)
    nifty_allocation = {'equity': 100, 'gold': 0, 'gilt': 0, 'debt': 0}
    nifty_results = run_backtest(nifty_allocation, years, initial_amount)
    
    # 100% Debt (FD equivalent)
    fd_allocation = {'equity': 0, 'gold': 0, 'gilt': 0, 'debt': 100}
    fd_results = run_backtest(fd_allocation, years, initial_amount)
    
    return {
        'Recommended Portfolio': recommended_results,
        'Nifty 50 Only': nifty_results,
        'Fixed Deposit Only': fd_results
    }
