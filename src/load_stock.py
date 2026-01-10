"""Load stock data module

This module provides API for loading stock data from database and
transforming it to the format suitable for UI display
"""

from datetime import datetime

import pandas as pd


def load_stock(stock_code, db):
    """Load stock data from database

    Args:
        stock_code (str): Stock code
        db (StockDatabase): Database instance

    Returns:
        dict: Dictionary containing metadata and DataFrames
            - 'code_name': Stock code and name string
            - 'revenue': Revenue data
            - 'financial': Financial data
            - 'metrics': Financial metrics data
    """
    # retrieve stock info
    df_s = db.get_stock_by_code(stock_code)

    code_name = f'{stock_code}'

    if not df_s.empty:
        name = df_s.iloc[0]['name']
        code_name = f'{stock_code} {name}'

    # calculate start date for the last 48 months (inclusive)
    start_date = (datetime.now().replace(day=1) - pd.DateOffset(months=47)).strftime(
        '%Y-%m-%d'
    )

    # retrieve data from database
    df_o = db.get_prices_by_code(stock_code, start_date=start_date)
    df_a = db.get_monthly_avg_prices_by_code(stock_code, start_date=start_date)
    df_r = db.get_revenue_by_code(stock_code, start_date=start_date)
    df_f = db.get_recent_financial_by_code(stock_code, limit=8)
    df_m = db.get_recent_financial_metrics_by_code(stock_code, limit=8)

    # transform data
    tbl_o = transform_ohlc_price(df_o)
    tbl_a = transform_monthly_avg_price(df_a)
    tbl_r = transform_monthly_revenue(df_r)
    tbl_f = transform_financial(df_f)
    tbl_m = transform_financial_metrics(df_m)

    return {
        'code_name': code_name,
        'ohlc_price': tbl_o,
        'avg_price': tbl_a,
        'revenue': tbl_r,
        'financial': tbl_f,
        'metrics': tbl_m,
    }


def transform_ohlc_price(df):
    """Transform OHLC price data for mplfinance

    Source format: columns [code, trade_date, open_price, high_price, ...]
    Target format: columns [Open, High, Low, Close, Volume]

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: Transformed DataFrame with DatetimeIndex
    """
    if df.empty:
        return pd.DataFrame()

    # rename columns to match mplfinance requirements
    result = df.rename(
        columns={
            'trade_date': 'Date',
            'open_price': 'Open',
            'high_price': 'High',
            'low_price': 'Low',
            'close_price': 'Close',
            'volume': 'Volume',
        }
    )

    # convert to datetime
    result['Date'] = pd.to_datetime(result['Date'])

    # set Date as index
    result = result.set_index('Date')

    return result


def transform_monthly_avg_price(df):
    """Transform monthly avg price data to UI format

    Source format: columns [code, year, month, price, volume]
    Target format: columns [year_month, price, volume]

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: Transformed DataFrame for UI display
    """
    if df.empty:
        return pd.DataFrame(columns=['year_month', 'price', 'volume'])

    # create year_month column
    result = pd.DataFrame()
    result['year_month'] = (
        df['year'].astype(str) + '/' + df['month'].astype(str).str.zfill(2)
    )

    # map columns and format values
    result['price'] = df['price']  # .apply(format_value)
    result['volume'] = df['volume']  # .apply(format_number)

    # sort by year_month descending (latest first)
    result = result.iloc[::-1].reset_index(drop=True)

    return result


def transform_monthly_revenue(df):
    """Transform monthly revenue data to UI format

    Source format: columns [code, year, month, revenue, ...]
    Target format: columns [year_month, revence, revence_mom, revence_ly, revence_yoy, revence_ytd, revence_ytd_yoy]

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: Transformed DataFrame for UI display
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                'year_month',
                'revence',
                'revence_mom',
                'revence_ly',
                'revence_yoy',
                'revence_ytd',
                'revence_ytd_yoy',
                'revenue_ma3',
                'revenue_ma12',
                'revenue_ytd_yoy_ma3',
                'revenue_ytd_yoy_ma12',
            ]
        )

    # create year_month column
    result = pd.DataFrame()
    result['year_month'] = (
        df['year'].astype(str) + '/' + df['month'].astype(str).str.zfill(2)
    )

    # map columns and format values
    result['revence'] = df['revenue']  # .apply(format_number)
    result['revence_mom'] = df['revenue_mom'].apply(format_100)
    result['revence_ly'] = df['revenue_ly']  # .apply(format_number)
    result['revence_yoy'] = df['revenue_yoy'].apply(format_100)
    result['revence_ytd'] = df['revenue_ytd']  # .apply(format_number)
    result['revence_ytd_yoy'] = df['revenue_ytd_yoy'].apply(format_100)
    result['revenue_ma3'] = df['revenue_ma3']  # .apply(format_number)
    result['revenue_ma12'] = df['revenue_ma12']  # .apply(format_number)
    result['revenue_ytd_yoy_ma3'] = df['revenue_ytd_yoy_ma3']  # .apply(format_number)
    result['revenue_ytd_yoy_ma12'] = df['revenue_ytd_yoy_ma12']  # .apply(format_number)

    # sort by year_month descending (latest first)
    result = result.iloc[::-1].reset_index(drop=True)

    return result


def transform_financial(df):
    """Transform financial data to UI format (pivot)

    Source format: columns [code, year, quarter, opr_revenue, opr_costs, ...]
    Target format: columns [Item, 2025.Q3, 2025.Q2, ...] (pivoted, items as rows)

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: Transformed DataFrame for UI display
    """
    if df.empty:
        return pd.DataFrame(columns=['Item'])

    # define items to display (column_name, display_name)
    items = [
        ('opr_revenue', '營業收入'),
        ('opr_costs', '營業成本'),
        ('gross_profit', '營業毛利'),
        ('opr_expenses', '營業費用'),
        ('opr_profit', '營業利益'),
        ('non_opr_income', '營業外收支'),
        ('pre_tax_income', '稅前淨利'),
        ('income_tax', '所得稅費用'),
        ('net_income', '稅後淨利'),
        ('eps', '每股盈餘'),
        ('curr_assets', '流動資產'),
        ('non_curr_assets', '非流動資產'),
        ('total_assets', '資產總額'),
        ('curr_liabs', '流動負債'),
        ('non_curr_liabs', '非流動負債'),
        ('total_liabs', '負債總額'),
        ('total_equity', '股東權益'),
        ('book_value', '每股淨值'),
        ('opr_cash_flow', '營業現金流'),
        ('inv_cash_flow', '投資現金流'),
        ('fin_cash_flow', '籌資現金流'),
        ('cash_equivs', '期末現金'),
    ]

    return _pivot_dataframe(df, items)


def transform_financial_metrics(df):
    """Transform financial metrics data to UI format (pivot)

    Source format: columns [code, year, quarter, gross_margin, ...]
    Target format: columns [Item, 2025.Q3, 2025.Q2, ...] (pivoted, items as rows)

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: Transformed DataFrame for UI display
    """
    if df.empty:
        return pd.DataFrame(columns=['Item'])

    # define items to display (column_name, display_name, formatter)
    # ratios are stored as decimals (e.g., 0.1234 for 12.34%), use format_100
    items = [
        ('gross_margin', '營業毛利率', format_100),
        ('opr_margin', '營業利益率', format_100),
        ('pre_tax_margin', '稅前淨利率', format_100),
        ('net_margin', '稅後淨利率', format_100),
        ('roa', '資產報酬率', format_100),
        ('roe', '股東權益報酬率', format_100),
        ('annual_roa', '年化 ROA', format_100),
        ('annual_roe', '年化 ROE', format_100),
        ('curr_ratio', '流動比率', format_100),
        ('quick_ratio', '速動比率', format_100),
        ('debt_ratio', '負債比率', format_100),
        ('fin_debt_ratio', '金融負債比', format_100),
        ('asset_turn_ratio', '資產週轉率'),
        ('days_inventory_outstd', '存貨週轉天數'),
        ('days_sales_outstd', '應收帳款週轉天數'),
        ('days_pay_outstd', '應付帳款週轉天數'),
        ('ccc', '現金循環週期'),
        ('eps_yoy', 'EPS 年增率', format_100),
        ('net_income_yoy', '淨利年增率', format_100),
        ('opr_cash_flow_yoy', '營業現金流年增率', format_100),
        ('gross_margin_yoy', '毛利率年增率', format_100),
        ('roe_yoy', 'ROE 年增率', format_100),
        ('pe_ratio', '本益比'),
        ('pb_ratio', '淨值比'),
        ('div_yield', '殖利率', format_100),
    ]

    return _pivot_dataframe(df, items)


def _pivot_dataframe(df, items):
    """Pivot DataFrame from row format to column format

    Args:
        df: Source DataFrame with year, quarter columns
        items: List of tuples (column_name, display_name)

    Returns:
        pd.DataFrame: Pivoted DataFrame with Item as first column
    """
    # create period labels (e.g., '2025.Q3')
    # sort by period descending (latest first)
    df_sorted = df.sort_values(
        by=['year', 'quarter'], ascending=[False, False]
    ).reset_index(drop=True)

    periods = (
        df_sorted['year'].astype(str) + '.Q' + df_sorted['quarter'].astype(str)
    ).tolist()

    # build result dictionary
    result_data = {'Item': []}

    for period in periods:
        result_data[period] = []

    # fill data for each item
    for item in items:
        col_name = item[0]
        display_name = item[1]
        formatter = item[2] if len(item) > 2 else format_value

        if col_name not in df_sorted.columns:
            continue

        result_data['Item'].append(display_name)

        for i, period in enumerate(periods):
            value = df_sorted.iloc[i][col_name]

            result_data[period].append(formatter(value))

    return pd.DataFrame(result_data)


def format_number(value):
    """Format number with comma separators

    Args:
        value: Numeric value

    Returns:
        str: Formatted string
    """
    if pd.isna(value):
        return ''
    try:
        return f'{int(value):,}'

    except (ValueError, TypeError):
        return str(value)


def format_percent(value):
    """Format percent value

    Args:
        value: Numeric value (decimal, e.g., 0.1234 for 12.34%)

    Returns:
        str: Formatted string with % sign
    """
    if pd.isna(value):
        return ''
    try:
        return f'{float(value) * 100:.2f}%'

    except (ValueError, TypeError):
        return str(value)


def format_100(value):
    """Format percent value without % sign

    Args:
        value: Numeric value (decimal, e.g., 0.1234 for 12.34)

    Returns:

        str: Formatted string without % sign
    """
    if pd.isna(value):
        return ''
    try:
        return f'{float(value) * 100:.2f}'

    except (ValueError, TypeError):
        return str(value)


def format_value(value):
    """Format general value for display

    Round to 2 decimal places for floats.

    Args:
        value: Any value

    Returns:
        str: Formatted string
    """
    if pd.isna(value):
        return ''
    if isinstance(value, float):
        return f'{value:.2f}'

    return str(value)
