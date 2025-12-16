import os
import re
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

# add parent directory for importing from sibling directory
# sys.path.append('..')
# then
from utils.ass import ensure_directory_exists, modification_time, parse_date_string


class StockDatabase:
    """Database manager for stock data using SQLite"""

    def __init__(self, db_path='storage/stock_data.db'):
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

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)

        # enable foreign key constraint
        # conn.execute('PRAGMA foreign_keys = ON;')

        return conn

    ##################
    # Metadata table #
    ##################

    def ensure_metadata_table(self):
        """Create metadata table if not exists"""
        if self.metadata_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    table_name TEXT PRIMARY KEY,
                    last_updated TIMESTAMP NOT NULL
                )
                """)

            conn.commit()

        self.metadata_table_initialized = True

    def set_table_updated_time(self, table_name, updated_at=None):
        """Set last updated time for specific table

        Args:
            table_name (str): Name of the table
            updated_at (datetime): Updated time, use current time if not provided
        """
        # create table if not exists
        self.ensure_metadata_table()

        # convert to ISO-8601 string 'YYYY-MM-DD HH:MM:SS'
        if updated_at is None:
            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = updated_at.strftime('%Y-%m-%d %H:%M:%S')

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # insert or replace data
            cursor.execute(
                """
                INSERT OR REPLACE INTO metadata (table_name, last_updated)
                VALUES (?, ?)
                """,
                (table_name, time_str),
            )

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

            try:
                # retrieve data
                cursor.execute(
                    """
                    SELECT last_updated
                    FROM metadata
                    WHERE table_name = ?
                    """,
                    (table_name,),
                )

                result = cursor.fetchone()

            except sqlite3.OperationalError:
                return None

        return datetime.fromisoformat(result[0]) if result else None

    def update_table_time(self, table_name, updated_at=None):
        """Update last updated time for specific table

        Only sets time when it is newer than the last updated time.

        Args:
            table_name (str): Name of the table
            updated_at (datetime): Updated time, use current time if not provided
        """
        if updated_at is None:
            updated_at = datetime.now()

        last_time = self.get_table_updated_time(table_name)

        if last_time is None or updated_at > last_time:
            self.set_table_updated_time(table_name, updated_at)

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_list (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    industry TEXT,
                    sector TEXT,
                    type TEXT NOT NULL
                )
                """)

            conn.commit()

        self.stock_list_table_initialized = True

    def import_stock_list_csv_to_database(self, csv_path='storage/stock_list.csv'):
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

        # define column mapping
        col_mapping = {
            'Code': 'code',
            'Name': 'name',
            'Market': 'market',
            'Industry': 'industry',
            'Type': 'type',
        }

        try:
            # read CSV
            df = pd.read_csv(csv_path)

            # build rename and need columns (based on mapping)
            rename_dict = {}
            use_cols = []

            for csv_col, db_col in col_mapping.items():
                if csv_col in df.columns:
                    rename_dict[csv_col] = db_col

                use_cols.append(db_col)

            # rename columns
            df.rename(columns=rename_dict, inplace=True)

            # available columns
            avail_cols = [c for c in df.columns if c in use_cols]

            # check for mandatory columns
            # (based on table schema NOT NULL constraints)
            mandatory_cols = [
                'code',
                'name',
                'market',
                'type',
            ]
            missing_cols = [c for c in mandatory_cols if c not in avail_cols]

            if missing_cols:
                print(f'Error: Missing mandatory columns {missing_cols}')

                return 0

            # keep only relevant columns
            df = df[avail_cols]

            # remove rows with empty code
            df.dropna(subset=['code'], inplace=True)

            # ensure 'code' in string format
            df['code'] = df['code'].astype(str)

            # replace NaNs with None for SQLite compatibility
            df = df.where(pd.notnull(df), None)

            # prepare SQL
            columns = ', '.join(avail_cols)
            placeholders = ', '.join(['?'] * len(avail_cols))

            sql = f'INSERT INTO stock_list ({columns}) VALUES ({placeholders})'

            data = df.values.tolist()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # clear existing data
                cursor.execute('DELETE FROM stock_list')

                # insert new data
                cursor.executemany(sql, data)

                conn.commit()

                # update table time
                self.set_table_updated_time('stock_list', csv_mod_time)

            return len(df)

        except Exception as e:
            print(f'Error: {e}')

            return 0

    def get_stock_list(self):
        """Get all stocks from database

        Returns:
            pandas.DataFrame: Stock list data
        """
        with self.get_connection() as conn:
            # read data
            df = pd.read_sql_query(
                """
                SELECT code, name, market, industry, type
                FROM stock_list
                ORDER BY code
                """,
                conn,
            )

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
            df = pd.read_sql_query(
                """
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE code = ?
                """,
                conn,
                params=(stock_code,),
            )

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
            df = pd.read_sql_query(
                """
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE code LIKE ? OR name LIKE ?
                ORDER BY code
                """,
                conn,
                params=(f'%{keyword}%', f'%{keyword}%'),
            )

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
            df = pd.read_sql_query(
                """
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE market = ?
                ORDER BY code
                """,
                conn,
                params=(market,),
            )

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
            df = pd.read_sql_query(
                """
                SELECT code, name, market, industry, type
                FROM stock_list
                WHERE industry = ?
                ORDER BY code
                """,
                conn,
                params=(industry,),
            )

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_prices (
                    code TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    --
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    --
                    volume INTEGER NOT NULL,
                    PRIMARY KEY (code, trade_date),
                    FOREIGN KEY (code) REFERENCES stock_list (code)
                )
                """)

            conn.commit()

        self.daily_price_table_initialized = True

    def import_daily_prices_csv_to_database(self, csv_folder='storage/daily'):
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
        last_mod_time = None  # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        # NOTE: '__prices' is not a real table name, just for tracking the
        #       last updated time of different data sources for 'daily_prices'
        updated_time = self.get_table_updated_time('__prices')

        # define column mapping
        col_mapping = {
            'Code': 'code',
            'Open': 'open_price',
            'High': 'high_price',
            'Low': 'low_price',
            'Close': 'close_price',
            'Volume': 'volume',
        }

        with self.get_connection() as conn:
            for file in files:
                match = re.search(r'prices_(\d{4})(\d{2})(\d{2})\.csv', file)
                if not match:
                    continue

                year, month, day = (
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                )

                trade_date = f'{year}-{month:02d}-{day:02d}'

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
                    print(f'Error: Failed reading: {e}')

                    continue

                # add new column
                df['trade_date'] = trade_date

                # build rename and need columns (based on mapping)
                rename_dict = {}
                use_cols = ['trade_date']

                for csv_col, db_col in col_mapping.items():
                    if csv_col in df.columns:
                        rename_dict[csv_col] = db_col

                    use_cols.append(db_col)

                # rename columns
                df.rename(columns=rename_dict, inplace=True)

                # available columns
                avail_cols = [c for c in df.columns if c in use_cols]

                # check for mandatory columns
                # (based on table schema NOT NULL constraints)
                mandatory_cols = [
                    'code',
                    # 'trade_date', <- no need to check
                    'open_price',
                    'high_price',
                    'low_price',
                    'close_price',
                    'volume',
                ]
                missing_cols = [c for c in mandatory_cols if c not in avail_cols]

                if missing_cols:
                    print(f'Error: Missing mandatory columns {missing_cols}')

                    continue

                # keep only relevant columns
                df = df[avail_cols]

                # remove rows with empty code
                df.dropna(subset=['code'], inplace=True)

                # ensure 'code' in string format
                df['code'] = df['code'].astype(str)

                # replace NaNs with None for SQLite compatibility
                df = df.where(pd.notnull(df), None)

                # prepare SQL
                columns = ', '.join(avail_cols)
                placeholders = ', '.join(['?'] * len(avail_cols))

                sql = f'INSERT OR REPLACE INTO daily_prices ({columns}) VALUES ({placeholders})'

                data = df.values.tolist()

                cursor = conn.cursor()

                # insert or replace data
                cursor.executemany(sql, data)

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if last_mod_time is None or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.set_table_updated_time('__prices', last_mod_time)

            self.update_table_time('daily_prices', last_mod_time)

        return total_imported_records

    def import_ohlc_prices_csv_to_database(self, csv_folder='storage/ohlc'):
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
        last_mod_time = None  # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        # NOTE: '__abc_prices' is not a real table name, just for tracking the
        #       last updated time of different data sources for 'daily_prices'
        updated_time = self.get_table_updated_time('__abc_prices')

        # define column mapping
        col_mapping = {
            'Date': 'trade_date',
            'Open': 'open_price',
            'High': 'high_price',
            'Low': 'low_price',
            'Close': 'close_price',
            'Volume': 'volume',
        }

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
                try:
                    df = pd.read_csv(csv_path)

                except Exception as e:
                    print(f'Error: Failed reading: {e}')

                    continue

                # add new column
                df['code'] = code

                # build rename and need columns (based on mapping)
                rename_dict = {}
                use_cols = ['code']

                for csv_col, db_col in col_mapping.items():
                    if csv_col in df.columns:
                        rename_dict[csv_col] = db_col

                    use_cols.append(db_col)

                # rename columns
                df.rename(columns=rename_dict, inplace=True)

                # available columns
                avail_cols = [c for c in df.columns if c in use_cols]

                # check for mandatory columns
                # (based on table schema NOT NULL constraints)
                mandatory_cols = [
                    # 'code', <- no need to check
                    'trade_date',
                    'open_price',
                    'high_price',
                    'low_price',
                    'close_price',
                    'volume',
                ]
                missing_cols = [c for c in mandatory_cols if c not in avail_cols]

                if missing_cols:
                    print(f'Error: Missing mandatory columns {missing_cols}')

                    continue

                # keep only relevant columns
                df = df[avail_cols]

                # ensure 'trade_date' in correct string format
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime(
                    '%Y-%m-%d'
                )

                # replace NaNs with None for SQLite compatibility
                df = df.where(pd.notnull(df), None)

                # prepare SQL
                columns = ', '.join(avail_cols)
                placeholders = ', '.join(['?'] * len(avail_cols))

                sql = f'INSERT OR REPLACE INTO daily_prices ({columns}) VALUES ({placeholders})'

                data = df.values.tolist()

                cursor = conn.cursor()

                # insert or replace data
                cursor.executemany(sql, data)

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if last_mod_time is None or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.set_table_updated_time('__abc_prices', last_mod_time)

            self.update_table_time('daily_prices', last_mod_time)

        return total_imported_records

    def get_prices_by_code(self, stock_code, start_date='2013-01-01', end_date=None):
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
            df = pd.read_sql_query(
                """
                SELECT *
                FROM daily_prices
                WHERE code = ?
                  AND trade_date BETWEEN ? AND ?
                ORDER BY trade_date
                """,
                conn,
                params=(stock_code, start_date, end_date),
            )

        return df

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_revenue (
                    code TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    revenue INTEGER NOT NULL,
                    note TEXT,
                    --
                    revenue_last_year INTEGER,
                    cumulative_revenue INTEGER,
                    cumulative_revenue_last_year INTEGER,
                    mom REAL,
                    yoy REAL,
                    cumulative_revenue_yoy REAL,
                    PRIMARY KEY (code, year, month),
                    FOREIGN KEY (code) REFERENCES stock_list (code)
                )
                """)

            conn.commit()

        self.monthly_revenue_table_initialized = True

    def import_monthly_revenue_csv_to_database(self, csv_folder='storage/monthly'):
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
        last_mod_time = None  # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        updated_time = self.get_table_updated_time('monthly_revenue')

        # define column mapping
        col_mapping = {
            'Code': 'code',
            'Revenue': 'revenue',
            'Note': 'note',
        }

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
                try:
                    df = pd.read_csv(csv_path)

                except Exception as e:
                    print(f'Error: Failed reading: {e}')

                    continue

                # add new columns
                df['year'] = year
                df['month'] = month

                # build rename and need columns (based on mapping)
                rename_dict = {}
                use_cols = ['year', 'month']

                for csv_col, db_col in col_mapping.items():
                    if csv_col in df.columns:
                        rename_dict[csv_col] = db_col

                    use_cols.append(db_col)

                # rename columns
                df.rename(columns=rename_dict, inplace=True)

                # available columns
                avail_cols = [c for c in df.columns if c in use_cols]

                # check for mandatory columns
                # (based on table schema NOT NULL constraints)
                mandatory_cols = [
                    'code',
                    # 'year', <- no need to check
                    # 'month', <- no need to check
                    'revenue',
                ]
                missing_cols = [c for c in mandatory_cols if c not in avail_cols]

                if missing_cols:
                    print(f'Error: Missing mandatory columns {missing_cols}')

                    continue

                # keep only relevant columns
                df = df[avail_cols]

                # remove rows with empty code
                df.dropna(subset=['code'], inplace=True)

                # ensure 'code' in string format
                df['code'] = df['code'].astype(str)

                # replace NaNs with None for SQLite compatibility
                df = df.where(pd.notnull(df), None)

                # prepare SQL
                columns = ', '.join(avail_cols)
                placeholders = ', '.join(['?'] * len(avail_cols))

                sql = f'INSERT OR REPLACE INTO monthly_revenue ({columns}) VALUES ({placeholders})'

                data = df.values.tolist()

                cursor = conn.cursor()

                # insert or replace data
                cursor.executemany(sql, data)

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if last_mod_time is None or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.set_table_updated_time('monthly_revenue', last_mod_time)

        # update calculated fields after import
        # self.update_monthly_revenue_calculations()

        return total_imported_records

    def update_monthly_revenue_calculations(self):
        """Update calculated fields in monthly_revenue table"""
        with self.get_connection() as conn:
            try:
                # prepare SQL
                # use SQL Window Functions to do incremental updates w/o pandas loading
                update_query = """
                    WITH Calculated AS (
                        SELECT
                            code,
                            year,
                            month,
                            revenue,
                            -- revenue_last_year (LAG 12 of revenue)
                            LAG(revenue, 12) OVER (
                                PARTITION BY code
                                ORDER BY year, month
                            ) as val_revenue_last_year,
                            -- cumulative_revenue (partition by code, year)
                            SUM(revenue) OVER (
                                PARTITION BY code, year
                                ORDER BY month
                            ) as val_cumulative_revenue,
                            -- revenue_prev_month (LAG 1 or revenue) for mom
                            LAG(revenue, 1) OVER (
                                PARTITION BY code
                                ORDER BY year, month
                            ) as val_revenue_prev_month
                        FROM monthly_revenue
                    ),
                    Refined AS (
                        SELECT
                            code,
                            year,
                            month,
                            revenue,
                            val_revenue_last_year,
                            val_cumulative_revenue,
                            -- cumulative_revenue_last_year (LAG 12 of cumulative)
                            LAG(val_cumulative_revenue, 12) OVER (
                                PARTITION BY code
                                ORDER BY year, month
                            ) as val_cumulative_revenue_last_year,
                            val_revenue_prev_month
                        FROM Calculated
                    ),
                    Final AS (
                        SELECT
                            code,
                            year,
                            month,
                            val_revenue_last_year,
                            val_cumulative_revenue,
                            val_cumulative_revenue_last_year,
                            -- mom
                            CASE
                                WHEN val_revenue_prev_month IS NOT NULL AND val_revenue_prev_month != 0
                                THEN (revenue * 1.0 / val_revenue_prev_month - 1.0) * 100
                                ELSE NULL
                            END as val_mom,
                            -- yoy
                            CASE
                                WHEN val_revenue_last_year IS NOT NULL AND val_revenue_last_year != 0
                                THEN (revenue * 1.0 / val_revenue_last_year - 1.0) * 100
                                ELSE NULL
                            END as val_yoy,
                            -- cumulative_revenue_yoy
                            CASE
                                WHEN val_cumulative_revenue_last_year IS NOT NULL AND val_cumulative_revenue_last_year != 0
                                THEN (val_cumulative_revenue * 1.0 / val_cumulative_revenue_last_year - 1.0) * 100
                                ELSE NULL
                            END as val_cumulative_revenue_yoy
                        FROM Refined
                    )
                    UPDATE monthly_revenue as mr
                    SET
                        revenue_last_year = f.val_revenue_last_year,
                        cumulative_revenue = f.val_cumulative_revenue,
                        cumulative_revenue_last_year = f.val_cumulative_revenue_last_year,
                        mom = f.val_mom,
                        yoy = f.val_yoy,
                        cumulative_revenue_yoy = f.val_cumulative_revenue_yoy
                    FROM Final f
                    WHERE mr.code = f.code
                      AND mr.year = f.year
                      AND mr.month = f.month
                      AND (
                           mr.revenue_last_year IS NOT f.val_revenue_last_year
                        OR mr.cumulative_revenue IS NOT f.val_cumulative_revenue
                        OR mr.cumulative_revenue_last_year IS NOT f.val_cumulative_revenue_last_year
                        OR mr.mom IS NOT f.val_mom
                        OR mr.yoy IS NOT f.val_yoy
                        OR mr.cumulative_revenue_yoy IS NOT f.val_cumulative_revenue_yoy
                      );
                    """

                cursor = conn.cursor()

                # execute
                cursor.execute(update_query)

            except sqlite3.OperationalError:
                print('Warning: SQLite incremental updateing failed, try to use pandas')
                print('         (it will take a while)')

                # fallback to use pandas
                df = pd.read_sql_query('SELECT * FROM monthly_revenue', conn)

                if df.empty:
                    return

                df.sort_values(by=['code', 'year', 'month'], inplace=True)

                # calculate derived fields
                # fmt: off
                df['revenue_last_year'] = df.groupby('code')['revenue'].shift(12)
                df['cumulative_revenue'] = df.groupby(['code', 'year'])['revenue'].cumsum()
                df['cumulative_revenue_last_year'] = df.groupby('code')['cumulative_revenue'].shift(12)
                df['mom'] = df.groupby('code')['revenue'].pct_change(periods=1) * 100
                df['yoy'] = df.groupby('code')['revenue'].pct_change(periods=12) * 100
                df['cumulative_revenue_yoy'] = (df['cumulative_revenue'] / df['cumulative_revenue_last_year'] - 1) * 100
                # fmt: on

                # prepare SQL
                update_query = """
                    UPDATE monthly_revenue
                    SET revenue_last_year = ?,
                        cumulative_revenue = ?,
                        cumulative_revenue_last_year = ?,
                        mom = ?,
                        yoy = ?,
                        cumulative_revenue_yoy = ?
                    WHERE code = ? AND year = ? AND month = ?
                    """

                cols = [
                    'revenue_last_year',
                    'cumulative_revenue',
                    'cumulative_revenue_last_year',
                    'mom',
                    'yoy',
                    'cumulative_revenue_yoy',
                    'code',
                    'year',
                    'month',
                ]

                # replace infinite values and NaN to None
                df_update = df[cols].replace(
                    {np.inf: None, -np.inf: None, np.nan: None}
                )

                update_data = list(df_update.itertuples(index=False, name=None))

                cursor = conn.cursor()

                # update data
                cursor.executemany(update_query, update_data)

            conn.commit()

    def get_revenue_by_code(self, stock_code, start_date='2013-01-01', end_date=None):
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
            df = pd.read_sql_query(
                """
                SELECT *
                FROM monthly_revenue
                WHERE code = ?
                  AND (year * 100 + month) BETWEEN ? AND ?
                ORDER BY year, month
                """,
                conn,
                params=(stock_code, start_period, end_period),
            )

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

            # schema content
            schema_content = """
                    code TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    quarter INTEGER NOT NULL,
                    -- balance
                    curr_assets INTEGER,
                    non_curr_assets INTEGER,
                    total_assets INTEGER,
                    curr_liabs INTEGER,
                    non_curr_liabs INTEGER,
                    total_liabs INTEGER,
                    total_equity INTEGER,
                    book_value REAL,
                    -- more balance
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
                    -- income
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
                    -- cash
                    opr_cash_flow INTEGER,
                    inv_cash_flow INTEGER,
                    fin_cash_flow INTEGER,
                    cash_equiv INTEGER,
                    divs_paid INTEGER,
                    --
                    PRIMARY KEY (code, year, quarter),
                    FOREIGN KEY (code) REFERENCES stock_list (code)
            """

            # create tables
            for table_name in ['financial_core', 'financial_ytd']:
                cursor.execute(
                    f'CREATE TABLE IF NOT EXISTS {table_name} ({schema_content})'
                )

            conn.commit()

        self.financial_core_table_initialized = True

    def import_quarterly_reports_csv_to_database(
        self,
        csv_folder='storage/quarterly',
        file_prefix='financial_reports',
        is_year_to_date=False,
        col_mapping=None,
        only_ci=True,
    ):
        """Import financial reports from CSV to database

        Args:
            csv_folder (str): Path to the folder containing CSV files
            file_prefix (str): Prefix of CSV files, e.g., 'financial_reports' in 'financial_reports_2025Q1.csv'
            is_year_to_date (bool): imported is cumulative Year-to-Date (YTD) data (True) or periodic data (False)
            col_mapping (dict): Mapping from CSV column headers to database
            only_ci (bool): Only import 'ci' (common industry) sector (True) or all industry sectors (False)

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_financial_core_table()

        if not os.path.isdir(csv_folder):
            raise FileNotFoundError(f'CSV folder not found: {csv_folder}')

        # pick target table
        to_table = 'financial_ytd' if is_year_to_date else 'financial_core'

        total_imported_records = 0
        last_mod_time = None  # track latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        # NOTE: '__{to_table}_{file_prefix}' is not a real table name, just for tracking the
        #       last updated time of different data sources for 'financial_core'
        updated_time = self.get_table_updated_time(f'__{to_table}_{file_prefix}')

        # define column mapping
        # NOTE: 1. below with '(i)' mark -> only disclosed in individual financial statements
        #       2. below with '(?)' mark -> only disclosed in some (3rd) data providers
        #          or get more fields to calculate
        #       3. others can find in summary reports
        default_mapping = {
            'Code': 'code',
            # balance
            '流動資產': 'curr_assets',
            '非流動資產': 'non_curr_assets',
            '資產總計': 'total_assets',
            '流動負債': 'curr_liabs',
            '非流動負債': 'non_curr_liabs',
            '負債總計': 'total_liabs',
            '權益總計': 'total_equity',
            '每股淨值': 'book_value',
            # more balance
            '應收帳款淨額': 'accts_receiv',  # (i)
            '應收帳款及票據': 'accts_notes_receiv',  # (?)
            '存貨': 'inventory',  # (i)
            '預付款項': 'prepaid',  # (i)
            '應付帳款': 'accts_pay',  # (i)
            '應付帳款及票據': 'accts_notes_pay',  # (?)
            '短期借款': 'st_loans',  # (i)
            '長期借款': 'lt_loans',  # (i)
            '應付公司債': 'bonds_pay',
            '保留盈餘': 'ret_earnings',
            # income
            '營業收入': 'opr_revenue',
            '營業成本': 'opr_costs',
            '營業毛利': 'gross_profit',
            '營業費用': 'opr_expenses',
            '營業利益': 'opr_profit',
            '營業外收入及支出': 'non_opr_income',
            '稅前淨利': 'pre_tax_income',
            '所得稅費用': 'income_tax',
            '本期淨利': 'net_income',
            '每股盈餘': 'eps',
            # cash
            '營業活動之淨現金流入': 'opr_cash_flow',
            '投資活動之淨現金流入': 'inv_cash_flow',
            '籌資活動之淨現金流入': 'fin_cash_flow',
            '期末現金及約當現金': 'cash_equiv',
            '發放現金股利': 'divs_paid',  # TODO: need to check
        }

        if col_mapping is None:
            col_mapping = default_mapping

        with self.get_connection() as conn:
            for file in files:
                # avoiding special character in file_prefix
                pattern = re.compile(rf'{re.escape(file_prefix)}_(\d{{4}})Q(\d)\.csv')
                match = pattern.search(file)
                # or
                # match = re.search(rf'{file_prefix}_(\d{{4}})Q(\d)\.csv', file)
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
                    print(f'Error: Failed reading: {e}')

                    continue

                if only_ci:
                    if 'Sector' not in df.columns:
                        print('Warning: No industry sector found, will import all rows')

                    else:
                        valid_sectors = {'basi', 'bd', 'ci', 'fh', 'ins', 'mim'}

                        # check for unknown sectors
                        unknown_mask = ~df['Sector'].isin(valid_sectors)

                        if unknown_mask.any():
                            for _, row in df[unknown_mask].iterrows():
                                code_val = row.get('Code', 'Unknown')
                                sector_val = row['Sector']
                                print(
                                    f'Warning: Unknown industry sector "{sector_val}" for {code_val}, will remove it'
                                )

                        # filter: only keep 'ci'
                        df = df[df['Sector'] == 'ci']

                # add new columns
                df['year'] = year
                df['quarter'] = quarter

                # build rename and need columns (based on mapping)
                rename_dict = {}
                use_cols = ['year', 'quarter']

                for csv_col, db_col in col_mapping.items():
                    if csv_col in df.columns:
                        rename_dict[csv_col] = db_col

                    use_cols.append(db_col)

                # rename columns
                df.rename(columns=rename_dict, inplace=True)

                # available columns
                avail_cols = [c for c in df.columns if c in use_cols]

                # check for mandatory columns
                # (based on table schema NOT NULL constraints)
                mandatory_cols = [
                    'code',
                    # 'year', <- no need to check
                    # 'quarter', <- no need to check
                ]
                missing_cols = [c for c in mandatory_cols if c not in avail_cols]

                if missing_cols:
                    print(f'Error: Missing mandatory columns {missing_cols}')

                    continue

                # keep only relevant columns
                df = df[avail_cols]

                # remove rows with empty code
                df.dropna(subset='code', inplace=True)

                # ensure 'code' in string format
                df['code'] = df['code'].astype(str)

                # replace NaNs with None for SQLite compatibility
                df = df.where(pd.notnull(df), None)

                # prepare SQL
                columns = ', '.join(avail_cols)
                placeholders = ', '.join(['?'] * len(avail_cols))

                # update part: exclude code, year, quarter from SET
                update_cols = [
                    c for c in avail_cols if c not in ('code', 'year', 'quarter')
                ]

                if not update_cols:
                    # insert data
                    sql = f"""
                        INSERT OR IGNORE INTO {to_table} ({columns})
                        VALUES ({placeholders})
                        """
                else:
                    update_assignments = ', '.join(
                        [f'{col}=excluded.{col}' for col in update_cols]
                    )

                    # upsert data
                    sql = f"""
                        INSERT INTO {to_table} ({columns})
                        VALUES ({placeholders})
                        ON CONFLICT(code, year, quarter) DO UPDATE SET
                        {update_assignments}
                        """

                data = df.values.tolist()

                cursor = conn.cursor()

                # insert or upsert data
                cursor.executemany(sql, data)

                total_imported_records += len(df)

                # update last_mod_time if file is newer
                if last_mod_time is None or csv_mod_time > last_mod_time:
                    last_mod_time = csv_mod_time

            conn.commit()

        # update table time
        if last_mod_time:
            self.set_table_updated_time(f'__{to_table}_{file_prefix}', last_mod_time)

            self.update_table_time(to_table, last_mod_time)

        return total_imported_records

    def calc_financial_core_from_ytd(self):
        """Calculate single quarter (Period) data from YTD data and update financial_core"""
        # flow columns (need subtraction: Q2 = YTD_Q2 - YTD_Q1)
        # data is Year-to-Date (YTD) can be split to single quarter
        flow_cols = [
            # income
            'opr_revenue',
            'opr_costs',
            'gross_profit',
            'opr_expenses',
            'opr_profit',
            'non_opr_income',
            'pre_tax_income',
            'income_tax',
            'net_income',
            'eps',
            # cash
            'opr_cash_flow',
            'inv_cash_flow',
            'fin_cash_flow',
            # 'divs_paid', TODO
        ]

        # stock columns (snapshot: Q2 = YTD_Q2)
        # data is current state (regardless of period)
        stock_cols = [
            # balance
            'curr_assets',
            'non_curr_assets',
            'total_assets',
            'curr_liabs',
            'non_curr_liabs',
            'total_liabs',
            'total_equity',
            'book_value',
            # more balance
            'accts_receiv',
            'accts_notes_receiv',
            'inventory',
            'prepaid',
            'accts_pay',
            'accts_notes_pay',
            'st_loans',
            'lt_loans',
            'bonds_pay',
            'ret_earnings',
            # cash
            'cash_equiv',
            'divs_paid',  # TODO: tbd
        ]

        with self.get_connection() as conn:
            print('Reading financial_ytd...')
            try:
                # read all YTD data
                df_ytd = pd.read_sql_query(
                    'SELECT * FROM financial_ytd ORDER BY code, year, quarter', conn
                )
            except Exception as e:
                print(f'Error reading financial_ytd: {e}')
                return

            if df_ytd.empty:
                print('No YTD data found.')
                return

            print(f'Processing {len(df_ytd)} YTD records...')

            records_to_upsert = []

            # group by code and year to process each year sequence
            # (sort_values is redundant if SQL ordered, but safe)
            groups = df_ytd.groupby(['code', 'year'])

            for (code, year), group in groups:
                # index by quarter for easy access
                group = group.set_index('quarter')
                quarters = sorted(group.index.tolist())

                for q in quarters:
                    if q == 1:
                        # Q1: direct copy (Core = YTD)
                        row = group.loc[q].to_dict()

                        # prepare record
                        # (filtering relevant columns to avoid extra fields if any)
                        record = {
                            'code': code,
                            'year': year,
                            'quarter': 1,
                        }
                        for col in flow_cols + stock_cols:
                            record[col] = row.get(col)

                        records_to_upsert.append(record)

                    else:
                        # Q2, Q3, Q4: need subtraction
                        prev_q = q - 1

                        # check 1: previous quarter record must exist
                        if prev_q not in group.index:
                            print(
                                f'[{code} {year}] Missing Q{prev_q} YTD data '
                                f'when processing Q{q}. Skipping rest of year.'
                            )
                            break

                        curr_row = group.loc[q]
                        prev_row = group.loc[prev_q]

                        # check 2: previous quarter flow columns must have values
                        valid_prev = True
                        for col in flow_cols:
                            if pd.isna(prev_row.get(col)):
                                print(
                                    f'[{code} {year}] Q{prev_q} YTD has missing '
                                    f'value for "{col}". Skipping rest of year.'
                                )
                                valid_prev = False
                                break

                        if not valid_prev:
                            break

                        # calculate
                        record = {
                            'code': code,
                            'year': year,
                            'quarter': q,
                        }

                        # stock cols: copy current
                        for col in stock_cols:
                            record[col] = curr_row.get(col)

                        # flow cols: current - previous
                        for col in flow_cols:
                            val_curr = curr_row.get(col)
                            val_prev = prev_row.get(col)

                            if pd.isna(val_curr) or pd.isna(val_prev):
                                record[col] = None
                            else:
                                record[col] = val_curr - val_prev

                        records_to_upsert.append(record)

            if not records_to_upsert:
                print('No records calculated.')
                return

            print(f'Upserting {len(records_to_upsert)} records to financial_core...')

            # create DataFrame
            df_core = pd.DataFrame(records_to_upsert)

            # prepare SQL for UPSERT
            columns = ', '.join(df_core.columns)
            placeholders = ', '.join(['?'] * len(df_core.columns))

            # exclude PK from UPDATE set
            update_cols = [
                c for c in df_core.columns if c not in ('code', 'year', 'quarter')
            ]
            update_assignments = ', '.join(
                [f'{col}=excluded.{col}' for col in update_cols]
            )

            sql = f"""
                INSERT INTO financial_core ({columns})
                VALUES ({placeholders})
                ON CONFLICT(code, year, quarter) DO UPDATE SET
                {update_assignments}
            """

            # handle None/NaN
            data = df_core.where(pd.notnull(df_core), None).values.tolist()

            cursor = conn.cursor()

            cursor.executemany(sql, data)

            conn.commit()

    def get_financial_by_code(
        self, stock_code, start_date='2013-01-01', end_date=None, year_to_date=False
    ):
        """Get financial data for specific stock

        Args:
            stock_code (str): Stock code
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            year_to_date (bool): return cumulative Year-to-Date (YTD) data (True) or periodic data (False)

        Returns:
            pandas.DataFrame: Financial data
        """
        # convert date string to datetime
        start = parse_date_string(start_date)
        # get year, quarter parts
        start_year = start.year
        start_quarter = (start.month - 1) // 3 + 1

        # end year, quarter
        if end_date:
            end = parse_date_string(end_date)
        else:
            end = datetime.today()
        end_year = end.year
        end_quarter = (end.month - 1) // 3 + 1

        # convert to comparable period (YYYYQ)
        start_period = start_year * 10 + start_quarter
        end_period = end_year * 10 + end_quarter

        # pick target table
        from_table = 'financial_ytd' if year_to_date else 'financial_core'

        with self.get_connection() as conn:
            # retrieve data
            df = pd.read_sql_query(
                f"""
                SELECT *
                FROM {from_table}
                WHERE code = ?
                  AND (year * 10 + quarter) BETWEEN ? AND ?
                ORDER BY year, quarter
                """,
                conn,
                params=(stock_code, start_period, end_period),
            )

        return df

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
            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """)
            tables = [table[0] for table in cursor.fetchall()]

            # for stock list table
            stock_list = {}
            # 1. get total count
            cursor.execute("""
                SELECT COUNT(*)
                FROM stock_list
                """)
            stock_list['total_count'] = cursor.fetchone()[0]

            # 2. get market distribution
            cursor.execute("""
                SELECT market, COUNT(*)
                FROM stock_list
                GROUP BY market
                ORDER BY market
                """)
            stock_list['market_stats'] = dict(cursor.fetchall())

            # 3. get last update time from metadata
            stock_list['last_updated'] = self.get_table_updated_time('stock_list')  # <- datetime # fmt: skip

            # for daily prices table
            daily_prices = {}
            # 1. get total count
            cursor.execute("""
                SELECT COUNT(*)
                FROM daily_prices
                """)
            daily_prices['total_count'] = cursor.fetchone()[0]

            # 2. get min and max trade date
            cursor.execute("""
                SELECT MIN(trade_date), MAX(trade_date)
                FROM daily_prices
                """)
            result = cursor.fetchone()
            min_date = result[0] if result[0] is not None else None
            max_date = result[1] if result[1] is not None else None
            daily_prices['min_date'] = min_date
            daily_prices['max_date'] = max_date

            # 3. get last update time from metadata
            daily_prices['last_updated'] = self.get_table_updated_time('daily_prices')  # <- datetime # fmt: skip

            # for monthly revenue table
            monthly_revenue = {}
            # 1. get total count
            cursor.execute("""
                SELECT COUNT(*)
                FROM monthly_revenue
                """)
            monthly_revenue['total_count'] = cursor.fetchone()[0]

            # 2. get min and max year-month
            cursor.execute("""
                SELECT MIN(year * 100 + month), MAX(year * 100 + month)
                FROM monthly_revenue
                """)
            result = cursor.fetchone()
            min_ym = result[0]
            max_ym = result[1]
            monthly_revenue['min_year_month'] = (
                f'{min_ym // 100}-{min_ym % 100:02d}' if min_ym is not None else None
            )
            monthly_revenue['max_year_month'] = (
                f'{max_ym // 100}-{max_ym % 100:02d}' if max_ym is not None else None
            )

            # 3. get last update time from metadata
            monthly_revenue['last_updated'] = self.get_table_updated_time('monthly_revenue')  # <- datetime # fmt: skip

            # for financial_core table
            financial_core = {}
            # 1. get total count
            cursor.execute("""
                SELECT COUNT(*)
                FROM financial_core
                """)
            financial_core['total_count'] = cursor.fetchone()[0]

            # 2. get min and max year-quarter
            cursor.execute("""
                SELECT MIN(year * 10 + quarter), MAX(year * 10 + quarter)
                FROM financial_core
                """)
            result = cursor.fetchone()
            min_yq = result[0]
            max_yq = result[1]
            financial_core['min_year_quarter'] = (
                f'{min_yq // 10}-Q{min_yq % 10}' if min_yq is not None else None
            )
            financial_core['max_year_quarter'] = (
                f'{max_yq // 10}-Q{max_yq % 10}' if max_yq is not None else None
            )

            # 3. get last update time from metadata
            financial_core['last_updated'] = self.get_table_updated_time('financial_core')  # <- datetime # fmt: skip

        return {
            'database_path': self.db_path,
            'tables': tables,
            #
            'stock_list': stock_list,
            'daily_prices': daily_prices,
            'monthly_revenue': monthly_revenue,
            'financial_core': financial_core,
        }
