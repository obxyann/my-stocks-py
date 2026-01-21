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
    # df_mp_plot = transform_monthly_avg_price(df_mp)
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


def transform_revenue(df):
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


def transform_revenue_plot(df_r, df_a):
    """Transform revenue and price data for plotting

    Args:
        df_r: Revenue DataFrame
        df_a: Monthly average price DataFrame

    Returns:
        pd.DataFrame: Merged and filtered DataFrame for plotting
                      columns: [year_month, revence, revenue_ma3, revenue_ma12, revence_yoy, price]
    """
    if df_r.empty:
        return pd.DataFrame(
            columns=[
                'year_month',
                'revence',
                'revenue_ma3',
                'revenue_ma12',
                'revence_yoy',
                'price',
            ]
        )

    # 1. prepare revenue data
    df_r_plot = pd.DataFrame()
    df_r_plot['year_month'] = (
        df_r['year'].astype(str) + '/' + df_r['month'].astype(str).str.zfill(2)
    )
    df_r_plot['revence'] = df_r['revenue']
    df_r_plot['revenue_ma3'] = df_r['revenue_ma3']
    df_r_plot['revenue_ma12'] = df_r['revenue_ma12']
    # multiply by 100 for percentage
    df_r_plot['revence_yoy'] = df_r['revenue_yoy'] * 100

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
    result = result.sort_values('year_month').reset_index(drop=True)

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

    # work on copy
    result = df.copy()

    # create year_quarter column e.g. 2025.Q3
    result['year_quarter'] = (
        result['year'].astype(str) + '.Q' + result['quarter'].astype(str)
    )

    # select columns for plot
    # gross_margin, opr_margin, net_margin
    # gross_margin_qoq, opr_margin_qoq, net_margin_qoq
    # gross_margin_yoy, opr_margin_yoy, net_margin_yoy

    # multiply by 100 for percentage
    cols_to_percent = [
        'gross_margin',
        'opr_margin',
        'net_margin',
        'gross_margin_qoq',
        'opr_margin_qoq',
        'net_margin_qoq',
        'gross_margin_yoy',
        'opr_margin_yoy',
        'net_margin_yoy',
    ]

    for col in cols_to_percent:
        if col in result.columns:
            result[col] = result[col] * 100

    # sort by year, quarter ascending (oldest first for chart)
    result = result.sort_values(by=['year', 'quarter'], ascending=[True, True])

    return result.reset_index(drop=True)


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

    # work on copy
    result = df.copy()

    # create year_quarter column e.g. 2025.Q3
    result['year_quarter'] = (
        result['year'].astype(str) + '.Q' + result['quarter'].astype(str)
    )

    # select columns for plot
    # net_income, opr_cash_flow, eps
    cols_to_keep = ['year_quarter', 'net_income', 'opr_cash_flow', 'eps']

    # ensure columns exist
    existing_cols = [col for col in cols_to_keep if col in result.columns]
    
    result = result[existing_cols]

    # sort by year, quarter ascending (oldest first for chart)
    # we need to recover year/quarter from year_quarter or use original df index if preserved
    # faster way: just rely on the fact that we derived it from a df that has year/quarter.
    # But we just sliced it. So we need to sort BEFORE slicing or include year/quarter in slice then drop.

    # Better approach: Sort original df copy first, then assign year_quarter, then slice.

    # Let's re-do logic slightly to be safe
    df_sorted = df.sort_values(by=['year', 'quarter'], ascending=[True, True])

    result = pd.DataFrame()
    result['year_quarter'] = (
        df_sorted['year'].astype(str) + '.Q' + df_sorted['quarter'].astype(str)
    )

    if 'net_income' in df_sorted.columns:
        result['net_income'] = df_sorted['net_income']
    if 'opr_cash_flow' in df_sorted.columns:
        result['opr_cash_flow'] = df_sorted['opr_cash_flow']
    if 'eps' in df_sorted.columns:
        result['eps'] = df_sorted['eps']

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
