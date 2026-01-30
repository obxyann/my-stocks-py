"""Revenue screening methods"""

import pandas as pd

from screening.helper import get_target_stocks


# R01: 近 N 個月營收創近 M 月新高
#      (or 營收連續 N 個月創近 M 月新高)
#      (or 近 N 月營收為近 M 月最大)
def list_revenue_hit_new_high(
    db, recent_n_months=3, lookback_m_months=12, input_df=None
):
    """Get stocks with recent revenue reaching a new high

    Find stocks whose revenue over the last N months exceeds the maximum
    revenue observed in the past M months.

    Args:
        db (StockDatabase): Database instance
        recent_n_months (int): Number of recent months to check
        lookback_m_months (int): Number of lookback months
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use stocks from list_industrial() as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
            score is the percentage by which the recent high exceeds
            the previous high
    """
    # check input parameters
    if recent_n_months < 1 or lookback_m_months < 1:
        raise ValueError('recent_n_months and lookback_m_months must be >= 1')
    if recent_n_months > lookback_m_months:
        raise ValueError('recent_n_months must be <= lookback_m_months')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # determine months to compare with recent
    early_months = lookback_m_months - recent_n_months

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=lookback_m_months)

        # skip if not enough data
        if len(revenue_df) < lookback_m_months:
            continue

        # ensure sorted by date ascending
        revenue_df = revenue_df.sort_values(
            by=['year', 'month'], ascending=True
        ).reset_index(drop=True)

        # split into early period and recent period
        early_df = revenue_df.iloc[:early_months]
        recent_df = revenue_df.iloc[early_months:]

        # get max revenue in each period
        early_max = early_df['revenue'].max()
        recent_max = recent_df['revenue'].max()

        # skip if early period has no valid revenue
        if pd.isna(early_max) or early_max <= 0:
            continue

        # check if recent max exceeds early max
        if recent_max > early_max:
            # calculate score:
            # percentage exceeded
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


# R02: 營收月增率(revenue_mom)連續 N 個月 > P%
def list_revenue_mom_above(db, cont_n_months=3, threshold=0.0, input_df=None):
    """Get stocks with revenue MoM above threshold consecutively

    Find stocks whose revenue MoM exceeds the specified threshold
    for N consecutive months.

    Args:
        db (StockDatabase): Database instance
        cont_n_months (int): Number of consecutive months to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if cont_n_months < 1:
        raise ValueError('cont_n_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # sorted by date ascending (old -> new)
        df_rev = db.get_recent_revenue_by_code(code, limit=cont_n_months)

        # skip if not enough data
        if len(df_rev) < cont_n_months:
            continue

        # get revenue MoM
        moms = df_rev['revenue_mom'].tolist()

        # check if all MoM > threshold
        if any(pd.isna(m) or m <= threshold for m in moms):
            continue

        # calculate score:
        # sum of excess over threshold
        score = sum(m - threshold for m in moms)

        # accumulate existing score
        final_score = row['score'] + score

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


# R02: 營收年增率(revenue_yoy)連續 N 個月 > P%
def list_revenue_yoy_above(db, cont_n_months=3, threshold=0.0, input_df=None):
    """Get stocks with revenue YoY above threshold consecutively

    Find stocks whose revenue YoY exceeds the specified threshold
    for N consecutive months.

    Args:
        db (StockDatabase): Database instance
        cont_n_months (int): Number of consecutive months to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if cont_n_months < 1:
        raise ValueError('consec_n_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # sorted by date ascending (old -> new)
        df_rev = db.get_recent_revenue_by_code(code, limit=cont_n_months)

        # skip if not enough data
        if len(df_rev) < cont_n_months:
            continue

        # get revenue YoY
        yoys = df_rev['revenue_yoy'].tolist()

        # check if all YoY > threshold
        if any(pd.isna(y) or y <= threshold for y in yoys):
            continue

        # calculate score:
        # sum of excess growth over threshold
        score = sum(y - threshold for y in yoys)

        # accumulate existing score
        final_score = row['score'] + score

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


# R03: N 個月平均營收連續 M 個月成長
def list_revenue_ma_growth(db, ma_n_months, cont_m_months=3, input_df=None):
    """Get stocks with consecutive growth in revenue moving average

    Find stocks whose N-month revenue moving average
    increases month over month for M consecutive months.

    Args:
        db (StockDatabase): Database instance
        ma_n_months (int): Moving average window size (e.g. 3, 12)
        cont_m_months (int): Number of consecutive months to check
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if ma_n_months < 2:
        raise ValueError('ma_n_months must be >= 2')
    if cont_m_months < 1:
        raise ValueError('cont_m_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # determine strategy based on ma_n_months
    if ma_n_months in (3, 12):
        # use pre-calculated columns
        use_precalc = True

        col_name = f'revenue_ma{ma_n_months}'

        # to check consecutive growth for M months
        # we need M+1 data points
        needed_points = cont_m_months + 1
    else:
        # calculate MA on the fly
        use_precalc = False

        col_name = None

        # to calculate the first N-months MA, we need N data points
        # we need additional M data points of MA to check for consecutive M growth
        # so total data points needed = N + M
        needed_points = ma_n_months + cont_m_months

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # sorted by date ascending (old -> new)
        df_rev = db.get_recent_revenue_by_code(code, limit=needed_points)

        # skip if not enough data
        if len(df_rev) < needed_points:
            continue

        # get target MA values
        if use_precalc:
            vals = df_rev[col_name].tolist()
        else:
            # calculate MA on the fly
            # df_rev is sorted ascending by date
            ma_series = df_rev['revenue'].rolling(window=ma_n_months).mean()

            # we only need the last (cont_m_months + 1) valid MA values
            vals = ma_series.tail(cont_m_months + 1).tolist()

        # check for valid data
        if len(vals) < cont_m_months + 1 or any(v is None or pd.isna(v) for v in vals):
            continue

        # check strictly increasing (continuous growth)
        # vals is [t-M, t-M+1, ..., t]
        is_increasing = True

        for i in range(len(vals) - 1):
            if vals[i + 1] <= vals[i]:
                is_increasing = False
                break

        if is_increasing:
            # calculate score:
            # percentage growth rate over the period
            # score = (end_value - start_val) / start_val * 100
            start_val = vals[0]
            end_val = vals[-1]

            if start_val == 0:
                score = 0
            else:
                score = (end_val - start_val) / abs(start_val) * 100

            # accumulate score
            final_score = row['score'] + score

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


# R03: N 個月平均累積營收年增率(revenue_ytd_yoy)連續 M 個月成長
def list_accum_revenue_yoy_ma_growth(db, ma_n_months=3, cont_m_months=3, input_df=None):
    """Get stocks with consecutive growth in accumulated (YTD) revenue YOY
    moving average

    Find stocks whose N-month accumulated (YTD) revenue YOY moving average
    increases month over month for M consecutive months.

    Args:
        db (StockDatabase): Database instance
        ma_n_months (int): Moving average window size (e.g. 3, 12)
        cont_m_months (int): Number of consecutive months to check
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if ma_n_months < 2:
        raise ValueError('ma_n_months must be >= 2')
    if cont_m_months < 1:
        raise ValueError('cont_m_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # calculate MA on the fly

    # to calculate the first N-months MA, we need N data points
    # we need additional M data points of MA to check for consecutive M growth
    # so total data points needed = N + M
    need_points = ma_n_months + cont_m_months

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # sorted by date ascending (old -> new)
        df_rev = db.get_recent_revenue_by_code(code, limit=need_points)

        # skip if not enough data
        if len(df_rev) < need_points:
            continue

        # calculate MA on the fly
        # df_rev is sorted ascending by date
        ma_series = df_rev['revenue_ytd_yoy'].rolling(window=ma_n_months).mean()

        # we only need the last (cont_m_months + 1) valid MA values
        vals = ma_series.tail(cont_m_months + 1).tolist()

        # check for valid data
        if len(vals) < cont_m_months + 1 or any(v is None or pd.isna(v) for v in vals):
            continue

        # check strictly increasing (continuous growth)
        # vals is [t-M, ..., t]
        is_increasing = True

        for i in range(len(vals) - 1):
            if vals[i + 1] <= vals[i]:
                is_increasing = False
                break

        if is_increasing:
            # calculate score:
            # percentage growth rate over the period
            # score = (end_value - start_val) / start_val * 100
            start_val = vals[0]
            end_val = vals[-1]

            if start_val == 0:
                score = 0
            else:
                score = (end_val - start_val) / abs(start_val) * 100

            # accumulate existing score
            final_score = row['score'] + score

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


# R04: N 個月平均累積營收年增率(revenue_ytd_yoy)成長幅度 > P%
def list_accum_revenue_yoy_ma_growth_above(
    db, ma_n_months=3, threshold=0.0, input_df=None
):
    """Get stocks with last growth rate above threshold in accumulated (YTD)
    revenue YOY moving average

    Find stocks whose last growth rate of N-month accumulated (YTD) revenue YOY
    moving average exceeds the specified threshold.

    Args:
        db (StockDatabase): Database instance
        ma_n_months (int): Moving average window size (e.g. 3, 12)
        threshold (float): Threshold percentage
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if ma_n_months < 1:
        raise ValueError('ma_n_months must be >= 1')

    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # to calculate the N-months MA, we need N data points
    # need one extra point to calculate previous MA for growth rate comparison
    needed_points = ma_n_months + 1

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # sorted by date ascending (old -> new)
        df_rev = db.get_recent_revenue_by_code(code, limit=needed_points)

        # skip if not enough data
        if len(df_rev) < needed_points:
            continue

        # calculate MA on the fly
        # df_rev is sorted ascending by date
        ma_series = df_rev['revenue_ytd_yoy'].rolling(window=ma_n_months).mean()

        # we only need the last 2 valid MA values
        vals = ma_series.tail(2).tolist()

        # check for valid data
        if len(vals) < 2 or any(v is None or pd.isna(v) for v in vals):
            continue

        prev_val = vals[0]
        curr_val = vals[1]

        # calculate growth rate
        if prev_val == 0:
            growth_rate = 0.0
        else:
            growth_rate = (curr_val - prev_val) / abs(prev_val) * 100

        if growth_rate > threshold:
            # calculate score:
            # ammount over threshold
            score = growth_rate - threshold

            # accumulate existing score
            final_score = row['score'] + score

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
