# core/data_fetcher.py

import yfinance as yf
import pandas as pd
from typing import Tuple
from datetime import datetime, timedelta

def get_nifty_pe() -> Tuple[float, float, bool]:
    """
    Fetch Nifty 50 P/E ratio and compare with historical average.
    Returns: (current_pe, average_pe, is_overvalued)
    
    Note: This is a simplified implementation using proxy data.
    In production, you'd use NSE API or paid data sources.
    """
    try:
        # Using Nifty 50 ETF as proxy (adjust ticker as needed)
        nifty = yf.Ticker("^NSEI")
        
        # Get historical P/E data (simplified - using price as proxy)
        hist = nifty.history(period="1y")
        
        if hist.empty:
            # Fallback to dummy values if API fails
            return 23.0, 20.0, True
        
        # Simplified P/E estimation
        current_price = hist['Close'].iloc[-1]
        avg_price = hist['Close'].mean()
        
        # Rough P/E proxy (you'd normally get actual P/E from NSE)
        current_pe = 22.5  # Placeholder - replace with actual data
        historical_avg_pe = 20.0
        
        is_overvalued = current_pe > historical_avg_pe * 1.05
        
        return current_pe, historical_avg_pe, is_overvalued
        
    except Exception as e:
        print(f"Error fetching Nifty data: {e}")
        # Return dummy values on error
        return 23.0, 20.0, True


def get_gold_valuation() -> Tuple[float, float, bool]:
    """
    Check if gold price is at recent peak.
    Returns: (current_price, one_year_avg, is_overvalued)
    """
    try:
        # Gold ETF ticker
        gold = yf.Ticker("GC=F")  # Gold Futures
        
        hist = gold.history(period="1y")
        
        if hist.empty:
            return 2000.0, 1900.0, False
        
        current_price = hist['Close'].iloc[-1]
        one_year_avg = hist['Close'].mean()
        one_year_high = hist['Close'].max()
        
        # Consider overvalued if within 5% of yearly high
        is_overvalued = current_price > one_year_high * 0.95
        
        return current_price, one_year_avg, is_overvalued
        
    except Exception as e:
        print(f"Error fetching gold data: {e}")
        return 2000.0, 1900.0, False


def is_equity_overvalued(threshold: float = 1.05) -> bool:
    """
    Simple check if equity market is overvalued.
    """
    _, avg_pe, is_over = get_nifty_pe()
    return is_over


def is_gold_overvalued() -> bool:
    """
    Simple check if gold is at peak.
    """
    _, _, is_over = get_gold_valuation()
    return is_over


def get_market_summary() -> dict:
    """
    Get comprehensive market summary for display.
    """
    nifty_pe, nifty_avg_pe, equity_overvalued = get_nifty_pe()
    gold_price, gold_avg, gold_overvalued = get_gold_valuation()
    
    return {
        "nifty_pe": nifty_pe,
        "nifty_avg_pe": nifty_avg_pe,
        "equity_status": "Overvalued" if equity_overvalued else "Normal/Undervalued",
        "gold_price": gold_price,
        "gold_avg": gold_avg,
        "gold_status": "At Peak" if gold_overvalued else "Normal",
    }
