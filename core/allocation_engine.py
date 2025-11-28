from typing import Dict

def base_allocation(risk_level: str, horizon_years: int) -> Dict[str, float]:
    """
    Returns base allocation across asset classes (in %)
    asset classes: 'equity', 'gold', 'gilt', 'debt'
    """

    # Conservative investors
    if risk_level == "Low":
        if horizon_years < 3:
            return {"equity": 20, "gold": 10, "gilt": 30, "debt": 40}
        else:
            return {"equity": 35, "gold": 15, "gilt": 30, "debt": 20}

    # Moderate investors
    if risk_level == "Medium":
        if horizon_years < 5:
            return {"equity": 45, "gold": 15, "gilt": 25, "debt": 15}
        else:
            return {"equity": 55, "gold": 20, "gilt": 15, "debt": 10}

    # Aggressive investors
    if horizon_years < 5:
        return {"equity": 60, "gold": 20, "gilt": 10, "debt": 10}
    else:
        return {"equity": 70, "gold": 15, "gilt": 10, "debt": 5}


def adjust_for_valuation(allocation: Dict[str, float],
                         equity_overvalued: bool,
                         gold_overvalued: bool) -> Dict[str, float]:
    """
    Tilt the allocation based on valuation signals.
    Very simple adjustment for now.
    """
    alloc = allocation.copy()

    if equity_overvalued:
        # shift 10% from equity to gilt/gold
        shift = min(10, alloc["equity"])
        alloc["equity"] -= shift
        alloc["gilt"] += shift / 2
        alloc["gold"] += shift / 2

    if gold_overvalued:
        # shift 5% from gold to equity/gilt
        shift = min(5, alloc["gold"])
        alloc["gold"] -= shift
        alloc["equity"] += shift * 0.6
        alloc["gilt"] += shift * 0.4

    # Ensure rounding to 100
    total = sum(alloc.values())
    for k in alloc:
        alloc[k] = round(alloc[k] * 100 / total, 2)

    return alloc

