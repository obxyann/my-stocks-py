"""Industrial stocks list screening method"""

import pandas as pd

from database.stock import StockDatabase


def list_industrial(db):
    """Get list of general industrial and commercial stocks

    Args:
        db (StockDatabase): Database instance

    Returns:
        pd.DataFrame: DataFrame with columns ('code', 'name')
    """
    df = db.get_industrial_stocks()

    # return only 'code' and 'name' columns
    if df.empty:
        return pd.DataFrame(columns=['code', 'name'])

    return df[['code', 'name']]
