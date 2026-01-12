"""Industrial stocks list screening method"""

import pandas as pd


def list_industrial(db, input_df=None):
    """Get general industrial and commercial stocks

    Args:
        db (StockDatabase): Database instance
        input_df (pd.DataFrame): Optional input list to filter
            If provided, filter only stocks in this list and accumulate scores.
            If None, return all industrial stocks in market.

    Returns:
        pd.DataFrame: DataFrame with columns ('code', 'name', 'score')
    """
    # get all industrial stocks
    industrial_df = db.get_industrial_stocks()

    if industrial_df.empty:
        print('Warning: No industrial stocks found')

        if input_df is None:
            return pd.DataFrame(columns=['code', 'name', 'score'])

        # TODO: handle case when input_df is not None
        return input_df.copy()

    # ensure consistent columns
    industrial_df = industrial_df[['code', 'name']]

    if input_df is not None and not input_df.empty:
        # filter: keep only stocks that are in BOTH lists (intersection)
        # use input_df as base to preserve existing scores/names
        merged_df = pd.merge(input_df, industrial_df[['code']], on='code', how='inner')

        # accumulate score by 1
        merged_df['score'] = merged_df['score'] + 1

        # sort by score descending
        merged_df = merged_df.sort_values(by='score', ascending=False).reset_index(
            drop=True
        )

        return merged_df[['code', 'name', 'score']]

    else:
        # No input_df. Return all industrial stocks with score 1.
        # Use .copy() to avoid SettingWithCopyWarning if industrial_df is a slice
        result_df = industrial_df.copy()

        result_df['score'] = 1

        return result_df[['code', 'name', 'score']]
