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
        dict: Dictionary containing metadata:
              'code_name': Stock code and name, string
              'ohlc_price': OHLC price data, DataFrame
              'revenue': Revenue data, DataFrame
              'revenue_plot': Revenue plot data, DataFrame
              'financial': Financial data, DataFrame
              'financial_plot': Financial financial plot data, DataFrame
              'metrics': Financial metrics data, DataFrame
              'metrics_plot': Financial metrics plot data, DataFrame
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
    df_p = db.get_prices_by_code(stock_code, start_date=start_date)
    df_mp = db.get_monthly_avg_prices_by_code(stock_code, start_date=start_date)

    df_r = db.get_revenue_by_code(stock_code, start_date=start_date)
    df_f = db.get_recent_financial_by_code(stock_code, limit=8)
    df_m = db.get_recent_financial_metrics_by_code(stock_code, limit=8)

    # transform data
    df_p_plot = transform_ohlc_price(df_p)
    df_r_tbl = transform_revenue(df_r)
    df_r_plot = transform_revenue_plot(df_r, df_mp)
    df_f_tbl = transform_financial(df_f)
    df_f_plot = transform_financial_plot(df_f)
    df_m_tbl = transform_financial_metrics(df_m)
    df_m_plot = transform_financial_metrics_plot(df_m)

    return {
        'code_name': code_name,
        'ohlc_price': df_p_plot,
        'revenue': df_r_tbl,
        'revenue_plot': df_r_plot,
        'financial': df_f_tbl,
        'financial_plot': df_f_plot,
        'metrics': df_m_tbl,
        'metrics_plot': df_m_plot,
    }


def transform_ohlc_price(df):
    """Transform OHLC price data for plotting (mplfinance)

    Source format: columns [code, trade_date, open_price, high_price, ...]
    Target format: columns [Open, High, Low, Close, Volume]

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: Transformed DataFrame with DatetimeIndex
    """
    if df.empty:
        return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

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

    # sort by Date ascending (oldest first for chart)
    result = result.sort_index(ascending=True)

    return result


def transform_revenue(df):
    """Transform monthly revenue data to UI format

    Source format: columns [code, year, month, revenue, ...]
    Target format: columns [year_month, revenue, revenue_mom, revenue_ly, revenue_yoy, revenue_ytd, revenue_ytd_yoy]

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: Transformed DataFrame for UI display
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                'year_month',
                'revenue',
                'revenue_mom',
                'revenue_ly',
                'revenue_yoy',
                'revenue_ytd',
                'revenue_ytd_yoy',
            ]
        )

    # create result DataFrame
    result = pd.DataFrame()

    # create year_month column e.g. 2025/01
    result['year_month'] = (
        df['year'].astype(str) + '/' + df['month'].astype(str).str.zfill(2)
    )

    # define items to extract (column_name, formatter)
    # NOTE: if formatter not assigned, use format_value by default
    #       ratios stored as decimals (e.g., 0.1234 for 12.34%), use format_100
    items = [
        ('revenue',),
        ('revenue_mom', format_100),
        ('revenue_ly',),
        ('revenue_yoy', format_100),
        ('revenue_ytd',),
        ('revenue_ytd_yoy', format_100),
    ]

    # extract items and apply formatters
    for item in items:
        col = item[0]
        formatter = item[1] if len(item) > 1 else format_value

        if col not in df.columns:
            continue

        result[col] = df[col].apply(formatter)

    # sort by year_month descending (latest first)
    result = result.sort_values('year_month', ascending=False)

    return result.reset_index(drop=True)


def transform_revenue_plot(df_r, df_a):
    """Transform revenue and price data for plotting

    Args:
        df_r: Revenue DataFrame
        df_a: Monthly average price DataFrame

    Returns:
        pd.DataFrame: Merged and filtered DataFrame for plotting
                      columns: [year_month, revenue, revenue_ma3, revenue_ma12, revenue_yoy, price]
    """
    if df_r.empty:
        return pd.DataFrame(
            columns=[
                'year_month',
                'revenue',
                'revenue_ma3',
                'revenue_ma12',
                'revenue_yoy',
                'price',
            ]
        )

    # 1. prepare revenue data
    df_r_plot = pd.DataFrame()

    df_r_plot['year_month'] = (
        df_r['year'].astype(str) + '/' + df_r['month'].astype(str).str.zfill(2)
    )
    df_r_plot['revenue'] = df_r['revenue']
    df_r_plot['revenue_ma3'] = df_r['revenue_ma3']
    df_r_plot['revenue_ma12'] = df_r['revenue_ma12']
    df_r_plot['revenue_yoy'] = df_r['revenue_yoy'] * 100  # for percentage

    # 2. prepare price data
    if df_a.empty:
        df_a_plot = pd.DataFrame(columns=['year_month', 'price'])
    else:
        df_a_plot = pd.DataFrame()

        df_a_plot['year_month'] = (
            df_a['year'].astype(str) + '/' + df_a['month'].astype(str).str.zfill(2)
        )
        df_a_plot['price'] = df_a['price']

    # 3. merge
    result = pd.merge(df_r_plot, df_a_plot, on='year_month', how='left')

    # 4. sort by year_month ascending (oldest first for chart)
    result = result.sort_values('year_month')

    return result.reset_index(drop=True)


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

    # define items to extract (column_name, display_name, formatter)
    # NOTE: if formatter not assigned, use format_value by default
    #       ratios stored as decimals (e.g., 0.1234 for 12.34%), use format_100
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

    # define items to extract (column_name, display_name, formatter)
    # NOTE: if formatter not assigned, use format_value by default
    #       ratios stored as decimals (e.g., 0.1234 for 12.34%), use format_100
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
        ('gross_margin_qoq', '毛利率季增率', format_100),
        ('opr_margin_qoq', '營業利益率季增率', format_100),
        ('net_margin_qoq', '稅後淨利率季增率', format_100),
        ('gross_margin_yoy', '毛利率年增率', format_100),
        ('opr_margin_yoy', '營業利益率年增率', format_100),
        ('net_margin_yoy', '稅後淨利率年增率', format_100),
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
    # sort by year, quarter descending (latest first)
    df_sorted = df.sort_values(by=['year', 'quarter'], ascending=[False, False])

    df_sorted = df_sorted.reset_index(drop=True)

    # create year_quarter column e.g. 2025.Q1
    periods = (
        df_sorted['year'].astype(str) + '.Q' + df_sorted['quarter'].astype(str)
    ).tolist()

    # build result dictionary
    result = {'Item': []}

    for period in periods:
        result[period] = []

    # fill data for each item
    for item in items:
        col_name = item[0]
        display_name = item[1]
        formatter = item[2] if len(item) > 2 else format_value

        if col_name not in df_sorted.columns:
            continue

        result['Item'].append(display_name)

        for i, period in enumerate(periods):
            value = df_sorted.iloc[i][col_name]

            result[period].append(formatter(value))

    return pd.DataFrame(result)


def transform_financial_plot(df):
    """Transform financial data for plotting

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: DataFrame for plotting
                      columns: [year_quarter, net_income, opr_cash_flow, eps]
    """
    if df.empty:
        return pd.DataFrame()

    # create result DataFrame
    result = pd.DataFrame()

    # create year_quarter column e.g. 2025.Q1
    result['year_quarter'] = df['year'].astype(str) + '.Q' + df['quarter'].astype(str)

    # define items to extract
    items = ['net_income', 'opr_cash_flow', 'eps']

    for col in items:
        if col not in df.columns:
            continue

        result[col] = df[col]

    # sort by year_quarter ascending (oldest first for chart)
    result = result.sort_values('year_quarter', ascending=True)

    return result.reset_index(drop=True)


def transform_financial_metrics_plot(df):
    """Transform financial metrics data for plotting

    Args:
        df: Source DataFrame from database

    Returns:
        pd.DataFrame: DataFrame for plotting
                      columns: [year_quarter, gross_margin, opr_margin, net_margin, ...]
    """
    if df.empty:
        return pd.DataFrame()

    # create result DataFrame
    result = pd.DataFrame()

    # create year_quarter column e.g. 2025.Q1
    result['year_quarter'] = df['year'].astype(str) + '.Q' + df['quarter'].astype(str)

    # define items to extract (column_name, multiplier)
    # NOTE: multiply by 100 for percentage
    items = [
        ('gross_margin', 100),
        ('opr_margin', 100),
        ('net_margin', 100),
        ('gross_margin_qoq', 100),
        ('opr_margin_qoq', 100),
        ('net_margin_qoq', 100),
        ('gross_margin_yoy', 100),
        ('opr_margin_yoy', 100),
        ('net_margin_yoy', 100),
    ]

    # extract items
    for col, mul in items:
        if col not in df.columns:
            continue

        result[col] = df[col] * mul

    # sort by year_quarter ascending (oldest first for chart)
    result = result.sort_values('year_quarter', ascending=True)

    return result.reset_index(drop=True)


def format_currency(value):
    """Format number as string with thousands separators

    e.g., 1234567 -> '1,234,567'

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
    """Format decimal as percentage string with % sign (multiplied by 100)

    e.g., 0.1234 -> '12.34%'

    Args:
        value: Numeric value

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
    """Format decimal as percentage value string (multiplied by 100)

    e.g., 0.1234 -> '12.34'

    Args:
        value: Numeric value

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
    """Round numeric value to 2 decimal places string

    e.g., 12.3456 -> '12.35'

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
