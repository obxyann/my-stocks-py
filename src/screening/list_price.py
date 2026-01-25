"""Price screening methods"""

import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 近 N 個月股價漲幅 ＞ p%
# ex. 近 6 個月股價漲幅 ＞ 0%
def list_price_growth(db, n_months=3, p_percent=10.0, input_df=None):
    """Filter stocks where price growth over the last N months > p%.

    Growth = (Latest_Price - Price_N_Months_Ago) / Price_N_Months_Ago * 100

    Args:
        db (StockDatabase): Database instance
        n_months (int): Number of months to look back
        p_percent (float): Growth threshold percentage
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # 1. Determine source stocks
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
    
    # Calculate start date with a buffer to ensure we find the date N months ago
    # Buffer +1 month to be safe
    buffer_months = n_months + 2
    start_search_date = datetime.now() - relativedelta(months=buffer_months)
    start_date_str = start_search_date.strftime('%Y-%m-%d')

    for code in stock_codes:
        # Get daily prices
        # We need enough history to find the price N months ago
        df_prices = db.get_prices_by_code(code, start_date=start_date_str)

        if df_prices.empty or len(df_prices) < 2:
            continue

        # Ensure sorted
        # df_prices is already sorted by get_prices_by_code, but to be safe:
        # df_prices = df_prices.sort_values('trade_date') 

        # Latest price
        latest_row = df_prices.iloc[-1]
        latest_price = latest_row['close_price']
        latest_date_str = latest_row['trade_date']
        
        try:
            latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
        except ValueError:
            continue

        # Target date for baseline price
        target_date = latest_date - relativedelta(months=n_months)
        
        # Find the row closest to target_date
        # We prefer a date <= target_date (true N months ago or slightly more), 
        # but if holiday, maybe checks nearby. 
        # Let's find index where date is closest.
        
        df_prices['date_obj'] = pd.to_datetime(df_prices['trade_date'])
        
        # Filter for dates <= target_date
        past_candidates = df_prices[df_prices['date_obj'] <= target_date]
        
        if past_candidates.empty:
            # If no data before target date, maybe the stock is too new
            # or data fetch didn't go back far enough.
            # Try getting the earliest available if it's close enough? 
            # For strict N months growth, if we don't have data N months ago, skip.
            continue
            
        # Take the last one of the candidates (closest to target_date from the left)
        base_row = past_candidates.iloc[-1]
        base_price = base_row['close_price']

        if base_price <= 0:
            continue

        # Calculate growth
        growth = (latest_price - base_price) / base_price * 100

        if growth > p_percent:
            # Score Calculation
            # -----------------------------------------------------------
            # Algorithm: Growth percentage itself is the score factor
            # or Difference from threshold.
            # "超越篩選幅度越高, 越高分" -> (Growth - Threshold) or just Growth.
            # Using Growth value directly correlates with "higher growth = higher score"
            # -----------------------------------------------------------
            score_val = growth

            # Accumulate
            current_score = code_to_score.get(code, 0)
            final_score = current_score + score_val

            results.append({
                'code': code,
                'name': code_to_name.get(code, ''),
                'score': round(final_score, 2)
            })

    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(drop=True)
    return result_df


# 最新股價 ＞ 近 N 個月月均價
# ex. 最新股價 ＞ 近 2 個月月均價
def list_price_above_avg(db, n_months=3, input_df=None):
    """Filter stocks where Latest Price > Average of Monthly Average Prices of last N months.

    Args:
        db (StockDatabase): Database instance
        n_months (int): Number of months to average
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # 1. Determine source stocks
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
    
    # Start date for fetching monthly data
    # We need last N months. 
    # Buffer: N+2 months to ensure we get N records.
    start_search_date = datetime.now() - relativedelta(months=n_months + 2)
    start_date_str = start_search_date.strftime('%Y-%m-%d')

    for code in stock_codes:
        # Get latest price
        # We assume recent data is available
        # Fetching a small window of daily prices for the latest price
        # Using a distinct call or a short window
        last_month_date = datetime.now() - relativedelta(days=30)
        df_daily = db.get_prices_by_code(code, start_date=last_month_date.strftime('%Y-%m-%d'))
        
        if df_daily.empty:
            continue
            
        latest_price = df_daily.iloc[-1]['close_price']
        
        # Get monthly averages
        df_monthly = db.get_monthly_avg_prices_by_code(code, start_date=start_date_str)
        
        if df_monthly.empty:
            continue
            
        # Take last N records
        # Note: df_monthly is sorted by year, month
        # If we have fewer than N records, use what we have? 
        # Usually "Recent N months" implies strict N. 
        # But if the stock is young, maybe N is too large.
        # Let's use up to last N records.
        
        target_months = df_monthly.tail(n_months)
        
        if target_months.empty:
            continue
            
        avg_price = target_months['price'].mean()
        
        if avg_price <= 0 or pd.isna(avg_price):
            continue
            
        if latest_price > avg_price:
            # Score Calculation
            # -----------------------------------------------------------
            # Algorithm: Percentage difference above average
            # Score = (Latest - Avg) / Avg * 100
            # -----------------------------------------------------------
            diff_percent = (latest_price - avg_price) / avg_price * 100
            
            # Accumulate
            current_score = code_to_score.get(code, 0)
            final_score = current_score + diff_percent
            
            results.append({
                'code': code,
                'name': code_to_name.get(code, ''),
                'score': round(final_score, 2)
            })

    result_df = pd.DataFrame(results, columns=['code', 'name', 'score'])
    result_df = result_df.sort_values(by='score', ascending=False).reset_index(drop=True)
    return result_df
