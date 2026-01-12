"""Method A screening method - Revenue New High"""

from screening.list_revenue import list_revenue_new_high


def list_method_a(db, input_df=None):
    """Get stock list using Method A (Revenue New High)

    Args:
        db (StockDatabase): Database instance
        input_df (pd.DataFrame): Optional input list to filter
            If provided, filter only stocks in this list and accumulate scores.
            If None, use get_industrial_stocks as default.

    Returns:
        pd.DataFrame: DataFrame with columns ('code', 'name', 'score')
    """
    return list_revenue_new_high(
        db, recent_months=3, lookback_months=12, input_df=input_df
    )
