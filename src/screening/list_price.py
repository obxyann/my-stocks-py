"""Price screening methods"""

from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta

from screening.helper import get_target_stocks


# R05: 近 N 個月股價漲幅 > T%
def list_price_growth_above(db, recent_n_months=3, threshold=10.0, input_df=None):
    """Get stocks with recent price growth rate above threshold

    Find stocks whose price growth rate exceeds the specified
    threshold in the last N months.

    Args:
        db (StockDatabase): Database instance
        recent_n_months (int): Number of recent months to check
        threshold (float): Threshold percentage (e.g. 5.0 for 5%)
        input_df (pd.DataFrame, optional): Input list of stocks with columns
            ['code', 'name', 'score']
            If provided, filter only stocks in this list and accumulate scores
            If None, use stocks from list_industrial() as default

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if recent_n_months < 1:
        raise ValueError('recent_n_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # because we don't know the exact latest date of price in database
    # estimate a start date to ensure we find the date N months ago
    # + 2 months to be safe
    need_months = recent_n_months + 2

    start_date = datetime.now() - relativedelta(months=need_months)
    start_date_str = start_date.strftime('%Y-%m-%d')

    for _, row in target_df.iterrows():
        code = row['code']

        # get daily prices
        # NOTE: ensure sorted by date ascending (old -> new)
        df_prices = db.get_prices_by_code(code, start_date=start_date_str)

        # skip if not enough data
        if len(df_prices) < 2:
            continue

        # latest price and date
        latest_row = df_prices.iloc[-1]

        latest_price = latest_row['close_price']
        latest_date_str = latest_row['trade_date']

        try:
            latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
        except ValueError:
            continue

        # target date for baseline price
        target_date = latest_date - relativedelta(months=recent_n_months)

        # find the row closest to target_date
        # we prefer a date <= target_date (true N months ago or slightly more),
        # but if holiday, maybe checks nearby
        # let's find index where date is closest

        df_prices['date_obj'] = pd.to_datetime(df_prices['trade_date'])

        # filter for dates <= target_date
        past_candidates = df_prices[df_prices['date_obj'] <= target_date]

        if past_candidates.empty:
            # if no data before target date, maybe the stock is too new
            # or data fetch didn't go back far enough
            # try getting the earliest available if it's close enough?
            # for strict N months growth, if we don't have data N months ago, skip
            continue

        # take the last one of the candidates (closest to target_date from the left)
        base_row = past_candidates.iloc[-1]
        base_price = base_row['close_price']

        if base_price <= 0:
            continue

        # calculate growth
        growth = (latest_price - base_price) / base_price * 100

        if growth > threshold:
            # calculate score:
            # = growth percentage itself
            score = growth

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


# R06: 最新股價 > 近 N 個月月均價
def list_price_above_avg(db, recent_n_months=1, input_df=None):
    """Get stocks with latest price above recent average price

    Find stocks whose latest price is greater than the average price of
    the last N months.

    Args:
        db (StockDatabase): Database instance
        recent_n_months (int): Number of recent months to average
        input_df (pd.DataFrame): Optional input list of stocks

    Returns:
        pd.DataFrame: Sorted DataFrame with columns ['code', 'name', 'score']
    """
    # check input parameters
    if recent_n_months < 1:
        raise ValueError('recent_n_months must be >= 1')

    # determine source stocks
    target_df = get_target_stocks(db, input_df)
    if target_df.empty:
        return pd.DataFrame(columns=['code', 'name', 'score'])

    results = []

    # because we don't know the exact latest date of price in database
    # estimate a start date to ensure we find the date N months ago
    # + 2 months to be safe
    need_months = recent_n_months + 2

    start_date = datetime.now() - relativedelta(months=need_months)
    start_date_str = start_date.strftime('%Y-%m-%d')

    for _, row in target_df.iterrows():
        code = row['code']

        # get latest price
        # by fetching a small window of daily prices for the latest price
        # NOTE: ensure sorted by date ascending (old -> new)
        last_month_date = datetime.now() - relativedelta(days=30)

        df_daily = db.get_prices_by_code(
            code, start_date=last_month_date.strftime('%Y-%m-%d')
        )

        if df_daily.empty:
            continue

        latest_price = df_daily.iloc[-1]['close_price']

        # get monthly averages
        # NOTE: ensure sorted by date ascending (old -> new)
        df_monthly = db.get_monthly_avg_prices_by_code(code, start_date=start_date_str)

        if df_monthly.empty:
            continue

        # take last N records
        # Note: df_monthly is sorted by year, month
        # if we have fewer than N records, use what we have?
        # usually "recent N months" implies strict N
        # But if the stock is young, maybe N is too large
        # Let's use up to last N records

        target_months = df_monthly.tail(recent_n_months)

        if target_months.empty:
            continue

        avg_price = target_months['price'].mean()

        if pd.isna(avg_price) or avg_price <= 0:
            continue

        if latest_price > avg_price:
            # calculate score
            # = percentage above average
            diff_percent = (latest_price - avg_price) / avg_price * 100

            # accumulate existing score
            final_score = row['score'] + diff_percent

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
