"""Financial metrics screening methods"""

import pandas as pd

from screening.helper import get_target_stocks


# H01_02: 近 N 季營業利益率為近 M 季最大  (P.S. 近 N 季中_有任何一季_)
#
# NOTE: this is like list_revenue_hit_new_high
def list_opr_margin_is_max(
    db, recent_n_quarters=1, lookback_m_quarters=4, input_df=None
):
    """Get stocks with recent operating margin is the max

    Find stocks whose operating margin over the last N quarters
    exceeds the maximum operating margin observed in the past M quarters.

    Args:
        db (StockDatabase): Database instance
        recent_n_quarters (int): Number of recent quarters to check
        lookback_m_quarters (int): Number of quarters to look back
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use stocks from list_industrial() as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if recent_n_quarters < 1:
        raise ValueError('recent_n_quarters must be >= 1')
    if lookback_m_quarters <= recent_n_quarters:
        raise ValueError('lookback_m_quarters must be > recent_n_quarters')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: already sorted by date ascending (old -> new)
        metrics_df = db.get_recent_financial_metrics_by_code(
            code, limit=lookback_m_quarters
        )

        # skip if not enough data
        if len(metrics_df) < lookback_m_quarters:
            continue

        # get data series
        vals = metrics_df['opr_margin']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # split into early period and recent period
        early_vals = vals.iloc[:-recent_n_quarters]
        recent_vals = vals.iloc[-recent_n_quarters:]

        # get max value in each period
        early_max = early_vals.max()
        recent_max = recent_vals.max()

        # skip if early period has no valid value
        if pd.isna(early_max) or pd.isna(recent_max):
            continue

        # check if recent max exceeds early max
        if recent_max > early_max:
            # --- score calculation ---
            # = percentage exceeded
            if early_max == 0:
                # TODO: reconsider this
                score = 0
            else:
                # (decimal to percentage)
                score = (recent_max - early_max) / abs(early_max) * 100

            # accumulate existing score
            final_score = row['score'] + score

            # append to results
            results.append(
                {
                    'code': code,
                    'name': row['name'],
                    'score': round(final_score, 2),
                }
            )

    # create result DataFrame and sort by score descending
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df


# H03_06: 近 N 季營業利益率最少 > T%  (P.S. 全部)
# -> 營業利益率連續 M 季 > T%
def list_opr_margin_above(db, cont_m_quarters=4, threshold=0.0, input_df=None):
    """Get stocks with operating margin over threshold consecutively

    Find stocks whose operating margin
    exceeds the specified threshold for M consecutive quarters.

    Args:
        db (StockDatabase): Database instance
        cont_m_quarters (int): Number of consecutive quarters to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if cont_m_quarters < 1:
        raise ValueError('cont_m_quarters must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # convert threshold to decimal for comparison
    threshold_dec = threshold / 100

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: already sorted by date ascending (old -> new)
        metrics_df = db.get_recent_financial_metrics_by_code(
            code, limit=cont_m_quarters
        )

        # skip if not enough data
        if len(metrics_df) < cont_m_quarters:
            continue

        # get data series
        vals = metrics_df['opr_margin']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # check if all > threshold
        if (vals > threshold_dec).all():
            # --- score calculation ---
            # = average exceeding amount (decimal to percentage)
            score = (vals - threshold_dec).mean() * 100

            # accumulate existing score
            final_score = row['score'] + score

            # append to results
            results.append(
                {
                    'code': code,
                    'name': row['name'],
                    'score': round(final_score, 2),
                }
            )

    # create result DataFrame and sort by score descending
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df


# H03_07: 近 N 季營業利益率季增率 > T%  (P.S. 全部)
# -> 營業利益率季增率連續 M 季 > T%
def list_opr_margin_qoq_above(db, cont_m_quarters=3, threshold=0.0, input_df=None):
    """Get stocks with operating margin QoQ above threshold consecutively

    Find stocks whose operating margin QoQ
    exceeds the specified threshold for M consecutive quarters.

    Args:
        db (StockDatabase): Database instance
        cont_m_quarters (int): Number of consecutive quarters to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use stocks from list_industrial() as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if cont_m_quarters < 1:
        raise ValueError('cont_m_quarters must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # convert threshold to decimal for comparison
    threshold_dec = threshold / 100

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: already sorted by date ascending (old -> new)
        metrics_df = db.get_recent_financial_metrics_by_code(
            code, limit=cont_m_quarters
        )

        # skip if not enough data
        if len(metrics_df) < cont_m_quarters:
            continue

        # get data series
        vals = metrics_df['opr_margin_qoq']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # check if all > threshold
        if (vals > threshold_dec).all():
            # --- score calculation ---
            # = average exceeding amount (decimal to percentage)
            score = (vals - threshold_dec).mean() * 100

            # accumulate existing score
            final_score = row['score'] + score

            # append to results
            results.append(
                {
                    'code': code,
                    'name': row['name'],
                    'score': round(final_score, 2),
                }
            )

    # create result DataFrame and sort by score descending
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df


# H03_08: 近 N 季營業利益率年增率 > T%  (P.S. 全部)
# -> 營業利益率年增率連續 M 季 > T%
def list_opr_margin_yoy_above(db, cont_m_quarters=3, threshold=0.0, input_df=None):
    """Get stocks with operating margin YoY above threshold consecutively

    Find stocks whose operating margin YoY
    exceeds the specified threshold for M consecutive quarters.

    Args:
        db (StockDatabase): Database instance
        cont_m_quarters (int): Number of consecutive quarters to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use stocks from list_industrial() as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if cont_m_quarters < 1:
        raise ValueError('cont_m_quarters must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # convert threshold to decimal for comparison
    threshold_dec = threshold / 100

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: already sorted by date ascending (old -> new)
        metrics_df = db.get_recent_financial_metrics_by_code(
            code, limit=cont_m_quarters
        )

        # skip if not enough data
        if len(metrics_df) < cont_m_quarters:
            continue

        # get data series
        vals = metrics_df['opr_margin_yoy']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # check if all > threshold
        if (vals > threshold_dec).all():
            # --- score calculation ---
            # = average exceeding amount (decimal to percentage)
            score = (vals - threshold_dec).mean() * 100

            # accumulate existing score
            final_score = row['score'] + score

            # append to results
            results.append(
                {
                    'code': code,
                    'name': row['name'],
                    'score': round(final_score, 2),
                }
            )

    # create result DataFrame and sort by score descending
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df


# H04_09: 近 N 季稅後純益率平均 > T%
def list_net_margin_avg_above(db, recent_n_quarters=4, threshold=0.0, input_df=None):
    """Get stocks with average net margin above threshold

    Find stocks whose average net margin
    exceeds the specified threshold in last N quarters.

    Args:
        db (StockDatabase): Database instance
        recent_n_quarters (int): Number of recent quarters to average
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if recent_n_quarters < 1:
        raise ValueError('recent_n_quarters must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # convert threshold to decimal for comparison
    threshold_dec = threshold / 100

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: already sorted by date ascending (old -> new)
        metrics_df = db.get_recent_financial_metrics_by_code(
            code, limit=recent_n_quarters
        )

        # skip if not enough data
        if len(metrics_df) < recent_n_quarters:
            continue

        # get data series
        vals = metrics_df['net_margin']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # calculate average
        val_avg = vals.mean()

        # check average
        if val_avg >= threshold_dec:
            # --- score calculation ---
            # = exceeding amount (decimal to percentage)
            score = (val_avg - threshold_dec) * 100

            # accumulate existing score
            final_score = row['score'] + score

            # append to results
            results.append(
                {
                    'code': code,
                    'name': row['name'],
                    'score': round(final_score, 2),
                }
            )

    # create result DataFrame and sort by score descending
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df


# H05_10: 近 N 季營業利益率最小/最大 > T%
def list_opr_margin_min_max_ratio_above(
    db, recent_n_quarters=4, threshold=0.0, input_df=None
):
    """Get stocks with min / max of operating margin over threshold

    Find stocks whose stability (min / max) of operating margin
    exceeds the specified threshold in last N quarters.

    A ratio close to 100% indicates very stable margins.

    Args:
        db (StockDatabase): Database instance
        recent_n_quarters (int): Number of recent quarters to calculate
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if recent_n_quarters < 1:
        raise ValueError('recent_n_quarters must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # convert threshold to decimal for comparison
    threshold_dec = threshold / 100

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: already sorted by date ascending (old -> new)
        metrics_df = db.get_recent_financial_metrics_by_code(
            code, limit=recent_n_quarters
        )

        # skip if not enough data
        if len(metrics_df) < recent_n_quarters:
            continue

        # get data series
        vals = metrics_df['opr_margin']

        # skip if any value is missing
        if vals.isna().any():
            continue

        val_min = vals.min()
        val_max = vals.max()

        # skip if max is not positive
        # (cannot divide or implies all negative/zero)
        if val_max <= 0:
            continue

        # calculate ratio in percentage
        ratio = (val_min / val_max) * 100

        # check ratio
        if ratio >= threshold_dec:
            # --- score calculation ---
            # = exceeding amount (decimal to percentage)
            score = (ratio - threshold_dec) * 100

            # accumulate existing score
            final_score = row['score'] + score

            # append to results
            results.append(
                {
                    'code': code,
                    'name': row['name'],
                    'score': round(final_score, 2),
                }
            )

    # create result DataFrame and sort by score descending
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df
