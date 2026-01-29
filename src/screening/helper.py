"""Helper functions for screening methods"""


def get_target_stocks(db, input_df):
    """Helper to setup input stocks.

    Args:
        db (StockDatabase): Database instance
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        tuple: (stock_codes, code_to_name, code_to_score)
    """
    if input_df is not None and not input_df.empty:
        stock_codes = input_df['code'].tolist()
        code_to_name = dict(zip(input_df['code'], input_df['name']))
        code_to_score = dict(zip(input_df['code'], input_df['score']))
    else:
        stocks_df = db.get_industrial_stocks()
        if stocks_df.empty:
            return [], {}, {}
        stock_codes = stocks_df['code'].tolist()
        code_to_name = dict(zip(stocks_df['code'], stocks_df['name']))
        code_to_score = {}
    return stock_codes, code_to_name, code_to_score
