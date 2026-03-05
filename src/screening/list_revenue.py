"""Revenue screening methods"""

import pandas as pd

from screening.helper import get_target_stocks


# R01: 近 N 個月營收創近 M 月新高  (P.S. 近 N 個月中_有任何一個月_)
#      近 N 個月營收為近 M 月最大  (P.S. 近 N 個月中_有任何一個月_)
def list_revenue_hit_new_high(
    db, recent_n_months=3, lookback_m_months=12, input_df=None
):
    """Get stocks with recent revenue reaching a new high

    Find stocks whose revenue over the last N months (at least one month)
    is the highest among the revenues in the past M months.

    Args:
        db (StockDatabase): Database instance
        recent_n_months (int): Number of recent months to check
        lookback_m_months (int): Number of months to look back
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
    if recent_n_months < 1:
        raise ValueError('recent_n_months must be >= 1')
    if lookback_m_months <= recent_n_months:
        raise ValueError('lookback_m_months > recent_n_months')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=lookback_m_months)

        # skip if not enough data
        if len(revenue_df) < lookback_m_months:
            continue

        # ensure sorted by date ascending
        # revenue_df = revenue_df.sort_values(
        #     by=['year', 'month'], ascending=True
        # ).reset_index(drop=True)

        # get data series
        vals = revenue_df['revenue']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # split into early period and recent period
        early_vals = vals.iloc[:-recent_n_months]
        recent_vals = vals.iloc[-recent_n_months:]

        # get max value in each period
        early_max = early_vals.max()
        recent_max = recent_vals.max()

        # skip if invalid values
        # NOTE: normaly this should not happen, we had guranteed enough data
        if pd.isna(early_max) or pd.isna(recent_max):
            continue

        # check if recent max exceeds early max
        if recent_max > early_max:
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


# R02: 營收月增率連續 M 個月 > T%
#      近 M 個月營收月增率 > T%  (P.S. 全部)
def list_revenue_mom_above(db, cont_m_months=3, threshold=0.0, input_df=None):
    """Get stocks with revenue MoM above threshold consecutively

    Find stocks whose revenue MoM
    exceeds the specified threshold for M consecutive months.

    Args:
        db (StockDatabase): Database instance
        cont_m_months (int): Number of consecutive months to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if cont_m_months < 1:
        raise ValueError('cont_m_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # convert threshold to decimal for comparison
    threshold = threshold / 100

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=cont_m_months)

        # skip if not enough data
        if len(revenue_df) < cont_m_months:
            continue

        # get data series
        vals = revenue_df['revenue_mom']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # check if all > threshold
        if (vals > threshold).all():
            # calculate score:
            # = average exceeding amount (decimal to percentage)
            score = (vals - threshold).mean() * 100

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


# R02: 營收年增率連續 M 個月 > T%
#      近 M 個月營收年增率 > T%  (P.S. 全部)
def list_revenue_yoy_above(db, cont_m_months=3, threshold=0.0, input_df=None):
    """Get stocks with revenue YoY above threshold consecutively

    Find stocks whose revenue YoY
    exceeds the specified threshold for M consecutive months.

    Args:
        db (StockDatabase): Database instance
        cont_m_months (int): Number of consecutive months to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if cont_m_months < 1:
        raise ValueError('cont_m_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    # convert threshold to decimal for comparison
    threshold = threshold / 100

    results = []

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=cont_m_months)

        # skip if not enough data
        if len(revenue_df) < cont_m_months:
            continue

        # get data series
        vals = revenue_df['revenue_yoy']

        # skip if any value is missing
        if vals.isna().any():
            continue

        # check if all > threshold
        if (vals > threshold).all():
            # calculate score:
            # = average exceeding amount (decimal to percentage)
            score = (vals - threshold).mean() * 100

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


# R03: N 個月平均(MA)營收連續 M 個月成長  (P.S. 數值遞增)
def list_revenue_ma_growth(db, ma_n_months, cont_m_months=3, input_df=None):
    """Get stocks with consecutive growth in revenue moving average

    Find stocks whose N-month moving average of revenue
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

    # to calculate the first N-month MA, we need N data points
    # we need additional M data points of MA to check for consecutive M growth
    # so total data points needed = N + M
    needed_points = ma_n_months + cont_m_months

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=needed_points)

        # skip if not enough data
        if len(revenue_df) < needed_points:
            continue

        # get data series and calculate MA values
        ma_vals = revenue_df['revenue'].rolling(window=ma_n_months).mean()

        # we only need the last (cont_m_months + 1) MA values
        vals = ma_vals.tail(cont_m_months + 1)

        # skip if not enough data
        if len(vals) < cont_m_months + 1:
            continue

        # skip if any value is missing
        if vals.isna().any():
            continue

        # check strictly increasing (continuous growth)
        # vals is [t-M, t-M+1, ..., t]
        is_increasing = (vals.diff().iloc[1:] > 0).all()

        if is_increasing:
            # calculate score:
            # = growth percentage over the period
            start_val = vals.iloc[0]
            end_val = vals.iloc[-1]

            # score = (end_value - start_val) / start_val * 100
            if start_val == 0:
                # TODO: reconsider this
                score = 0
            else:
                score = (end_val - start_val) / abs(start_val) * 100

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


# R03: N 個月平均(MA)累積營收年增率連續 M 個月成長  (P.S. 年增率遞增)
def list_accum_revenue_yoy_ma_growth(db, ma_n_months=3, cont_m_months=3, input_df=None):
    """Get stocks with consecutive growth in accumulated (YTD) revenue YoY
    moving average

    Find stocks whose N-month moving average of accumulated (YTD) revenue YoY
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

    # to calculate the first N-month MA, we need N data points
    # we need additional M data points of MA to check for consecutive M growth
    # so total data points needed = N + M
    need_points = ma_n_months + cont_m_months

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=need_points)

        # skip if not enough data
        if len(revenue_df) < need_points:
            continue

        # get data series and calculate MA values
        ma_vals = revenue_df['revenue_ytd_yoy'].rolling(window=ma_n_months).mean()

        # we only need the last (cont_m_months + 1) MA values
        vals = ma_vals.tail(cont_m_months + 1)

        # skip if not enough data
        if len(vals) < cont_m_months + 1:
            continue

        # skip if any value is missing
        if vals.isna().any():
            continue

        # check strictly increasing (continuous growth)
        # vals is [t-M, ..., t]
        is_increasing = (vals.diff().iloc[1:] > 0).all()

        if is_increasing:
            # calculate score:
            # = growth percentage over the period
            start_val = vals.iloc[0]
            end_val = vals.iloc[-1]

            # score = (end_value - start_val) / start_val * 100
            if start_val == 0:
                # TODO: reconsider this
                score = 0
            else:
                score = (end_val - start_val) / abs(start_val) * 100

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


# R04: (最新一期) N 個月平均(MA)累積營收年增率成長幅度 > T%  (P.S. 年增率遞增幅度)
def list_accum_revenue_yoy_ma_growth_above(
    db, ma_n_months=3, threshold=0.0, input_df=None
):
    """Get stocks with latest growth rate in accumulated (YTD) revenue YOY
    moving average above threshold

    Find stocks whose latest increasing rate of N-month moving average of
    accumulated (YTD) revenue YOY exceeds the specified threshold.

    Args:
        db (StockDatabase): Database instance
        ma_n_months (int): Moving average window size (e.g. 3, 12)
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
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

    # convert threshold to decimal for comparison
    threshold = threshold / 100

    results = []

    # to calculate the N-month MA, we need N data points
    # need one extra point to calculate previous MA for growth rate comparison
    needed_points = ma_n_months + 1

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=needed_points)

        # skip if not enough data
        if len(revenue_df) < needed_points:
            continue

        # get data series and calculate MA values
        ma_vals = revenue_df['revenue_ytd_yoy'].rolling(window=ma_n_months).mean()

        # we only need the last 2 MA values
        vals = ma_vals.tail(2)

        # skip if not enough data
        if len(vals) < 2:
            continue

        # skip if any value is missing
        if vals.isna().any():
            continue

        prev_val = vals.iloc[0]
        curr_val = vals.iloc[1]

        # calculate growth rate (in decimal)
        if prev_val == 0:
            # TODO: reconsider this
            growth_rate = 0.0
        else:
            growth_rate = (curr_val - prev_val) / abs(prev_val)

        # check growth rate
        if growth_rate > threshold:
            # calculate score:
            # = exceeding amount (decimal to percentage)
            score = (growth_rate - threshold) * 100

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


# F01: (最新一期) N 個月平均(MA)營收創近 M 月新高
def list_revenue_ma_hit_new_high(
    db, ma_n_months=3, lookback_m_months=12, input_df=None
):
    """Get stocks with latest N-month MA revenue reaching a new high

    Find stocks whose latest N-month moving average of revenue
    is the highest among the moving averages in the past M months.

    Args:
        db (StockDatabase): Database instance
        ma_n_months (int): Moving average window size (e.g. 3, 12)
        lookback_m_months (int): Number of months to look back
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    if ma_n_months < 2:
        raise ValueError('ma_n_months must be >= 2')
    if lookback_m_months < 2:
        raise ValueError('lookback_m_months must be >= 2')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # calculate needed points
    # we need M periods of MA, each N-month MA requires N data points
    # to get M consecutive N-month MAs, we need N + M - 1 data points
    needed_points = ma_n_months + lookback_m_months - 1

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=needed_points)

        # skip if not enough data
        if len(revenue_df) < needed_points:
            continue

        # get data series and calculate MA values
        ma_vals = revenue_df['revenue'].rolling(window=ma_n_months).mean()

        # we only need the last 'lookback_m_months' MA values
        vals = ma_vals.tail(lookback_m_months)

        # skip if not enough data
        if len(vals) < lookback_m_months:
            continue

        # skip if any value is missing
        if vals.isna().any():
            continue

        # exclude the newest value to find the max of previous
        early_vals = vals.iloc[:-1]
        recent_val = vals.iloc[-1]  # this is the newest value

        early_max = early_vals.max()

        # skip if invalid values
        # NOTE: normaly this should not happen, we had guranteed enough data
        if pd.isna(early_max) or pd.isna(recent_val):
            continue

        # check if recent val exceeds early max
        if recent_val > early_max:
            # calculate score:
            # = percentage exceeded
            if early_max == 0:
                # TODO: reconsider this
                score = 0
            else:
                score = (recent_val - early_max) / abs(early_max) * 100

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


# F02: (最新一期) N 月平均(MA)營收大於 M 月平均(MA)營收
def list_revenue_ma_greater_than(db, ma_n_months=3, ma_m_months=12, input_df=None):
    """Get stocks with latest N-month average revenue is greater than
    M-month average revenue

    Find stocks whose the latest N-month (moving) average revenue
    is greater than the latest M-month (moving) average revenue.

    Args:
        db (StockDatabase): Database instance
        ma_n_months (int): First moving average window size
        ma_m_months (int): Second moving average window size
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use get_industrial_stocks as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    if ma_n_months < 2:
        raise ValueError('ma_n_months must be >= 2')
    if ma_m_months < 2:
        raise ValueError('ma_m_months must be >= 2')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # calculate needed points
    needed_points = max(ma_n_months, ma_m_months)

    for _, row in target_df.iterrows():
        code = row['code']

        # get recent revenue data
        # NOTE: already sorted by date ascending (old -> new)
        revenue_df = db.get_recent_revenue_by_code(code, limit=needed_points)

        # skip if not enough data
        if len(revenue_df) < needed_points:
            continue

        # get data series
        vals = revenue_df['revenue']

        # we only need the last values to calculate average
        n_vals = vals.tail(ma_n_months)
        m_vals = vals.tail(ma_m_months)

        if len(n_vals) < ma_n_months or len(m_vals) < ma_m_months:
            continue

        # calculate latest N-month average and M-month average
        n_avg = n_vals.mean()
        m_avg = m_vals.mean()

        # skip if invalid values
        # NOTE: normaly this should not happen, we had guranteed enough data
        if pd.isna(n_avg) or pd.isna(m_avg):
            continue

        # check if N-month average > M-month average
        if n_avg > m_avg:
            # calculate score:
            # = percentage exceeded
            if m_avg == 0:
                # TODO: reconsider this
                score = 0
            else:
                score = (n_avg - m_avg) / abs(m_avg) * 100

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
