"""Load stock data module

This module provides API for loading stock data from database and
transforming it to the format suitable for UI display
"""

import pandas as pd

from database.stock import StockDatabase


def load_stock(stock_code, db):
    """Load stock data from database

    Args:
        stock_code (str): Stock code
        db (StockDatabase): Database instance

    Returns:
        dict: Dictionary containing DataFrames
            - 'revenue': Revenue data
            - 'financial': Financial data
            - 'indicator': Financial metrics data
    """
    # retrieve data from database
    df_r = db.get_recent_revenue_by_code(stock_code, limit=24)
    df_f = db.get_recent_financial_by_code(stock_code, limit=8)
    df_m = db.get_recent_financial_metrics_by_code(stock_code, limit=8)

    # transform data
    tbl_r = transform_revenue(df_r)
    tbl_f = transform_financial(df_f)
    tbl_m = transform_financial_metrics(df_m)

    return {
        'revenue': tbl_r,
        'financial': tbl_f,
        'indicator': tbl_m,
    }


def transform_revenue(df):
    """Transform revenue data to UI format

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
            ]
        )

    # create year_month column
    result = pd.DataFrame()
    result['year_month'] = (
        df['year'].astype(str) + '/' + df['month'].astype(str).str.zfill(2)
    )

    # map columns and format values
    result['revence'] = df['revenue']  # .apply(format_number)
    result['revence_mom'] = df['revenue_mom'].apply(format_percent)
    result['revence_ly'] = df['revenue_ly']  # .apply(format_number)
    result['revence_yoy'] = df['revenue_yoy'].apply(format_percent)
    result['revence_ytd'] = df['revenue_ytd']  # .apply(format_number)
    result['revence_ytd_yoy'] = df['revenue_ytd_yoy'].apply(format_percent)

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

    # define items to display (column_name, display_name)
    items = [
        ('gross_margin', '營業毛利率'),
        ('opr_margin', '營業利益率'),
        ('pre_tax_margin', '稅前淨利率'),
        ('net_margin', '稅後淨利率'),
        ('roa', '資產報酬率'),
        ('roe', '股東權益報酬率'),
        ('annual_roa', '年化 ROA'),
        ('annual_roe', '年化 ROE'),
        ('curr_ratio', '流動比率'),
        ('quick_ratio', '速動比率'),
        ('debt_ratio', '負債比率'),
        ('fin_debt_ratio', '金融負債比'),
        ('asset_turn_ratio', '資產週轉率'),
        ('days_inventory_outstd', '存貨週轉天數'),
        ('days_sales_outstd', '應收帳款週轉天數'),
        ('days_pay_outstd', '應付帳款週轉天數'),
        ('ccc', '現金循環週期'),
        ('eps_yoy', 'EPS 年增率'),
        ('net_income_yoy', '淨利年增率'),
        ('opr_cash_flow_yoy', '營業現金流年增率'),
        ('gross_margin_yoy', '毛利率年增率'),
        ('roe_yoy', 'ROE 年增率'),
        ('pe_ratio', '本益比'),
        ('pb_ratio', '淨值比'),
        ('div_yield', '殖利率'),
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
    for col_name, display_name in items:
        if col_name not in df_sorted.columns:
            continue

        result_data['Item'].append(display_name)

        for i, period in enumerate(periods):
            value = df_sorted.iloc[i][col_name]
            result_data[period].append(format_value(value))

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


def format_value(value):
    """Format general value for display

    Args:
        value: Any value

    Returns:
        str: Formatted string
    """
    if pd.isna(value):
        return ''
    if isinstance(value, float):
        # round to 2 decimal places for floats
        return f'{value:.2f}'
    return str(value)
