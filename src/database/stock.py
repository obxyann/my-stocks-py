import os
import re
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

# add parent directory for importing from sibling directory
# sys.path.append('..')
# then
from utils.ansiColors import Colors, use_color
from utils.ass import ensure_directory_exists, modification_time, parse_date_string


class StockDatabase:
    """Database manager for stock data using SQLite"""

    def __init__(self, db_path='storage/stock_data.db'):
        """Initialize database

        Args:
            db_path (str): Path to SQLite database file
        """
        self.metadata_table_initialized = False
        self.stocks_table_initialized = False
        self.daily_prices_table_initialized = False
        self.monthly_revenue_table_initialized = False
        self.financial_core_ytd_table_initialized = False
        self.financial_metrics_table_initialized = False

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

    ################
    # Stocks table #
    ################

    def ensure_stocks_table(self):
        """Create stocks table if not exists"""
        if self.stocks_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    industry TEXT,
                    security_type TEXT,
                    business_type TEXT
                )
                """)

            conn.commit()

        self.stocks_table_initialized = True

    def import_stock_list_csv_to_database(self, csv_path='storage/stock_list.csv'):
        """Import stock list from CSV to database

        Args:
            csv_path (str): Path to CSV file

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_stocks_table()

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f'CSV file not found: {csv_path}')

        # compare file modification time with table updated time
        csv_mod_time = datetime.fromtimestamp(modification_time(csv_path))

        updated_time = self.get_table_updated_time('stocks')

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
            'Type': 'security_type',
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
            ]
            missing_cols = [c for c in mandatory_cols if c not in avail_cols]

            if missing_cols:
                use_color(Colors.ERROR)
                print(f'Error: Missing mandatory columns {missing_cols}')
                use_color(Colors.RESET)

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

            # insert data
            sql = f"""
                INSERT INTO stocks ({columns}) 
                VALUES ({placeholders})
                """

            data = df.values.tolist()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # clear existing data
                cursor.execute('DELETE FROM stocks')

                cursor.executemany(sql, data)

                conn.commit()

                # update table time
                self.set_table_updated_time('stocks', csv_mod_time)

            return len(df)

        except Exception as e:
            use_color(Colors.ERROR)
            print(f'Error: {e}')
            use_color(Colors.RESET)

            return 0

    def get_stocks(self):
        """Get all stocks from database

        Returns:
            pandas.DataFrame: Stock list data
        """
        with self.get_connection() as conn:
            # read data
            df = pd.read_sql_query(
                """
                SELECT code, name, market, industry, security_type, business_type
                FROM stocks
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
                SELECT code, name, market, industry, security_type, business_type
                FROM stocks
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
                SELECT code, name, market, industry, security_type, business_type
                FROM stocks
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
                SELECT code, name, industry, security_type
                FROM stocks
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
                SELECT code, name, market
                FROM stocks
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
                    PRIMARY KEY (code, trade_date)
                    -- , FOREIGN KEY (code) REFERENCES stocks (code)
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
                    use_color(Colors.ERROR)
                    print(f'Error: Failed reading: {e}')
                    use_color(Colors.RESET)

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
                    use_color(Colors.ERROR)
                    print(f'Error: Missing mandatory columns {missing_cols}')
                    use_color(Colors.RESET)

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

                # insert or replace data
                sql = f"""
                    INSERT OR REPLACE INTO daily_prices ({columns})
                    VALUES ({placeholders})
                    """

                data = df.values.tolist()

                cursor = conn.cursor()

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
                    use_color(Colors.ERROR)
                    print(f'Error: Failed reading: {e}')
                    use_color(Colors.RESET)

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
                    use_color(Colors.ERROR)
                    print(f'Error: Missing mandatory columns {missing_cols}')
                    use_color(Colors.RESET)

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

                # insert or replace data
                sql = f"""
                    INSERT OR REPLACE INTO daily_prices ({columns})
                    VALUES ({placeholders})
                    """

                data = df.values.tolist()

                cursor = conn.cursor()

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
                    revenue_ly INTEGER,
                    revenue_ytd INTEGER,
                    revenue_ytd_ly INTEGER,
                    revenue_mom REAL,
                    revenue_yoy REAL,
                    revenue_ytd_yoy REAL,
                    --
                    revenue_ma3 REAL,
                    revenue_ma12 REAL,
                    revenue_ytd_yoy_ma3 REAL,
                    revenue_ytd_yoy_ma12 REAL,
                    --
                    PRIMARY KEY (code, year, month)
                    -- , FOREIGN KEY (code) REFERENCES stocks (code)
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
                    use_color(Colors.ERROR)
                    print(f'Error: Failed reading: {e}')
                    use_color(Colors.RESET)

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
                    use_color(Colors.ERROR)
                    print(f'Error: Missing mandatory columns {missing_cols}')
                    use_color(Colors.RESET)

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

                # insert or replace data
                sql = f"""
                    INSERT OR REPLACE INTO monthly_revenue ({columns}) 
                    VALUES ({placeholders})
                    """

                data = df.values.tolist()

                cursor = conn.cursor()

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
        # self.update_monthly_revenue()

        return total_imported_records

    def update_monthly_revenue(self):
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
                            -- revenue_ly (prev year, LAG 12 of revenue)
                            LAG(revenue, 12) OVER (
                                PARTITION BY code
                                ORDER BY year, month
                            ) as val_revenue_ly,
                            -- revenue_ytd (year-to-date, partition by code, year)
                            SUM(revenue) OVER (
                                PARTITION BY code, year
                                ORDER BY month
                            ) as val_revenue_ytd,
                            -- revenue_lm (prev month, LAG 1 of revenue) only for mom
                            LAG(revenue, 1) OVER (
                                PARTITION BY code
                                ORDER BY year, month
                            ) as val_revenue_lm
                        FROM monthly_revenue
                    ),
                    Refined AS (
                        SELECT
                            code,
                            year,
                            month,
                            revenue,
                            val_revenue_ly,
                            val_revenue_ytd,
                            -- revenue_ytd_ly (YTD prev year, LAG 12 of YTD)
                            LAG(val_revenue_ytd, 12) OVER (
                                PARTITION BY code
                                ORDER BY year, month
                            ) as val_revenue_ytd_ly,
                            val_revenue_lm
                        FROM Calculated
                    ),
                    Final AS (
                        SELECT
                            code,
                            year,
                            month,
                            val_revenue_ly,
                            val_revenue_ytd,
                            val_revenue_ytd_ly,
                            -- mom
                            CASE
                                WHEN val_revenue_lm IS NOT NULL AND val_revenue_lm != 0
                                THEN (revenue * 1.0 / val_revenue_lm - 1.0) * 100
                                ELSE NULL
                            END as val_revenue_mom,
                            -- yoy
                            CASE
                                WHEN val_revenue_ly IS NOT NULL AND val_revenue_ly != 0
                                THEN (revenue * 1.0 / val_revenue_ly - 1.0) * 100
                                ELSE NULL
                            END as val_revenue_yoy,
                            -- revenue_ytd_yoy
                            CASE
                                WHEN val_revenue_ytd_ly IS NOT NULL AND val_revenue_ytd_ly != 0
                                THEN (val_revenue_ytd * 1.0 / val_revenue_ytd_ly - 1.0) * 100
                                ELSE NULL
                            END as val_revenue_ytd_yoy
                        FROM Refined
                    )
                    UPDATE monthly_revenue as mr
                    SET
                        revenue_ly = f.val_revenue_ly,
                        revenue_ytd = f.val_revenue_ytd,
                        revenue_ytd_ly = f.val_revenue_ytd_ly,
                        revenue_mom = f.val_revenue_mom,
                        revenue_yoy = f.val_revenue_yoy,
                        revenue_ytd_yoy = f.val_revenue_ytd_yoy
                    FROM Final f
                    WHERE mr.code = f.code
                      AND mr.year = f.year
                      AND mr.month = f.month
                      AND (
                           mr.revenue_ly IS NOT f.val_revenue_ly
                        OR mr.revenue_ytd IS NOT f.val_revenue_ytd
                        OR mr.revenue_ytd_ly IS NOT f.val_revenue_ytd_ly
                        OR mr.revenue_mom IS NOT f.val_revenue_mom
                        OR mr.revenue_yoy IS NOT f.val_revenue_yoy
                        OR mr.revenue_ytd_yoy IS NOT f.val_revenue_ytd_yoy
                      );
                    """

                cursor = conn.cursor()

                # execute
                cursor.execute(update_query)

            except sqlite3.OperationalError:
                use_color(Colors.WARNING)
                print('Warning: SQLite incremental updateing failed, try to use pandas')
                print('         (it will take a while)')
                use_color(Colors.RESET)

                # fallback to use pandas
                df = pd.read_sql_query(
                    """
                    SELECT *
                    FROM monthly_revenue
                    """,
                    conn,
                )

                if df.empty:
                    return

                df.sort_values(by=['code', 'year', 'month'], inplace=True)

                # calculate derived fields
                # fmt: off
                df['revenue_ly'] = df.groupby('code')['revenue'].shift(12)
                df['revenue_ytd'] = df.groupby(['code', 'year'])['revenue'].cumsum()
                df['revenue_ytd_ly'] = df.groupby('code')['revenue_ytd'].shift(12)
                df['revenue_mom'] = df.groupby('code')['revenue'].pct_change(periods=1) * 100
                df['revenue_yoy'] = df.groupby('code')['revenue'].pct_change(periods=12) * 100
                df['revenue_ytd_yoy'] = (df['revenue_ytd'] / df['revenue_ytd_ly'] - 1) * 100
                # fmt: on

                # prepare SQL
                update_query = """
                    UPDATE monthly_revenue
                    SET revenue_ly = ?,
                        revenue_ytd = ?,
                        revenue_ytd_ly = ?,
                        revenue_mom = ?,
                        revenue_yoy = ?,
                        revenue_ytd_yoy = ?
                    WHERE code = ? AND year = ? AND month = ?
                    """

                cols = [
                    'revenue_ly',
                    'revenue_ytd',
                    'revenue_ytd_ly',
                    'revenue_mom',
                    'revenue_yoy',
                    'revenue_ytd_yoy',
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
        if self.financial_core_ytd_table_initialized:
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
                    -- balance details
                    accts_receiv INTEGER,
                    notes_receiv INTEGER,
                    accts_notes_receiv INTEGER,
                    inventory INTEGER,
                    prepaid INTEGER,
                    accts_pay INTEGER,
                    notes_pay INTEGER,
                    accts_notes_pay INTEGER,
                    st_loans INTEGER,
                    lt_liabs_due_1y INTEGER,
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
                    cash_equivs INTEGER,
                    divs_paid INTEGER,
                    --
                    PRIMARY KEY (code, year, quarter)
                    -- , FOREIGN KEY (code) REFERENCES stocks (code)
            """

            # create tables
            for table_name in ['financial_core', 'financial_ytd']:
                cursor.execute(
                    f'CREATE TABLE IF NOT EXISTS {table_name} ({schema_content})'
                )

            conn.commit()

        self.financial_core_ytd_table_initialized = True

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
            # balance details
            '應收帳款': 'accts_receiv',  # (i)
            '應收票據': 'notes_receiv',  # (i)
            '應收帳款及票據': 'accts_notes_receiv',  # (?)
            '存貨': 'inventory',  # (i)
            '預付款項': 'prepaid',  # (i)
            '應付帳款': 'accts_pay',  # (i)
            '應付票據': 'notes_pay',  # (i)
            '應付帳款及票據': 'accts_notes_pay',  # (?)
            '短期借款': 'st_loans',  # (i)
            '一年內到期長期負債': 'lt_liabs_due_1y',  # (i)
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
            '期末現金及約當現金': 'cash_equivs',
            '配發股利': 'divs_paid',
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
                    use_color(Colors.ERROR)
                    print(f'Error: Failed reading: {e}')
                    use_color(Colors.RESET)

                    continue

                if only_ci:
                    if 'Sector' not in df.columns:
                        use_color(Colors.WARNING)
                        print('Warning: No industry sector found, will import all rows')
                        use_color(Colors.RESET)
                    else:
                        valid_sectors = {'basi', 'bd', 'ci', 'fh', 'ins', 'mim'}

                        # check for unknown sectors
                        unknown_mask = ~df['Sector'].isin(valid_sectors)

                        if unknown_mask.any():
                            for _, row in df[unknown_mask].iterrows():
                                code_val = row.get('Code', 'Unknown')
                                sector_val = row['Sector']

                                use_color(Colors.WARNING)
                                print(f'Warning: Unknown industry sector "{sector_val}" for {code_val}, will remove it')  # fmt: skip
                                use_color(Colors.RESET)

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
                    use_color(Colors.ERROR)
                    print(f'Error: Missing mandatory columns {missing_cols}')
                    use_color(Colors.RESET)

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

    def verify_financial_data(self, df, warning_cols=None):
        """Verify financial reports for missing quarters or missing values

        Args:
            df (pandas.DataFrame): Financial data
            warning_cols (list, optional): Columns to check for missing values
        """
        if warning_cols is None:
            warning_cols = []

        for code, group in df.groupby('code'):
            # 1. find first and last year, quarter
            # (df is already sorted by code, year, quarter)
            start_year = group['year'].iloc[0]
            start_q = group['quarter'].iloc[0]
            end_year = group['year'].iloc[-1]
            end_q = group['quarter'].iloc[-1]

            # use a lookup set and indexed group for efficiency
            existing_periods = set(zip(group['year'], group['quarter']))

            group_indexed = group.set_index(['year', 'quarter'])

            # 2. check for missing year, quarter data in the range
            year, q = start_year, start_q

            warning_code = False  # to control layout of warning messages

            while (year < end_year) or (year == end_year and q <= end_q):
                if (year, q) not in existing_periods:
                    if not warning_code:
                        print(f'Warning: [{code}] {start_year}-Q{start_q} ~ {end_year}-Q{end_q}')  # fmt: skip

                        warning_code = True

                    # append (H1) to Q3 or (A) to Q4
                    # (NOTE: q == 2 is H1, q == 4 is Annual)
                    n = ' (H1)' if q == 2 else ' (A)' if q == 4 else ''

                    use_color(Colors.ERROR if q == 4 else Colors.WARNING)
                    print(f'         {year}-Q{q}{n} has no data')
                    use_color(Colors.RESET)
                else:
                    # 3. verify warning_cols for missing values
                    row = group_indexed.loc[(year, q)]

                    for col in warning_cols:
                        if pd.isna(row[col]):
                            if not warning_code:
                                print(f'Warning: [{code}] {start_year}-Q{start_q} ~ {end_year}-Q{end_q}')  # fmt: skip

                                warning_code = True

                            # append (H1) to Q3 or (A) to Q4
                            n = ' (H1)' if q == 2 else ' (A)' if q == 4 else ''

                            use_color(Colors.WARNING)
                            print(f'         {year}-Q{q}{n} missing "{col}"')
                            use_color(Colors.RESET)

                # increment year, quarter
                q += 1
                if q > 4:
                    q = 1
                    year += 1

    def update_financial_core_from_ytd(self, verify_data=True):
        """Update financial core data from Year-to-Date (YTD) data

        This will update 'financial_core' (single quarter data) table by calculating
        quarterly differences from the cumulative 'financial_ytd' table.

        Args:
            verify_data (bool): Whether to verify YTD data for missing quarters or missing values
        """
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
            'divs_paid',
        ]

        # exclude warning these columns in flow_cols (for missing values)
        # data not ready in summary reports
        no_warning_cols = [
            'divs_paid',
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
            # balance details
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
            'cash_equivs',
        ]

        with self.get_connection() as conn:
            print('Reading YTD data...')

            try:
                # read all YTD data
                df_ytd = pd.read_sql_query(
                    """
                    SELECT *
                    FROM financial_ytd
                    ORDER BY code, year, quarter
                    """,
                    conn,
                )
            except Exception as e:
                use_color(Colors.ERROR)
                print(f'Error: {e}')
                use_color(Colors.RESET)

                return

            if df_ytd.empty:
                use_color(Colors.WARNING)
                print('Warning: No data found')
                use_color(Colors.RESET)
                return

            if verify_data:
                print('Verifying data...')

                # define warning columns
                warning_cols = [c for c in flow_cols if c not in no_warning_cols]

                self.verify_financial_data(df_ytd, warning_cols)

            print(f'Processing {len(df_ytd)} records...')

            records_to_upsert = []

            # group by code and year to process each year sequence
            # (sort_values is redundant if SQL ordered, but safe)
            groups = df_ytd.groupby(['code', 'year'])

            for (code, year), group in groups:
                # index by quarter for easy access
                group = group.set_index('quarter')

                quarters = sorted(group.index.tolist())

                for q in quarters:
                    curr_row = group.loc[q].to_dict()

                    if q == 1:
                        # Q1: direct copy (Core = YTD)
                        # curr_row = group.loc[q].to_dict()

                        # prepare record
                        # (filtering relevant columns to avoid extra fields if any)
                        record = {
                            'code': code,
                            'year': year,
                            'quarter': 1,
                        }
                        for col in flow_cols + stock_cols:
                            record[col] = curr_row.get(col)

                        records_to_upsert.append(record)

                    else:
                        # Q2, Q3, Q4: need subtraction
                        prev_q = q - 1

                        # check 3: previous quarter record must exist
                        if prev_q not in group.index:
                            # print(f'Warning: [{code}] {year}-Q{prev_q} YTD data missed')
                            continue

                        # curr_row = group.loc[q]
                        prev_row = group.loc[prev_q]

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
                use_color(Colors.WARNING)
                print('Warning: No records calculated')
                use_color(Colors.RESET)

                return

            print(f'Upserting {len(records_to_upsert)} records...')

            # create DataFrame
            df_core = pd.DataFrame(records_to_upsert)

            # prepare SQL
            columns = ', '.join(df_core.columns)
            placeholders = ', '.join(['?'] * len(df_core.columns))

            # exclude PK from UPDATE set
            update_cols = [
                c for c in df_core.columns if c not in ('code', 'year', 'quarter')
            ]
            update_assignments = ', '.join(
                [f'{col}=excluded.{col}' for col in update_cols]
            )

            # upset data
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

    ###########################
    # Financial Metrics table #
    ###########################

    def ensure_financial_metrics_table(self):
        """Create financial_metric table if not exists"""
        if self.financial_metrics_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_metrics (
                    code TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    quarter INTEGER NOT NULL,
                    --
                    free_cash_flow INTEGER,
                    days_inventory_outstd REAL,
                    days_sales_outstd REAL,
                    days_pay_outstd REAL,
                    ccc REAL,
                    -- 
                    curr_ratio REAL,
                    quick_ratio REAL,
                    debt_ratio REAL,
                    fin_debt_ratio REAL,
                    core_profit_ratio REAL,
                    asset_turn_ratio REAL,
                    -- 
                    gross_margin REAL,
                    opr_margin REAL,
                    pre_tax_margin REAL,
                    net_margin REAL,
                    roa REAL,
                    roe REAL,
                    annual_roa REAL,
                    annual_roe REAL,
                    rore REAL,
                    --
                    eps_qoq REAL,
                    eps_yoy REAL,
                    net_income_qoq REAL,
                    net_income_yoy REAL,
                    opr_cash_flow_qoq REAL,
                    opr_cash_flow_yoy REAL,
                    gross_margin_qoq REAL,
                    gross_margin_yoy REAL,
                    opr_margin_qoq REAL,
                    opr_margin_yoy REAL,
                    net_margin_qoq REAL,
                    net_margin_yoy REAL,
                    roe_qoq REAL,
                    roe_yoy REAL,
                    --
                    pe_ratio REAL,
                    pb_ratio REAL,
                    div_yield REAL,
                    annual_payout_ratio REAL,
                    irr REAL,
                    --
                    PRIMARY KEY (code, year, quarter)
                    -- , FOREIGN KEY (code) REFERENCES stocks (code)
                )
                """)

            conn.commit()

        self.financial_metrics_table_initialized = True

    def update_financial_metrics(self):
        """Calculate and update financial metrics from financial core data"""
        self.ensure_financial_metrics_table()

        print('Calculating financial metrics...')

        with self.get_connection() as conn:
            # read financial_core
            df = pd.read_sql_query(
                """
                SELECT * 
                FROM financial_core
                ORDER BY code, year, quarter
                """,
                conn,
            )

        if df.empty:
            use_color(Colors.WARNING)
            print('Warning: No financial core data found')
            use_color(Colors.RESET)
            return

        # constant: days in quarter (approx)
        DAYS = 365 / 4

        # --- metrics calculation ---
        # P.S. NaN will be propagated through the calculation

        # Free Cash Flow = Opr Cash Flow + Inv Cash Flow
        df['free_cash_flow'] = df['opr_cash_flow'] + df['inv_cash_flow']

        # Days Inventory = (Inventory / Opr Costs) * Days
        df['days_inventory_outstd'] = (df['inventory'] / df['opr_costs']) * DAYS

        # Days Sales (DSO) = (Receivables / Revenue) * Days
        receivables = df['accts_notes_receiv'].combine_first(
            df[['accts_receiv', 'notes_receiv']].sum(axis=1, min_count=1)
        )
        df['days_sales_outstd'] = (receivables / df['opr_revenue']) * DAYS

        # Days Payables (DPO) = (Payables / Opr Costs) * Days
        payables = df['accts_notes_pay'].combine_first(
            df[['accts_pay', 'notes_pay']].sum(axis=1, min_count=1)
        )
        df['days_pay_outstd'] = (payables / df['opr_costs']) * DAYS

        # CCC
        df['ccc'] = (df['days_inventory_outstd'] + df['days_sales_outstd'] - df['days_pay_outstd'])  # fmt: skip

        # Current Ratio
        df['curr_ratio'] = df['curr_assets'] / df['curr_liabs']

        # Quick Ratio = (Curr Assets - Inventory - Prepaid) / Curr Liabs
        quick_reduce = df[['inventory', 'prepaid']].sum(axis=1, min_count=1)
        df['quick_ratio'] = (df['curr_assets'] - quick_reduce) / df['curr_liabs']

        # Debt Ratio
        df['debt_ratio'] = df['total_liabs'] / df['total_assets']

        # Financial Debt Ratio = (Loans + Bonds) / Total Assets
        fin_debt_cols = [
            'st_loans',
            'notes_pay',
            'lt_liabs_due_1y',
            'lt_loans',
            'bonds_pay',
        ]
        fin_debt = df[fin_debt_cols].sum(axis=1, min_count=1)
        df['fin_debt_ratio'] = fin_debt / df['total_assets']

        # Core Profit Ratio = Opr Profit / Pre-tax Income
        df['core_profit_ratio'] = df['opr_profit'] / df['pre_tax_income']

        # Asset Turnover = Revenue / Total Assets
        df['asset_turn_ratio'] = df['opr_revenue'] / df['total_assets']

        # Margins
        df['gross_margin'] = df['gross_profit'] / df['opr_revenue']
        df['opr_margin'] = df['opr_profit'] / df['opr_revenue']
        df['pre_tax_margin'] = df['pre_tax_income'] / df['opr_revenue']
        df['net_margin'] = df['net_income'] / df['opr_revenue']

        # Returns
        df['roa'] = df['net_income'] / df['total_assets']
        df['roe'] = df['net_income'] / df['total_equity']

        # Annualized Returns
        # TODO: 4Q/4Y
        df['annual_roa'] = df['roa'] * 4
        df['annual_roe'] = df['roe'] * 4

        # ? RORE (Return on Retained Earnings)
        # TODO: 保留盈餘報酬率 = (稅後淨利 - 配發股利?) / 保留盈餘
        df['rore'] = df['net_income'] / df['ret_earnings']

        # ? Annual Payout Ratio = Divs Paid / Net Income
        # TODO: 年配息率 = 全年_現金股利 / 全年_EPS
        df['annual_payout_ratio'] = df['divs_paid'] / df['net_income']

        # placeholders for metrics requiring price or external data
        df['pe_ratio'] = None
        df['pb_ratio'] = None
        df['div_yield'] = None
        df['irr'] = None

        # --- growth (QoQ, YoY) calculation ---

        def calc_growth(series, shift_n):
            prev = series.shift(shift_n)
            # return (curr - prev) / abs(prev)
            return (series - prev) / prev.abs()

        # group by code
        g = df.groupby('code')

        # QoQ (1 quarter)
        # fmt: off
        df['eps_qoq'] = g['eps'].transform(lambda x: calc_growth(x, 1))
        df['net_income_qoq'] = g['net_income'].transform(lambda x: calc_growth(x, 1))
        df['opr_cash_flow_qoq'] = g['opr_cash_flow'].transform(lambda x: calc_growth(x, 1))
        df['gross_margin_qoq'] = g['gross_margin'].transform(lambda x: calc_growth(x, 1))
        df['opr_margin_qoq'] = g['opr_margin'].transform(lambda x: calc_growth(x, 1))
        df['net_margin_qoq'] = g['net_margin'].transform(lambda x: calc_growth(x, 1))
        df['roe_qoq'] = g['roe'].transform(lambda x: calc_growth(x, 1))
        # fmt: on

        # YoY (4 quarters)
        # fmt: off
        df['eps_yoy'] = g['eps'].transform(lambda x: calc_growth(x, 4))
        df['net_income_yoy'] = g['net_income'].transform(lambda x: calc_growth(x, 4))
        df['opr_cash_flow_yoy'] = g['opr_cash_flow'].transform(lambda x: calc_growth(x, 4))
        df['gross_margin_yoy'] = g['gross_margin'].transform(lambda x: calc_growth(x, 4))
        df['opr_margin_yoy'] = g['opr_margin'].transform(lambda x: calc_growth(x, 4))
        df['net_margin_yoy'] = g['net_margin'].transform(lambda x: calc_growth(x, 4))
        df['roe_yoy'] = g['roe'].transform(lambda x: calc_growth(x, 4))
        # fmt: on

        # --- upsert logic ---

        cols_map = [
            'code',
            'year',
            'quarter',
            'free_cash_flow',
            'days_inventory_outstd',
            'days_sales_outstd',
            'days_pay_outstd',
            'ccc',
            'curr_ratio',
            'quick_ratio',
            'debt_ratio',
            'fin_debt_ratio',
            'core_profit_ratio',
            'asset_turn_ratio',
            'gross_margin',
            'opr_margin',
            'pre_tax_margin',
            'net_margin',
            'roa',
            'roe',
            'annual_roa',
            'annual_roe',
            'rore',
            'eps_qoq',
            'eps_yoy',
            'net_income_qoq',
            'net_income_yoy',
            'opr_cash_flow_qoq',
            'opr_cash_flow_yoy',
            'gross_margin_qoq',
            'gross_margin_yoy',
            'opr_margin_qoq',
            'opr_margin_yoy',
            'net_margin_qoq',
            'net_margin_yoy',
            'roe_qoq',
            'roe_yoy',
            'pe_ratio',
            'pb_ratio',
            'div_yield',
            'annual_payout_ratio',
            'irr',
        ]

        # select relevant columns
        df_upsert = df[cols_map].copy()

        # clean all numeric columns for NaN/Inf
        num_cols = df_upsert.select_dtypes(include=[np.number]).columns

        df_upsert[num_cols] = df_upsert[num_cols].where(
            np.isfinite(df_upsert[num_cols]), np.nan
        )

        # convert NaN to None
        df_upsert = df_upsert.where(pd.notnull(df_upsert), None)

        print(f'Upserting {len(df_upsert)} metrics records...')

        with self.get_connection() as conn:
            # prepare SQL
            columns = ', '.join(cols_map)
            placeholders = ', '.join(['?'] * len(cols_map))

            # update exclusions
            update_cols = [c for c in cols_map if c not in ('code', 'year', 'quarter')]
            update_assignments = ', '.join(
                [f'{col}=excluded.{col}' for col in update_cols]
            )

            # upsert data
            sql = f"""
                INSERT INTO financial_metrics ({columns})
                VALUES ({placeholders})
                ON CONFLICT(code, year, quarter) DO UPDATE SET
                {update_assignments}
            """

            cursor = conn.cursor()

            cursor.executemany(sql, df_upsert.values.tolist())

            conn.commit()

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
            stocks = {}
            # 1. get total count
            cursor.execute("""
                SELECT COUNT(*)
                FROM stocks
                """)
            stocks['total_count'] = cursor.fetchone()[0]

            # 2. get market distribution
            cursor.execute("""
                SELECT market, COUNT(*)
                FROM stocks
                GROUP BY market
                ORDER BY market
                """)
            stocks['market_stats'] = dict(cursor.fetchall())

            # 3. get last update time from metadata
            stocks['last_updated'] = self.get_table_updated_time('stocks')  # <- datetime # fmt: skip

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
            'stocks': stocks,
            'daily_prices': daily_prices,
            'monthly_revenue': monthly_revenue,
            'financial_core': financial_core,
        }
