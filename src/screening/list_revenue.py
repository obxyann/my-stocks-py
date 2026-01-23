"""Revenue screening methods"""

import pandas as pd


# 近 N 個月營收創近 M 月新高
# ex. 近 2 個月營收創近 1 年新高
def list_revenue_new_high(db, recent_months=3, lookback_months=12, input_df=None):
    """Get stocks whose recent revenue hit a new high

    Find stocks where the maximum revenue in the last N months exceeds
    the maximum revenue in the preceding M months.

    Args:
        db (StockDatabase): Database instance
        recent_months (int): Number of recent months to check (N)
        lookback_months (int): Number of preceding months to compare against (M)
        input_df (pd.DataFrame): Optional input DataFrame with columns ('code', 'name', 'score')
            If provided, filter only stocks in this list and accumulate scores.
            If None, use get_industrial_stocks as default.

    Returns:
        pd.DataFrame: DataFrame with columns ('code', 'name', 'score')
            score is the percentage by which recent high exceeds previous high
    """
    # determine source stocks
    if input_df is not None and not input_df.empty:
        # use input_df as source
        code_to_name = dict(zip(input_df['code'], input_df['name']))
        code_to_score = dict(zip(input_df['code'], input_df['score']))

        stock_codes = input_df['code'].tolist()
    else:
        # get all industrial stocks as default
        stocks_df = db.get_industrial_stocks()

        if stocks_df.empty:
            return pd.DataFrame(columns=['code', 'name', 'score'])

        code_to_name = dict(zip(stocks_df['code'], stocks_df['name']))
        code_to_score = {}

        stock_codes = stocks_df['code'].tolist()

    # total months needed
    total_months = recent_months + lookback_months

    results = []

    for code in stock_codes:
        # get recent revenue data
        revenue_df = db.get_recent_revenue_by_code(code, limit=total_months)

        # skip if not enough data
        if len(revenue_df) < total_months:
            continue

        # ensure sorted by date ascending
        revenue_df = revenue_df.sort_values(
            by=['year', 'month'], ascending=True
        ).reset_index(drop=True)

        # split into lookback period and recent period
        lookback_df = revenue_df.iloc[:lookback_months]
        recent_df = revenue_df.iloc[lookback_months:]

        # get max revenue in each period
        lookback_max = lookback_df['revenue'].max()
        recent_max = recent_df['revenue'].max()

        # skip if lookback period has no valid revenue
        if pd.isna(lookback_max) or lookback_max <= 0:
            continue

        # check if recent max exceeds lookback max
        if recent_max > lookback_max:
            # calculate score: percentage exceeded
            new_score = (recent_max - lookback_max) / lookback_max * 100
            # accumulate existing score from input_df
            existing_score = code_to_score.get(code, 0)
            total_score = existing_score + new_score
            results.append(
                {
                    'code': code,
                    'name': code_to_name.get(code, ''),
                    'score': round(total_score, 2),
                }
            )

    # create result DataFrame and sort by score descending
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df


# 3/12 個月平均營收連續 N 個月成長
# ex. 12 個月平均營收連續 2 個月成長
def list_revenue_continuous_growth(db, ma_type, n_months=3, input_df=None):
    """Filter stocks with continuous growth in MA3 or MA12 revenue for N months.

    Args:
        db (StockDatabase): Database instance
        ma_type (int): 3 or 12, indicating MA3 or MA12
        n_months (int): Number of continuous months of growth required
        input_df (pd.DataFrame): Optional input list of stocks with columns ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores.
            If None, use get_industrial_stocks as default.

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # 1. Validation for ma_type (3 or 12)
    if ma_type not in (3, 12):
        print(f'Warning: Invalid ma_type {ma_type}. Must be 3 or 12.')
        return pd.DataFrame(columns=['code', 'name', 'score'])

    col_name = f'revenue_ma{ma_type}'

    # 2. Determine source stocks
    if input_df is not None and not input_df.empty:
        stock_codes = input_df['code'].tolist()
        code_to_name = dict(zip(input_df['code'], input_df['name']))
        code_to_score = dict(zip(input_df['code'], input_df['score']))
    else:
        stocks_df = db.get_industrial_stocks()
        if stocks_df.empty:
            return pd.DataFrame(columns=['code', 'name', 'score'])

        stock_codes = stocks_df['code'].tolist()
        code_to_name = dict(zip(stocks_df['code'], stocks_df['name']))
        code_to_score = {}

    results = []
    # To check continuous growth for N months (N intervals), we need N+1 data points.
    # e.g. M1 < M2 < M3 (2 months growth) needs 3 points.
    # N months growth -> N comparison steps -> N+1 points.
    limit = n_months + 1

    for code in stock_codes:
        # 3. Data source from db
        # get_recent_revenue_by_code returns sorted by date ascending (old -> new)
        df_rev = db.get_recent_revenue_by_code(code, limit=limit)

        if len(df_rev) < limit:
            continue

        # Extract target MA values
        vals = df_rev[col_name].tolist()

        # Check for valid data
        if any(v is None or pd.isna(v) for v in vals):
            continue

        # Check strictly increasing (Continuous Growth)
        # vals is [t-N, t-N+1, ..., t]
        is_increasing = True
        for i in range(len(vals) - 1):
            if vals[i + 1] <= vals[i]:
                is_increasing = False
                break

        if is_increasing:
            # 4. Score calculation
            # -----------------------------------------------------------
            # Algorithm: Total percentage growth over the N months
            # Score = (Last_Value - First_Value) / First_Value * 100
            # NOTE: can be adjusted here
            # -----------------------------------------------------------
            start_val = vals[0]
            end_val = vals[-1]

            if start_val == 0:
                score = 0
            else:
                score = (end_val - start_val) / abs(start_val) * 100

            # 5. Accumulate score
            current_score = code_to_score.get(code, 0)
            final_score = current_score + score

            results.append(
                {
                    'code': code,
                    'name': code_to_name.get(code, ''),
                    'score': round(final_score, 2),
                }
            )

    # 6. Sort by score
    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )

    return result_df


# 營收月增率連續 N 個月 ＞ P%
# ex. 營收月增率連續 2 個月 ＞ 0%
def list_revenue_mom_growth(db, n_months=3, threshold=0.0, input_df=None):
    """Filter stocks with consecutive MoM growth > P% for N months.

    Args:
        db (StockDatabase): Database instance
        n_months (int): Number of consecutive months
        threshold (float): Growth threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # Determine source stocks
    if input_df is not None and not input_df.empty:
        stock_codes = input_df['code'].tolist()
        code_to_name = dict(zip(input_df['code'], input_df['name']))
        code_to_score = dict(zip(input_df['code'], input_df['score']))
    else:
        stocks_df = db.get_industrial_stocks()
        if stocks_df.empty:
            return pd.DataFrame(columns=['code', 'name', 'score'])
        stock_codes = stocks_df['code'].tolist()
        code_to_name = dict(zip(stocks_df['code'], stocks_df['name']))
        code_to_score = {}

    results = []

    for code in stock_codes:
        df_rev = db.get_recent_revenue_by_code(code, limit=n_months)

        if len(df_rev) < n_months:
            continue

        moms = df_rev['revenue_mom'].tolist()

        # Check if all MoM > threshold
        if any(pd.isna(m) or m <= threshold for m in moms):
            continue

        # Score Calculation
        # Algorithm: Sum of excess growth over threshold
        # Score = Sum(MoM_i - Threshold)
        score_val = sum(m - threshold for m in moms)

        current_score = code_to_score.get(code, 0)
        final_score = current_score + score_val

        results.append(
            {
                'code': code,
                'name': code_to_name.get(code, ''),
                'score': round(final_score, 2),
            }
        )

    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )
    return result_df


# 營收年增率連續 N 個月 ＞ P%
# ex. 營收年增率連續 1 個月 ＞ 40%
def list_revenue_yoy_growth(db, n_months=3, threshold=0.0, input_df=None):
    """Filter stocks with consecutive YoY growth > P% for N months.

    Args:
        db (StockDatabase): Database instance
        n_months (int): Number of consecutive months
        threshold (float): Growth threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    if input_df is not None and not input_df.empty:
        stock_codes = input_df['code'].tolist()
        code_to_name = dict(zip(input_df['code'], input_df['name']))
        code_to_score = dict(zip(input_df['code'], input_df['score']))
    else:
        stocks_df = db.get_industrial_stocks()
        if stocks_df.empty:
            return pd.DataFrame(columns=['code', 'name', 'score'])
        stock_codes = stocks_df['code'].tolist()
        code_to_name = dict(zip(stocks_df['code'], stocks_df['name']))
        code_to_score = {}

    results = []

    for code in stock_codes:
        df_rev = db.get_recent_revenue_by_code(code, limit=n_months)

        if len(df_rev) < n_months:
            continue

        yoys = df_rev['revenue_yoy'].tolist()

        # Check if all YoY > threshold
        if any(pd.isna(y) or y <= threshold for y in yoys):
            continue

        # Score Calculation
        # Algorithm: Sum of excess growth over threshold
        # Score = Sum(YoY_i - Threshold)
        score_val = sum(y - threshold for y in yoys)

        current_score = code_to_score.get(code, 0)
        final_score = current_score + score_val

        results.append(
            {
                'code': code,
                'name': code_to_name.get(code, ''),
                'score': round(final_score, 2),
            }
        )

    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )
    return result_df


# N 個月累積營收年增率連續 M 個月成長
# ex. 3 個月累積營收年增率連續 1 個月成長
def list_revenue_accumulated_growth(
    db, n_months_accum=3, m_months_cont=3, input_df=None
):
    """Filter stocks where N-month Accumulated Revenue YoY Rate has been growing for M consecutive months.

    Condition: AccumYoY(t) > AccumYoY(t-1) for M consecutive steps.

    Args:
        db (StockDatabase): Database instance
        n_months_accum (int): N months for accumulated revenue (e.g. 3 for Qaccum)
        m_months_cont (int): M months of consecutive growth of the rate
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    if input_df is not None and not input_df.empty:
        stock_codes = input_df['code'].tolist()
        code_to_name = dict(zip(input_df['code'], input_df['name']))
        code_to_score = dict(zip(input_df['code'], input_df['score']))
    else:
        stocks_df = db.get_industrial_stocks()
        if stocks_df.empty:
            return pd.DataFrame(columns=['code', 'name', 'score'])
        stock_codes = stocks_df['code'].tolist()
        code_to_name = dict(zip(stocks_df['code'], stocks_df['name']))
        code_to_score = {}

    results = []

    # We need M steps of comparison: T vs T-1, ..., T-M+1 vs T-M
    # So we need data points T, T-1, ..., T-M (Total M+1 points of AccumYoY)
    # Each AccumYoY point needs N months of revenue.
    # So we need rows from index T down to T - M - N + 1.
    # Total rows = n_months_accum + m_months_cont
    limit = n_months_accum + m_months_cont

    for code in stock_codes:
        df_rev = db.get_recent_revenue_by_code(code, limit=limit)

        # Ensure filtered by date ascending just in case, though get_recent usually returns sorted
        df_rev = df_rev.sort_values(by=['year', 'month'], ascending=True).reset_index(
            drop=True
        )

        if len(df_rev) < limit:
            continue

        # Calculate N-month rolling sum for Revenue and Revenue_LY
        # Since we need exactly M+1 points of Accumulated YoY at the END of the series
        # Window size = n_months_accum

        # Vectorized rolling calculation
        # Note: 'min_periods=n_months_accum' ensures we only get valid sums where we have full data
        rolling_rev = df_rev['revenue'].rolling(window=n_months_accum).sum()
        rolling_rev_ly = df_rev['revenue_ly'].rolling(window=n_months_accum).sum()

        # Calculate YoY of the accumulated revenue
        # Handle division by zero or NaN
        accum_yoy = (rolling_rev - rolling_rev_ly) / rolling_rev_ly * 100

        # The rolling result will have NaNs for the first N-1 rows
        # We only care about the last m_months_cont + 1 values
        # slice: last (m_months_cont + 1)
        target_yoy = accum_yoy.tail(m_months_cont + 1).tolist()

        if len(target_yoy) < m_months_cont + 1:
            continue

        if any(pd.isna(v) for v in target_yoy):
            continue

        # Check strictly increasing: V[i+1] > V[i]
        is_increasing = True
        for i in range(len(target_yoy) - 1):
            if target_yoy[i + 1] <= target_yoy[i]:
                is_increasing = False
                break

        if is_increasing:
            # Score Calculation
            # Algorithm: Total increase in the Accum YoY Growth Rate over the period
            # Score = Last_Accum_YoY - First_Accum_YoY (of the checking period)
            score_val = target_yoy[-1] - target_yoy[0]

            # If negative (techically possible if all negative but increasing? -10 -> -5),
            # it still represents improvement/growth magnitude.

            current_score = code_to_score.get(code, 0)
            final_score = current_score + score_val

            results.append(
                {
                    'code': code,
                    'name': code_to_name.get(code, ''),
                    # 'debug_yoy': target_yoy,
                    'score': round(final_score, 2),
                }
            )

    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )
    return result_df


# N 個月累積營收年增率成長幅度 > p%
# ex. 12 個月累積營收年增率成長幅度 ＞ 2%
def list_revenue_accumulated_growth_exceeds(
    db, n_months=3, threshold=0.0, input_df=None
):
    """Filter stocks where N-month Accumulated Revenue YoY Rate > threshold.

    Args:
        db (StockDatabase): Database instance
        n_months (int): Number of months to accumulate (N)
        threshold (float): Threshold percentage (P)
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    if input_df is not None and not input_df.empty:
        stock_codes = input_df['code'].tolist()
        code_to_name = dict(zip(input_df['code'], input_df['name']))
        code_to_score = dict(zip(input_df['code'], input_df['score']))
    else:
        stocks_df = db.get_industrial_stocks()
        if stocks_df.empty:
            return pd.DataFrame(columns=['code', 'name', 'score'])
        stock_codes = stocks_df['code'].tolist()
        code_to_name = dict(zip(stocks_df['code'], stocks_df['name']))
        code_to_score = {}

    results = []

    for code in stock_codes:
        limit = n_months
        df_rev = db.get_recent_revenue_by_code(code, limit=limit)

        if len(df_rev) < limit:
            continue

        # Calculate N-month sum for Revenue and Revenue_LY
        sum_rev = df_rev['revenue'].sum()
        sum_rev_ly = df_rev['revenue_ly'].sum()

        if sum_rev_ly <= 0 or pd.isna(sum_rev_ly):
            continue

        accum_yoy = (sum_rev - sum_rev_ly) / sum_rev_ly * 100

        if accum_yoy > threshold:
            # Score Calculation
            # -----------------------------------------------------------
            # Algorithm: Difference between Accumulated YoY and Threshold
            # Score = Accum_YoY - Threshold
            # -----------------------------------------------------------
            score_val = accum_yoy - threshold

            current_score = code_to_score.get(code, 0)
            final_score = current_score + score_val

            results.append(
                {
                    'code': code,
                    'name': code_to_name.get(code, ''),
                    'score': round(final_score, 2),
                }
            )

    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(
        drop=True
    )
    return result_df
