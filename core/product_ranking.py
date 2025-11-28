# core/product_ranking.py

import pandas as pd
import os

def load_products() -> pd.DataFrame:
    """
    Load products from CSV file.
    """
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_products.csv')
    df = pd.read_csv(csv_path)
    return df


def rank_products(asset_class: str, top_n: int = 3) -> pd.DataFrame:
    """
    Rank and return top N products for a given asset class.
    
    Ranking logic:
    - Higher returns are better (1Y, 3Y, 5Y weighted)
    - Lower expense ratio is better
    - Lower volatility is better
    - Higher rating is better
    """
    products_df = load_products()
    
    # Filter by asset class
    df = products_df[products_df["asset_class"] == asset_class].copy()
    
    if df.empty:
        return df
    
    # Calculate composite score
    # Weights: 30% 5Y return, 25% 3Y return, 20% 1Y return, 
    #          15% expense ratio (inverted), 5% volatility (inverted), 5% rating
    df["score"] = (
        0.30 * df["five_yr_return"] +
        0.25 * df["three_yr_return"] +
        0.20 * df["one_yr_return"] +
        0.15 * (10 - df["expense_ratio"]) +  # Lower is better, so invert
        0.05 * (20 - df["volatility"]) +     # Lower is better, so invert
        0.05 * df["rating"]
    )
    
    # Sort by score descending
    df = df.sort_values("score", ascending=False)
    
    # Return top N
    return df.head(top_n)


def get_recommended_products(allocation: dict, top_n: int = 2) -> dict:
    """
    Get recommended products for each asset class in the allocation.
    
    Args:
        allocation: Dict with asset classes and their percentages
        top_n: Number of top products to return per asset class
        
    Returns:
        Dict with asset class as key and list of recommended products as value
    """
    recommendations = {}
    
    for asset_class, percentage in allocation.items():
        if percentage > 0:
            top_products = rank_products(asset_class, top_n)
            
            if not top_products.empty:
                recommendations[asset_class] = top_products.to_dict('records')
    
    return recommendations


def format_product_display(product: dict) -> str:
    """
    Format a product for display in the UI.
    """
    return f"""
**{product['name']}**  
- 1Y Return: {product['one_yr_return']:.1f}%  
- 3Y Return: {product['three_yr_return']:.1f}%  
- 5Y Return: {product['five_yr_return']:.1f}%  
- Expense Ratio: {product['expense_ratio']:.2f}%  
- Volatility: {product['volatility']:.1f}%  
- Rating: {'⭐' * int(product['rating'])}  
    """
