"""Financial metrics screening methods"""

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


# 近 N 季營業利益率(opr_margin)最小/最大 ＞ P%
def list_opr_margin_min_max_ratio_above(db, n_quarters=4, threshold=0.0, input_df=None):
    """Filter stocks where (Min Opr Margin / Max Opr Margin) in last N quarters > P%.

    This metric is often used to assess the stability of the operating margin.
    A ratio close to 100% indicates very stable margins.

    Args:
        db (StockDatabase): Database instance
        n_quarters (int): Number of recent quarters to check
        threshold (float): Threshold percentage (e.g. 50.0 for 50%)
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for code in stock_codes:
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=n_quarters)

        if len(df_metrics) < n_quarters:
            continue

        opr_margins = df_metrics['opr_margin'].tolist()

        # check valid data (filter out None)
        valid_margins = [m for m in opr_margins if m is not None]
        # if not enough data points (e.g. need at least 1, usually N), though len check above covers it mostly
        if not valid_margins:
            continue

        # opr_margin is ratio (0.15), convert to percentage (15.0)
        valid_margins_pct = [m * 100 for m in valid_margins]

        val_min = min(valid_margins_pct)
        val_max = max(valid_margins_pct)

        # Skip if max is not positive (cannot divide or implies all negative/zero)
        if val_max <= 0:
            continue

        # Calculate ratio in percentage
        # e.g. min=10, max=20 -> 50%
        ratio = (val_min / val_max) * 100

        if ratio > threshold:
            # Score: Exceeding amount
            score_val = ratio - threshold

            # accumulate
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


# 近 N 季營業利益率(opr_margin)為近 M 季最大
def list_opr_margin_recent_is_max(db, n_quarters=1, m_lookback=4, input_df=None):
    """Filter stocks where opr_margin in recent N quarters contains the Max of recent M quarters.

    Args:
        db (StockDatabase): Database instance
        n_quarters (int): Number of recent quarters to consider as 'recent'
        m_lookback (int): Total number of quarters to look back (M >= N)
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    limit = max(n_quarters, m_lookback)

    for code in stock_codes:
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=limit)

        if len(df_metrics) < limit:
            continue

        opr_margins = df_metrics['opr_margin'].tolist()  # Sorted old -> new

        # valid data check
        if any(m is None for m in opr_margins):
            continue

        # Split: [.... rest .... | ... recent N ...]
        recent_vals = opr_margins[-n_quarters:]
        # full_vals includes recent_vals
        full_vals = opr_margins

        max_all = max(full_vals)
        max_recent = max(recent_vals)

        # Condition: recent max is the all-time max (of this window)
        if max_recent >= max_all:
            # Score: How much it exceeds the 'non-recent' max?
            # If non-recent part exists:
            others = full_vals[:-n_quarters]
            if others:
                max_others = max(others)
                if max_others == 0:
                    # avoided div by zero
                    if max_recent > 0:
                        score_val = 100  # arbitrary high score
                    else:
                        score_val = 0
                else:
                    # Percentage excess over previous high
                    score_val = (max_recent - max_others) / abs(max_others) * 100
            else:
                # If N=M, checking against itself?
                score_val = 0

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


# 近 N 季營業利益率年增率(opr_margin_yoy)連續 M 季成長
def list_opr_margin_yoy_cont_growth(db, n_quarters=4, m_quarters=3, input_df=None):
    """Filter stocks where opr_margin_yoy has grown continuously for M quarters within the recent N quarters window.

    Actually interpreting: The recent trend (ending at latest) shows M quarters of continuous growth in opr_margin_yoy.

    Args:
        db (StockDatabase): Database instance
        n_quarters (int): (Unused/Redundant in strict interpretation) Window size
        m_quarters (int): Consecutive quarters of growth required
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # To check M quarters growth we need M+1 data points: T > T-1 > ... > T-M
    limit = m_quarters + 1

    for code in stock_codes:
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=limit)

        if len(df_metrics) < limit:
            continue

        vals = df_metrics['opr_margin_yoy'].tolist()

        if any(v is None for v in vals):
            continue

        # Check strictly increasing
        is_increasing = True
        for i in range(len(vals) - 1):
            if vals[i + 1] <= vals[i]:
                is_increasing = False
                break

        if is_increasing:
            # Score: Total increase (Magnitude)
            score_val = vals[-1] - vals[0]

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


# 近 N 季營業利益率季增率(opr_margin_qoq)連續 M 季成長
def list_opr_margin_qoq_cont_growth(db, n_quarters=4, m_quarters=3, input_df=None):
    """Filter stocks where opr_margin_qoq has grown continuously for M quarters.

    Args:
        db (StockDatabase): Database instance
        n_quarters (int): (Unused)
        m_quarters (int): Consecutive quarters of growth required
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []
    limit = m_quarters + 1

    for code in stock_codes:
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=limit)

        if len(df_metrics) < limit:
            continue

        vals = df_metrics['opr_margin_qoq'].tolist()

        if any(v is None for v in vals):
            continue

        # Check strictly increasing
        is_increasing = True
        for i in range(len(vals) - 1):
            if vals[i + 1] <= vals[i]:
                is_increasing = False
                break

        if is_increasing:
            # Score: Total increase
            score_val = vals[-1] - vals[0]

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


# 近 N 季稅後純益率(net_margin)平均 ＞ P%
def list_net_margin_avg_above(db, n_quarters=4, threshold=0.0, input_df=None):
    """Filter stocks where Average Net Margin in last N quarters > P%.

    Args:
        db (StockDatabase): Database instance
        n_quarters (int): Number of quarters
        threshold (float): Threshold percentage
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for code in stock_codes:
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=n_quarters)

        if len(df_metrics) < n_quarters:
            continue

        vals = df_metrics['net_margin'].tolist()

        # Filter None
        vals = [v for v in vals if v is not None]
        if not vals:
            continue

        # Convert to percentage
        vals_pct = [v * 100 for v in vals]

        avg_val = sum(vals_pct) / len(vals_pct)

        if avg_val > threshold:
            score_val = avg_val - threshold

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


# 近 N 季營業利益率(opr_margin)最少 ＞ P%
def list_opr_margin_min_above(db, n_quarters=4, threshold=0.0, input_df=None):
    """Filter stocks where Minimum Operating Margin in last N quarters > P%.

    Args:
        db (StockDatabase): Database instance
        n_quarters (int): Number of quarters
        threshold (float): Threshold percentage
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    stock_codes, code_to_name, code_to_score = _get_target_stocks(db, input_df)
    if not stock_codes:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    for code in stock_codes:
        df_metrics = db.get_recent_financial_metrics_by_code(code, limit=n_quarters)

        if len(df_metrics) < n_quarters:
            continue

        opr_margins = df_metrics['opr_margin'].tolist()

        # check valid data (filter out None)
        valid_margins = [m for m in opr_margins if m is not None]
        if not valid_margins:
            continue

        # opr_margin is ratio (0.15), convert to percentage (15.0)
        valid_margins_pct = [m * 100 for m in valid_margins]

        val_min = min(valid_margins_pct)

        if val_min > threshold:
            # Score: Exceeding amount
            score_val = val_min - threshold

            # accumulate
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
