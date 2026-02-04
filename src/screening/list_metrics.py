"""Financial metrics screening methods"""

import pandas as pd

from screening.helper import get_target_stocks


# R07: 近 N 季稅後純益率(net_margin)平均 > P%
def list_net_margin_avg_above(db, recent_n_quarters=4, threshold=0.0, input_df=None):
    """Get stocks with average net margin above threshold

    Find stocks whose average net margin exceeds the specified threshold
    in last N quarters.

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

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        df_metrics = db.get_recent_financial_metrics_by_code(
            code, limit=recent_n_quarters
        )

        # skip if not enough data
        if len(df_metrics) < recent_n_quarters:
            continue

        # get net margin series, drop None/NaN
        margins = df_metrics['net_margin'].dropna()

        # skip if empty
        if margins.empty:
            continue

        # convert to percentage and calculate average
        # e.g. 0.05 -> 5.0(%)
        val_avg = (margins * 100).mean()

        if val_avg > threshold:
            # calculate score:
            # = exceeding amount
            score = val_avg - threshold

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


# R08: 近 N 季營業利益率(opr_margin)最少 ＞ P%
def list_opr_margin_min_above(db, recent_n_quarters=4, threshold=0.0, input_df=None):
    """Get stocks with minimum operating margin over threshold

    Find stocks whose minimum operating margin exceeds the specified threshold
    in last N quarters.

    Args:
        db (StockDatabase): Database instance
        recent_n_quarters (int): Number of recent quarters to check
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

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        df_metrics = db.get_recent_financial_metrics_by_code(
            code, limit=recent_n_quarters
        )

        # skip if not enough data
        if len(df_metrics) < recent_n_quarters:
            continue

        # get opr margin series, drop None/NaN
        margins = df_metrics['opr_margin'].dropna()

        # skip if empty
        if margins.empty:
            continue

        # convert to percentage and get min
        val_min = (margins * 100).min()

        if val_min > threshold:
            # calculate score:
            # = exceeding amount
            score = val_min - threshold

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


# R09: 近 N 季營業利益率(opr_margin)最小/最大 ＞ P%
def list_opr_margin_min_max_ratio_above(
    db, recent_n_quarters=4, threshold=0.0, input_df=None
):
    """Get stocks with (min operating margin/max operating margin) over
    threshold

    This metric is often used to assess the stability of margin.
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

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        df_metrics = db.get_recent_financial_metrics_by_code(
            code, limit=recent_n_quarters
        )

        # skip if not enough data
        if len(df_metrics) < recent_n_quarters:
            continue

        # get opr margin series, drop None/NaN
        margins = df_metrics['opr_margin'].dropna()

        # skip if empty
        if margins.empty:
            continue

        # convert to percentage
        series_percent = margins * 100

        val_min = series_percent.min()
        val_max = series_percent.max()

        # skip if max is not positive
        # (cannot divide or implies all negative/zero)
        if val_max <= 0:
            continue

        # calculate ratio in percentage
        ratio = (val_min / val_max) * 100

        if ratio > threshold:
            # calculate score:
            # = exceeding amount
            score = ratio - threshold

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


# R01a: 近 N 季營業利益率(opr_margin)為近 M 季最大
def list_opr_margin_is_max(
    db, recent_n_quarters=1, lookback_m_quarters=4, input_df=None
):
    """Get stocks with recent operating margin is the max

    Find stocks whose operating margin over the last N quarters exceeds the
    maximum operating margin observed in the past M quarters.

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
        # NOTE: ensure sorted by date ascending (old -> new)
        df_metrics = db.get_recent_financial_metrics_by_code(
            code, limit=lookback_m_quarters
        )

        # skip if not enough data
        if len(df_metrics) < lookback_m_quarters:
            continue

        # get opr margin series
        margins = df_metrics['opr_margin']

        # skip if any value is missing
        if margins.isna().any():
            continue

        # split into early period and recent period
        early_vals = margins.iloc[:-recent_n_quarters]
        recent_vals = margins.iloc[-recent_n_quarters:]

        # get max value in each period
        early_max = early_vals.max()
        recent_max = recent_vals.max()

        # skip if early period has no valid value
        # NOTE: normaly this should not happen, we had guranteed
        #       enough data > recent_n_quarters
        if pd.isna(early_max):
            continue

        if recent_max >= early_max:
            # calculate score:
            # = percentage exceeded
            if early_max == 0:
                # TODO: reconsider this
                score = 0
            else:
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


# R10: 近 N 季營業利益率季增率(opr_margin_qoq)連續 M 季成長
def list_opr_margin_qoq_growth(
    db, recent_n_quarters=4, cont_m_quarters=3, input_df=None
):
    """Get stocks with with consecutive growth in operating margin QoQ

    Find stocks whose N-month operating margin QoQ
    increases quarter over quarter for M consecutive quarters.

    Args:
        db (StockDatabase): Database instance
        recent_n_quarters (int): Number of recent quarters to check
        cont_m_quarters (int): Number of consecutive quarters to check
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
    if cont_m_quarters > recent_n_quarters:
        raise ValueError('cont_m_quarters must be <= recent_n_quarters')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # need one extra point to calculate increasing (growth)
    need_points = cont_m_quarters + 1

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: ensure sorted by date ascending (old -> new)
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=need_points)

        # skip if not enough data
        if len(df_metrics) < need_points:
            continue

        # get opr margin QoQ values
        qoqs = df_metrics['opr_margin_qoq']

        # skip if any value is missing
        if qoqs.isna().any():
            continue

        # check strictly increasing
        is_increasing = (qoqs.diff().iloc[1:] > 0).all()

        if is_increasing:
            # calculate score:
            # = exceeding amount
            score = qoqs.iloc[-1] - qoqs.iloc[0]

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


# R10: 近 N 季營業利益率年增率(opr_margin_yoy)連續 M 季成長
def list_opr_margin_yoy_growth(
    db, recent_n_quarters=4, cont_m_quarters=3, input_df=None
):
    """Get stocks with with consecutive growth in operating margin YoY

    Find stocks whose N-month operating margin YoY
    increases quarter over quarter for M consecutive quarters.

    Args:
        db (StockDatabase): Database instance
        recent_n_quarters (int): Number of recent quarters to check
        cont_m_quarters (int): Number of consecutive quarters to check
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
    if cont_m_quarters > recent_n_quarters:
        raise ValueError('cont_m_quarters must be <= recent_n_quarters')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # need one extra point to calculate increasing (growth)
    need_points = cont_m_quarters + 1

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent financial metrics
        # NOTE: ensure sorted by date ascending (old -> new)
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=need_points)

        # skip if not enough data
        if len(df_metrics) < need_points:
            continue

        # get opr margin YoY series
        yoys = df_metrics['opr_margin_yoy']

        # skip if any value is missing
        if yoys.isna().any():
            continue

        # check strictly increasing
        is_increasing = (yoys.diff().iloc[1:] > 0).all()

        if is_increasing:
            # calculate score:
            # = exceeding amount
            score = yoys.iloc[-1] - yoys.iloc[0]

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
