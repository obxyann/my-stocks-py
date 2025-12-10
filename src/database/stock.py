import sys
import sqlite3
from datetime import datetime
import os
import pandas as pd
import re
import numpy as np

# add parent directory for importing from sibling directory
# sys.path.append('..')
# then
from utils.ass import ensure_directory_exists, modification_time, parse_date_string

class StockDatabase:
    """Database manager for stock data using SQLite"""

    def __init__ (self, db_path = 'storage/stock_data.db'):
        """Initialize database

        Args:
            db_path (str): Path to SQLite database file
        """
        self.metadata_table_initialized = False
        self.stock_list_table_initialized = False
        self.daily_prices_table_initialized = False
        self.monthly_revenue_table_initialized = False
        self.financial_core_table_initialized = False

        ensure_directory_exists(db_path)

        self.db_path = db_path

    def get_connection (self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)

        # enable foreign key constraint
        # conn.execute('PRAGMA foreign_keys = ON;')

        return conn

    ##################
    # Metadata table #
    ##################

    def ensure_metadata_table(self):
        """Create metadata table to track table update times if not exists"""
        if self.metadata_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    table_name TEXT PRIMARY KEY,
                    last_updated TIMESTAMP NOT NULL
                )
            ''')

            conn.commit()

        self.metadata_table_initialized = True

    def update_table_updated_time(self, table_name, updated_time = None):
        """Update last updated time for specific table

        Creates metadata table if missing. Uses current time if no timestamp provided.

        Args:
            table_name (str): Name of the table to update
            updated_time (datetime): Optional time
        """
        # create table if not exists
        self.ensure_metadata_table()

        # convert to ISO-8601 string 'YYYY-MM-DD HH:MM:SS'
        if not updated_time:
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = updated_time.strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # insert or replace data
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (table_name, last_updated)
                VALUES (?, ?)
            ''', (table_name, time_str))

            conn.commit()

    def get_table_updated_time(self, table_name):
        """Get last updated time for specific table

        Args:
            table_name (str): Name of the table

        Returns:
            datetime: Last updated time or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # retrieve data
            cursor.execute('''
                SELECT last_updated
                FROM metadata
                WHERE table_name = ?
            ''', (table_name,))

            result = cursor.fetchone()

        return datetime.fromisoformat(result[0]) if result else None

    ####################
    # Stock List table #
    ####################

    def ensure_stock_list_table(self):
        """Create stock_list table if not exists"""
        if self.stock_list_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_list (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    industry TEXT,
                    type TEXT NOT NULL
                )
            ''')

            conn.commit()

        self.stock_list_table_initialized = True

    def import_stock_list_csv_to_database(self, csv_path = 'storage/stock_list.csv'):
        """Import stock list from CSV to database

        Args:
            csv_path (str): Path to CSV file

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_stock_list_table()

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f'CSV file not found: {csv_path}')

        # compare file modification time with table updated time
        csv_mod_time = datetime.fromtimestamp(modification_time(csv_path))

        updated_time = self.get_table_updated_time('stock_list')

        if updated_time and csv_mod_time <= updated_time:
            print(f'{csv_path} is old')

            return 0

        print(f'Importing {csv_path}')

        # read CSV
        df = pd.read_csv(csv_path)
        # or
        # do not detect missing value markers
        # df = pd.read_csv(csv_path, na_filter = False)

        # rename columns to match database schema
        # df.rename(columns = {'Code': 'stock_code', 'Name': 'company_name'}, inplace = True)

        # convert 'code' to string to match schema
        # df['code'] = df['code'].astype(str)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # clear existing data
            cursor.execute('DELETE FROM stock_list')

            # insert new data
            df.to_sql('stock_list', conn, if_exists = 'append', index = False)

            conn.commit()

            # update table time
            self.update_table_updated_time('stock_list', csv_mod_time)

        return len(df)

    def get_stock_list(self):
        """Get all stocks from database

        Returns:
            pandas.DataFrame: Stock list data
        """
        with self.get_connection() as conn:
            # read data
            df = pd.read_sql_query('''
                SELECT code, name, market, industry, type
                FROM stock_list
                ORDER BY code
            ''', conn)

        return df

    def get_stock_by_code(self, stock_code):
        """Get specific stock by stock code

        Args:
            stock_code (str): Stock code

        Returns:
            pandas.DataFrame: Stock data
        """
        with self.get_connection() as conn:
            # retrieve data
            df = pd.read_sql_query('''
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE code = ?
            ''', conn, params = (stock_code,))

        return df

    def search_stocks(self, keyword):
        """Search stocks by name or code

        Args:
            keyword (str): Search keyword

        Returns:
            pandas.DataFrame: Matching stocks
        """
        with self.get_connection() as conn:
            # retrieve data
            df = pd.read_sql_query('''
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE code LIKE ? OR name LIKE ?
                ORDER BY code
            ''', conn, params = (f'%{keyword}%', f'%{keyword}%'))

        return df

    def get_stocks_by_market(self, market):
        """Get stocks by market

        Args:
            market (str): Market name ('tse', 'otc', 'esb')

        Returns:
            pandas.DataFrame: Stocks in specified market
        """
        with self.get_connection() as conn:
            # retrieve data
            df = pd.read_sql_query('''
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE market = ?
                ORDER BY code
            ''', conn, params = (market,))

        return df

    def get_stocks_by_industry(self, industry):
        """Get stocks by industry

        Args:
            industry (str): Industry name

        Returns:
            pandas.DataFrame: Stocks in specified industry
        """
        with self.get_connection() as conn:
            # retrieve data
            df = pd.read_sql_query('''
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE industry = ?
                ORDER BY code
            ''', conn, params = (industry,))

        return df

    ######################
    # Daily Prices table #
    ######################

    def ensure_daily_prices_table(self):
        """Create daily_prices table if not exists"""
        if self.daily_prices_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_prices (
                    code TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    PRIMARY KEY (code, trade_date),
                    FOREIGN KEY (code) REFERENCES stock_list (code)
                )
            ''')

            conn.commit()

        self.daily_price_table_initialized = True

    def get_prices_by_code(self, stock_code, start_date = '2013-01-01', end_date = None):
        """Get daily prices for stock code within date range

        Args:
            stock_code (str): Stock code
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format, defaults to today

        Returns:
            pandas.DataFrame: Daily prices data
        """
        # use today if end_date not provided
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        with self.get_connection() as conn:
            # retrieve data
            df = pd.read_sql_query('''
                SELECT *
                FROM daily_prices
                WHERE code = ?
                  AND trade_date BETWEEN ? AND ?
                ORDER BY trade_date
            ''', conn, params = (stock_code, start_date, end_date))

        return df

    def import_daily_prices_csv_to_database(self, csv_folder = 'storage/daily'):
        """Import daily prices from CSV to database

        Args:
            csv_folder (str): Path to the folder containing CSV files

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_daily_prices_table()

        if not os.path.isdir(csv_folder):
            raise FileNotFoundError(f'CSV folder not found: {csv_folder}')

        total_imported_records = 0
        last_mod_time = None # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        updated_time = self.get_table_updated_time('daily_prices')

        with self.get_connection() as conn:
            for file in files:
                match = re.search(r'prices_(\d{4})(\d{2})(\d{2})\.csv', file)
                if not match:
                    continue

                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))

                trade_date = f"{year}-{month:02d}-{day:02d}"

                csv_path = os.path.join(csv_folder, file)

                # compare file modification time with table updated time
                csv_mod_time = datetime.fromtimestamp(modification_time(csv_path))

                if updated_time and csv_mod_time <= updated_time:
                    print(f'{csv_path} is old')

                    continue

                print(f'Importing {csv_path}')

                # read CSV
                df = pd.read_csv(csv_path)

                # drop unnecessary columns
                if 'Name' in df.columns:
                    df = df.drop('Name', axis=1)
                if 'Value' in df.columns:
                    df = df.drop('Value', axis=1)
                if 'Market' in df.columns:
                    df = df.drop('Market', axis=1)

                # add trade_date column
                df['trade_date'] = trade_date

                # rename columns to match schema
                df.rename(columns = {
                    'Code': 'code',
                    'Open': 'open_price',
                    'High': 'high_price',
                    'Low': 'low_price',
                    'Close': 'close_price',
                    'Volume': 'volume'
                }, inplace = True)

                # convert 'code' to string to match schema
                df['code'] = df['code'].astype(str)

                # select and reorder columns for insertion
                df = df[['code', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']]

                # insert or replace data
                for _, row in df.iterrows():
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT OR REPLACE INTO daily_prices (code, trade_date, open_price, high_price, low_price, close_price, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['code'],
                        row['trade_date'],
                        row['open_price'],
                        row['high_price'],
                        row['low_price'],
                        row['close_price'],
                        row['volume']
                    ))

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if not last_mod_time or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.update_table_updated_time('daily_prices', last_mod_time)

        return total_imported_records

    def import_ohlc_prices_csv_to_database(self, csv_folder = 'storage/ohlc'):
        """Import OHLC prices from CSV to database

        Args:
            csv_folder (str): Path to the folder containing CSV files

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_daily_prices_table()

        if not os.path.isdir(csv_folder):
            raise FileNotFoundError(f'CSV folder not found: {csv_folder}')

        total_imported_records = 0
        last_mod_time = None # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        updated_time = self.get_table_updated_time('daily_prices')

        with self.get_connection() as conn:
            for file in files:
                match = re.match(r'^([A-Za-z0-9]+)_prices\.csv$', file)
                if not match:
                    continue

                code = match.group(1)

                csv_path = os.path.join(csv_folder, file)

                # compare file modification time with table updated time
                csv_mod_time = datetime.fromtimestamp(modification_time(csv_path))

                if updated_time and csv_mod_time <= updated_time:
                    print(f'{csv_path} is old')

                    continue

                print(f'Importing {csv_path}')

                # read CSV
                df = pd.read_csv(csv_path)

                # add code column
                df['code'] = code

                # rename columns to match schema
                df.rename(columns = {
                    'Date': 'trade_date',
                    'Open': 'open_price',
                    'High': 'high_price',
                    'Low': 'low_price',
                    'Close': 'close_price',
                    'Volume': 'volume'
                }, inplace = True)

                # ensure 'trade_date' in correct string format
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

                # select and reorder columns
                df = df[['code', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']]

                # insert or replace data
                for _, row in df.iterrows():
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT OR REPLACE INTO daily_prices (code, trade_date, open_price, high_price, low_price, close_price, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['code'],
                        row['trade_date'],
                        row['open_price'],
                        row['high_price'],
                        row['low_price'],
                        row['close_price'],
                        row['volume']
                    ))

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if not last_mod_time or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.update_table_updated_time('daily_prices', last_mod_time)

        return total_imported_records

    #########################
    # Monthly Revenue table #
    #########################

    def ensure_monthly_revenue_table(self):
        """Create monthly_revenue table if not exists"""
        if self.monthly_revenue_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monthly_revenue (
                    code TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    revenue INTEGER NOT NULL,
                    revenue_last_year INTEGER,
                    cumulative_revenue INTEGER,
                    cumulative_revenue_last_year INTEGER,
                    mom REAL,
                    yoy REAL,
                    cumulative_revenue_yoy REAL,
                    note TEXT,
                    PRIMARY KEY (code, year, month),
                    FOREIGN KEY (code) REFERENCES stock_list (code)
                )
            ''')

            conn.commit()

        self.monthly_revenue_table_initialized = True

    def import_monthly_revenue_csv_to_database(self, csv_folder = 'storage/monthly'):
        """Import monthly revenue from CSV to database

        Args:
            csv_folder (str): Path to the folder containing CSV files

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_monthly_revenue_table()

        if not os.path.isdir(csv_folder):
            raise FileNotFoundError(f'CSV folder not found: {csv_folder}')

        total_imported_records = 0
        last_mod_time = None # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        updated_time = self.get_table_updated_time('monthly_revenue')

        with self.get_connection() as conn:
            for file in files:
                match = re.search(r'revenues_(\d{4})(\d{2})\.csv', file)
                if not match:
                    continue

                year, month = int(match.group(1)), int(match.group(2))

                csv_path = os.path.join(csv_folder, file)

                # compare file modification time with table updated time
                csv_mod_time = datetime.fromtimestamp(modification_time(csv_path))

                if updated_time and csv_mod_time <= updated_time:
                    print(f'{csv_path} is old')

                    continue

                print(f'Importing {csv_path}')

                # read CSV
                df = pd.read_csv(csv_path)

                df['year'] = year
                df['month'] = month

                # rename columns to match schema
                df.rename(columns = {'Code': 'code', 'Revenue': 'revenue', 'Note': 'note'}, inplace = True)

                # select and reorder columns
                df = df[['code', 'year', 'month', 'revenue', 'note']]

                # convert 'code' to string to match schema
                df['code'] = df['code'].astype(str)

                # insert or replace data
                for _, row in df.iterrows():
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT OR REPLACE INTO monthly_revenue (code, year, month, revenue, note)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row['code'],
                        row['year'],
                        row['month'],
                        row['revenue'],
                        row['note']
                    ))

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if not last_mod_time or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.update_table_updated_time('monthly_revenue', last_mod_time)

        # update calculated fields after import
        # self.update_monthly_revenue_calculations()

        return total_imported_records

    def update_monthly_revenue_calculations(self):
        """Update calculated fields in monthly_revenue table"""
        with self.get_connection() as conn:
            df = pd.read_sql_query('SELECT * FROM monthly_revenue', conn)

            if df.empty:
                return

            df.sort_values(by = ['code', 'year', 'month'], inplace = True)

            # calculate derived fields
            df['revenue_last_year'] = df.groupby('code')['revenue'].transform(lambda x: x.shift(12))
            df['cumulative_revenue'] = df.groupby(['code', 'year'])['revenue'].cumsum()
            df['cumulative_revenue_last_year'] = df.groupby('code')['cumulative_revenue'].transform(lambda x: x.shift(12))
            df['mom'] = df.groupby('code')['revenue'].pct_change(periods = 1) * 100
            df['yoy'] = df.groupby('code')['revenue'].pct_change(periods = 12) * 100
            df['cumulative_revenue_yoy'] = (df['cumulative_revenue'] / df['cumulative_revenue_last_year'] - 1) * 100

            # replace infinite values with NaN
            df.replace([np.inf, -np.inf], np.nan, inplace=True)

            # update data
            update_query = '''
                UPDATE monthly_revenue
                SET revenue_last_year = ?,
                    cumulative_revenue = ?,
                    cumulative_revenue_last_year = ?,
                    mom = ?,
                    yoy = ?,
                    cumulative_revenue_yoy = ?
                WHERE code = ? AND year = ? AND month = ?
            '''

            update_data = [
                (
                    row['revenue_last_year'] if pd.notna(row['revenue_last_year']) else None,
                    row['cumulative_revenue'] if pd.notna(row['cumulative_revenue']) else None,
                    row['cumulative_revenue_last_year'] if pd.notna(row['cumulative_revenue_last_year']) else None,
                    row['mom'] if pd.notna(row['mom']) else None,
                    row['yoy'] if pd.notna(row['yoy']) else None,
                    row['cumulative_revenue_yoy'] if pd.notna(row['cumulative_revenue_yoy']) else None,
                    row['code'],
                    row['year'],
                    row['month']
                )
                for _, row in df.iterrows()
            ]

            cursor = conn.cursor()

            cursor.executemany(update_query, update_data)

            conn.commit()

    def get_revenue_by_code(self, stock_code, start_date = '2013-01-01', end_date = None):
        """Get monthly revenue data for specific stock

        Args:
            stock_code (str): Stock code
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)

        Returns:
            pandas.DataFrame: Revenue data
        """
        # convert date string to datetime
        start = parse_date_string(start_date)
        # get year, month parts
        start_year, start_month = start.year, start.month

        # end year, month
        if end_date:
            end = parse_date_string(end_date)
        else:
            end = datetime.today()
        end_year, end_month = end.year, end.month

        # convert to comparable period (YYYYMM)
        start_period = start_year * 100 + start_month
        end_period = end_year * 100 + end_month

        with self.get_connection() as conn:
            # retrieve data
            df = pd.read_sql_query('''
                SELECT *
                FROM monthly_revenue
                WHERE code = ?
                  AND (year * 100 + month) BETWEEN ? AND ?
                ORDER BY year, month
            ''', conn, params = (stock_code, start_period, end_period))

        return df

    ########################
    # Financial Core table #
    ########################

    def ensure_financial_core_table(self):
        """Create financial_core table if not exists"""
        if self.financial_core_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS financial_core (
                    code TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    quarter INTEGER NOT NULL,
                    curr_assets INTEGER,
                    non_curr_assets INTEGER,
                    total_assets INTEGER,
                    curr_liabs INTEGER,
                    non_curr_liabs INTEGER,
                    total_liabs INTEGER,
                    total_equity INTEGER,
                    book_value REAL,
                    accts_receiv INTEGER,
                    accts_notes_receiv INTEGER,
                    inventory INTEGER,
                    prepaid INTEGER,
                    accts_pay INTEGER,
                    accts_notes_pay INTEGER,
                    st_loans INTEGER,
                    lt_loans INTEGER,
                    bonds_pay INTEGER,
                    ret_earnings INTEGER,
                    opr_revenue INTEGER,
                    opr_costs INTEGER,
                    gross_profit INTEGER,
                    opr_expenses INTEGER,
                    opr_profit INTEGER,
                    non_opr_income INTEGER,
                    pre_tax_income INTEGER,
                    income_tax INTEGER,
                    net_income INTEGER,
                    eps REAL,
                    opr_cash_flow INTEGER,
                    inv_cash_flow INTEGER,
                    fin_cash_flow INTEGER,
                    cash_equiv INTEGER,
                    divs_paid INTEGER,
                    PRIMARY KEY (code, year, quarter),
                    FOREIGN KEY (code) REFERENCES stock_list (code)
                )
            ''')

            conn.commit()

        self.financial_core_table_initialized = True

    def import_income_reports_csv_to_database(self, csv_folder = 'storage/quarterly'):
        """Import income reports from CSV to database

        Args:
            csv_folder (str): Path to the folder containing CSV files

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_financial_core_table()

        if not os.path.isdir(csv_folder):
            raise FileNotFoundError(f'CSV folder not found: {csv_folder}')

        total_imported_records = 0
        last_mod_time = None # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        updated_time = self.get_table_updated_time('financial_core')

        # define column mapping
        col_mapping = {
            '營業收入': 'opr_revenue',
            '營業成本': 'opr_costs',
            '營業毛利': 'gross_profit',
            '營業費用': 'opr_expenses',
            '營業利益': 'opr_profit',
            '營業外收入及支出': 'non_opr_income',
            '稅前淨利': 'pre_tax_income',
            '所得稅費用': 'income_tax',
            '本期淨利': 'net_income',
            '每股盈餘': 'eps'
        }

        with self.get_connection() as conn:
            for file in files:
                match = re.search(r'income_reports_(\d{4})Q(\d)\.csv', file)
                if not match:
                    continue

                year, quarter = int(match.group(1)), int(match.group(2))

                csv_path = os.path.join(csv_folder, file)

                # compare file modification time with table updated time
                csv_mod_time = datetime.fromtimestamp(modification_time(csv_path))

                if updated_time and csv_mod_time <= updated_time:
                    print(f'{csv_path} is old')

                    continue

                print(f'Importing {csv_path}')

                # read CSV
                try:
                    df = pd.read_csv(csv_path)

                except Exception as e:
                    print(f"Error reading {csv_path}: {e}")

                    continue

                if 'Code' not in df.columns:
                     print(f"Skipping {csv_path}: No 'Code' column found")

                     continue

                df.rename(columns = {'Code': 'code'}, inplace = True)

                # remove rows with empty code
                df.dropna(subset = 'code', inplace = True)

                # convert 'code' to string to match schema
                df['code'] = df['code'].astype(str)

                # add new columns
                df['year'] = year
                df['quarter'] = quarter

                # rename columns based on mapping
                rename_dict = {}
                keep_cols = ['code', 'year', 'quarter']

                for csv_col, db_col in col_mapping.items():
                    if csv_col in df.columns:
                        rename_dict[csv_col] = db_col

                        keep_cols.append(db_col)

                df.rename(columns = rename_dict, inplace = True)

                # keep only relevant columns
                available_db_cols = [c for c in df.columns if c in keep_cols]

                df = df[available_db_cols]

                if df.empty:
                    continue

                # replace NaNs with None for SQLite compatibility
                df = df.where(pd.notnull(df), None)

                # insert or update data
                # construct dynamic SQL
                columns = ', '.join(available_db_cols)
                placeholders = ', '.join(['?'] * len(available_db_cols))

                # update part: exclude code, year, quarter from SET
                update_cols = [c for c in available_db_cols if c not in ('code', 'year', 'quarter')]

                if not update_cols:
                    # insert data
                    sql = f'''
                        INSERT OR IGNORE INTO financial_core ({columns})
                        VALUES ({placeholders})
                    '''
                else:
                    update_assignments = ', '.join([f"{col}=excluded.{col}" for col in update_cols])

                    # upsert data
                    sql = f'''
                        INSERT INTO financial_core ({columns})
                        VALUES ({placeholders})
                        ON CONFLICT(code, year, quarter) DO UPDATE SET
                        {update_assignments}
                    '''

                data = df.values.tolist()

                cursor = conn.cursor()

                cursor.executemany(sql, data)

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if not last_mod_time or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.update_table_updated_time('financial_core', last_mod_time)

        return total_imported_records

    #################
    # Database info #
    #################

    def get_database_info(self):
        """Get database information

        Returns:
            dict: Database statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # get all tables in database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [table[0] for table in cursor.fetchall()]

            # for stock list table
            stock_list = {}
            # 1. get total count
            cursor.execute('SELECT COUNT(*) FROM stock_list')
            stock_list['total_count'] = cursor.fetchone()[0]

            # 2. get market distribution
            cursor.execute('''
                SELECT market, COUNT(*)
                FROM stock_list
                GROUP BY market
                ORDER BY market
            ''')
            stock_list['market_stats'] = dict(cursor.fetchall())

            # 3. get last update time from metadata
            stock_list['last_updated'] = self.get_table_updated_time('stock_list') # <- datetime

            # for monthly revenue table
            monthly_revenue = {}
            # 1. get total count
            cursor.execute('SELECT COUNT(*) FROM monthly_revenue')
            monthly_revenue['total_count'] = cursor.fetchone()[0]

            # 2. get min and max year-month
            cursor.execute('SELECT MIN(year * 100 + month), MAX(year * 100 + month) FROM monthly_revenue')
            min_max_result = cursor.fetchone()
            monthly_revenue['min_year_month'] = min_max_result[0] if min_max_result[0] is not None else None
            monthly_revenue['max_year_month'] = min_max_result[1] if min_max_result[1] is not None else None

            # 3. get last update time from metadata
            monthly_revenue['last_updated'] = self.get_table_updated_time('monthly_revenue') # <- datetime

            # for daily prices table
            daily_prices = {}
            # 1. get total count
            cursor.execute('SELECT COUNT(*) FROM daily_prices')
            daily_prices['total_count'] = cursor.fetchone()[0]

            # 2. get min and max trade date
            cursor.execute('SELECT MIN(trade_date), MAX(trade_date) FROM daily_prices')
            min_max_result = cursor.fetchone()
            daily_prices['min_trade_date'] = min_max_result[0] if min_max_result[0] is not None else None
            daily_prices['max_trade_date'] = min_max_result[1] if min_max_result[1] is not None else None

            # 3. get last update time from metadata
            daily_prices['last_updated'] = self.get_table_updated_time('daily_prices') # <- datetime

        return {
            'database_path': self.db_path,
            'tables': tables,

            'stock_list': stock_list,
            'monthly_revenue': monthly_revenue,
            'daily_prices': daily_prices
        }
