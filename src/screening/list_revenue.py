"""Revenue screening methods"""

import pandas as pd


# Helper to setup input stocks
def _get_target_stocks(db, input_df):
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


# 近 N 個月營收創近 M 月新高
def list_revenue_hit_new_high(db, recent_months=3, lookback_months=12, input_df=None):
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
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

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


# N 個月平均營收連續 M 個月成長
def list_avg_revenue_cont_growth(db, ma_type, m_months=3, input_df=None):
    """Filter stocks with continuous growth in average revenue (MA) for N months.

    Args:
        db (StockDatabase): Database instance
        ma_type (int): Moving average window size (e.g. 3, 6, 12)
        m_months (int): Number of continuous months of growth required
        input_df (pd.DataFrame): Optional input list of stocks with columns ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores.
            If None, use get_industrial_stocks as default.

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # 2. Determine source stocks
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # Determine limit and strategy based on ma_type
    if ma_type in (3, 12):
        # Use pre-calculated columns
        use_precalc = True
        col_name = f'revenue_ma{ma_type}'
        # To check continuous growth for N months (N intervals), we need N+1 data points.
        limit = m_months + 1
    else:
        # Calculate MA on the fly
        use_precalc = False
        col_name = None
        # We need N+1 data points of MA.
        # To calculate the first (oldest) MA point of window W, we need W prior revenue points.
        # So total revenue rows needed = (N + 1) + (ma_type - 1) = n_months + ma_type
        limit = m_months + ma_type

    for code in stock_codes:
        # 3. Data source from db
        # get_recent_revenue_by_code returns sorted by date ascending (old -> new)
        df_rev = db.get_recent_revenue_by_code(code, limit=limit)

        if len(df_rev) < limit:
            continue

        # Extract target MA values
        if use_precalc:
            vals = df_rev[col_name].tolist()
        else:
            # Calculate MA on the fly
            # df_rev is sorted ascending by date
            ma_series = df_rev['revenue'].rolling(window=ma_type).mean()
            # We only need the last (n_months + 1) valid MA values
            # The first (ma_type - 1) values will be NaN, which is expected
            vals = ma_series.tail(m_months + 1).tolist()

        # Check for valid data
        if len(vals) < m_months + 1 or any(v is None or pd.isna(v) for v in vals):
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


# 營收月增率(revenue_mom)連續 N 個月 ＞ P%
def list_revenue_mom_cont_above(db, n_months=3, threshold=0.0, input_df=None):
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
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

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


# 營收年增率(revenue_yoy)連續 N 個月 ＞ P%
def list_revenue_yoy_cont_above(db, n_months=3, threshold=0.0, input_df=None):
    """Filter stocks with consecutive YoY growth > P% for N months.

    Args:
        db (StockDatabase): Database instance
        n_months (int): Number of consecutive months
        threshold (float): Growth threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

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


# 近 N 個月累積營收年增率(revenue_ytd_yoy)連續 M 個月成長
def list_accum_revenue_yoy_cont_growth(
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
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # We need M steps of comparison: T vs T-1, ..., T-M+1 vs T-M
    # So we need data points T, T-1, ..., T-M (Total M+1 points of AccumYoY)
    limit = m_months_cont + 1

    for code in stock_codes:
        df_rev = db.get_recent_revenue_by_code(code, limit=limit)

        # Ensure filtered by date ascending just in case, though get_recent usually returns sorted
        df_rev = df_rev.sort_values(by=['year', 'month'], ascending=True).reset_index(
            drop=True
        )

        if len(df_rev) < limit:
            continue

        accum_yoy = df_rev['revenue_ytd_yoy']

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


# 近 N 個月累積營收年增率(revenue_ytd_yoy)成長幅度 > P%
def list_accum_revenue_yoy_growth_above(db, n_months=3, threshold=0.0, input_df=None):
    """Filter stocks where N-month Accumulated Revenue YoY Rate > threshold.

    Args:
        db (StockDatabase): Database instance
        n_months (int): Number of months to accumulate (N)
        threshold (float): Threshold percentage (P)
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for code in stock_codes:
        limit = 1
        df_rev = db.get_recent_revenue_by_code(code, limit=limit)

        if df_rev.empty:
            continue

        accum_yoy = df_rev['revenue_ytd_yoy'].iloc[-1]

        if pd.isna(accum_yoy):
            continue

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
