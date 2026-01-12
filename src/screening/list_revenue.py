"""Revenue screening methods"""

import pandas as pd


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
