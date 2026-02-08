"""Helper functions for screening methods"""

import pandas as pd


def get_target_stocks(db, input_df):
    """Helper to setup input stocks

    Args:
        db (StockDatabase): Database instance
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']

    Returns:
        pd.DataFrame: DataFrame with columns ['code', 'name', 'score']
    """
    if input_df is not None and not input_df.empty:
        # return copy of input_df to avoid modifying original
        return input_df[['code', 'name', 'score']].copy()
    else:
        stocks_df = db.get_industrial_stocks()

        if stocks_df.empty:
            return pd.DataFrame(columns=['code', 'name', 'score'])

        # initialize score column to 0
        stocks_df['score'] = 0

        return stocks_df[['code', 'name', 'score']].copy()
