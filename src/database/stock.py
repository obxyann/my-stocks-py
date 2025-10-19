import sys
import sqlite3
from datetime import datetime
import os
import pandas as pd
import re
import numpy as np

# add the parent directory for importing foo from sibling directory
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
        self.monthly_revenue_table_initialized = False

        ensure_directory_exists(db_path)

        self.db_path = db_path

    def get_connection (self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    ##################
    # Metadata table #
    ##################

    def ensure_metadata_table(self):
        """Create metadata table to track table update times if it doesn't exist"""
        if self.metadata_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    table_name TEXT PRIMARY KEY,
                    last_updated TIMESTAMP NOT NULL
                )
            ''')
            conn.commit()

        self.metadata_table_initialized = True

    def update_table_timestamp(self, table_name, timestamp = None):
        """Update last updated timestamp for specific table

        Creates metadata table if missing. Uses current time if no timestamp provided.

        Args:
            table_name (str): Name of the table to update
            timestamp (str): Optional timestamp in 'YYYY-MM-DD HH:MM:SS' ISO-8601 format
        """
        # create table if not exists
        self.ensure_metadata_table()

        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # update data to database
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (table_name, last_updated)
                VALUES (?, ?)
            ''', (table_name, timestamp))
            conn.commit()

    def get_last_update_timestamp(self, table_name):
        """Get last update timestamp for specific table

        Args:
            table_name (str): Name of the table to query

        Returns:
            str: Last updated timestamp in 'YYYY-MM-DD HH:MM:SS' ISO-8601 format
                 or None if not found
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query('''
                SELECT last_updated
                FROM metadata
                WHERE table_name = ?
            ''', conn, params = (table_name,))

        return df['last_updated'][0] if not df.empty else None

    ####################
    # Stock List table #
    ####################

    def ensure_stock_list_table(self):
        """Create stock_list table if it doesn't exist"""
        if self.stock_list_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_list (
                    stock_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    industry TEXT,
                    type TEXT NOT NULL
                )
            ''')
            conn.commit()

        self.stock_list_table_initialized = True

    def import_stock_list_csv_to_database(self, csv_path = 'storage/stock_list.csv'):
        """Import stock list from CSV file to database

        Args:
            csv_path (str): Path to CSV file

        Returns:
            int: Number of records imported
        """
        # create table if not exists
        self.ensure_stock_list_table()

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # read CSV file
        df = pd.read_csv(csv_path)
        # or
        # dont detect missing value markers (empty strings and the value of na_values)
        # df = pd.read_csv(csv_path, na_filter = False)

        # convert 'stock_id' to string to match the database schema
        # df['stock_id'] = df['stock_id'].astype(str)

        # import data to database
        with self.get_connection() as conn:
            # clear existing data
            cursor = conn.cursor()
            cursor.execute('DELETE FROM stock_list')

            # insert new data
            df.to_sql('stock_list', conn, if_exists = 'append', index = False)

            conn.commit()

            # update timestamp in metadata
            timestamp = datetime.fromtimestamp(modification_time(csv_path)).strftime('%Y-%m-%d %H:%M:%S')

            self.update_table_timestamp('stock_list', timestamp)

        return len(df)

    def get_stock_list(self):
        """Get all stocks from database

        Returns:
            pandas.DataFrame: Stock list data
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query('''
                SELECT stock_id, name, market, industry, type
                FROM stock_list
                ORDER BY stock_id
            ''', conn)

        return df

    def get_stock_by_id(self, stock_id):
        """Get specific stock by stock id

        Args:
            stock_id (str): Stock id

        Returns:
            pandas.DataFrame: Stock data
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query('''
                SELECT stock_id, name, market, industry, type
                FROM stock_list
                WHERE stock_id = ?
            ''', conn, params = (stock_id,))

        return df

    def search_stocks(self, keyword):
        """Search stocks by name or stock id

        Args:
            keyword (str): Search keyword

        Returns:
            pandas.DataFrame: Matching stocks
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query('''
                SELECT stock_id, name, market, industry, type
                FROM stock_list
                WHERE stock_id LIKE ? OR name LIKE ?
                ORDER BY stock_id
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
            df = pd.read_sql_query('''
                SELECT stock_id, name, market, industry, type
                FROM stock_list
                WHERE market = ?
                ORDER BY stock_id
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
            df = pd.read_sql_query('''
                SELECT stock_id, name, market, industry, type
                FROM stock_list
                WHERE industry = ?
                ORDER BY stock_id
            ''', conn, params = (industry,))

        return df

    #########################
    # Monthly Revenue table #
    #########################

    def ensure_monthly_revenue_table(self):
        """Create monthly_revenue table if it doesn't exist"""
        if self.monthly_revenue_table_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monthly_revenue (
                    stock_id TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    revenue INTEGER,
                    revenue_last_year INTEGER,
                    cumulative_revenue INTEGER,
                    cumulative_revenue_last_year INTEGER,
                    mom REAL,
                    yoy REAL,
                    cumulative_revenue_yoy REAL,
                    note TEXT,
                    PRIMARY KEY (stock_id, year, month),
                    FOREIGN KEY (stock_id) REFERENCES stock_list (stock_id)
                )
            ''')
            conn.commit()

        self.monthly_revenue_table_initialized = True

    def import_monthly_revenue_csv_to_database(self, csv_folder = 'storage/monthly'):
        """Import monthly revenue from CSV files to database

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
        last_mod_time = 0  # for tracking the latest modification time of all files

        files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

        with self.get_connection() as conn:
            for file in files:
                match = re.search(r'revenues_(\d{4})(\d{2})\.csv', file)
                if not match:
                    continue

                year, month = int(match.group(1)), int(match.group(2))

                csv_path = os.path.join(csv_folder, file)

                print(f'Importing {csv_path}')

                # read CSV file
                df = pd.read_csv(csv_path)

                df['year'] = year
                df['month'] = month

                # rename columns to match the database schema
                df.rename(columns = {'Stock_id': 'stock_id', 'Revenue': 'revenue', 'Note': 'note'}, inplace = True)

                # select and reorder columns for insertion
                df = df[['stock_id', 'year', 'month', 'revenue', 'note']]

                # convert 'stock_id' to string to match the database schema
                df['stock_id'] = df['stock_id'].astype(str)

                # insert or update data
                for _, row in df.iterrows():
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO monthly_revenue (stock_id, year, month, revenue, note)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (row['stock_id'], row['year'], row['month'], row['revenue'], row['note']))

                total_imported_records += len(df)

                mod_time = modification_time(csv_path)
                # update last_mod_time if this file is newer
                if (mod_time > last_mod_time):
                    last_mod_time = mod_time

            conn.commit()

        # update timestamp in metadata
        if last_mod_time:
            timestamp = datetime.fromtimestamp(last_mod_time).strftime('%Y-%m-%d %H:%M:%S')

            self.update_table_timestamp('monthly_revenue', timestamp)

        # update calculated fields after all data is imported
        # self.update_monthly_revenue_calculations()

        return total_imported_records

    def update_monthly_revenue_calculations(self):
        """Update calculated fields in the monthly_revenue table"""
        with self.get_connection() as conn:
            df = pd.read_sql_query('SELECT * FROM monthly_revenue', conn)

            if df.empty:
                return

            df.sort_values(by=['stock_id', 'year', 'month'], inplace=True)

            # calculate derived fields
            df['revenue_last_year'] = df.groupby('stock_id')['revenue'].transform(lambda x: x.shift(12))
            df['cumulative_revenue'] = df.groupby(['stock_id', 'year'])['revenue'].cumsum()
            df['cumulative_revenue_last_year'] = df.groupby('stock_id')['cumulative_revenue'].transform(lambda x: x.shift(12))
            df['mom'] = df.groupby('stock_id')['revenue'].pct_change(periods = 1) * 100
            df['yoy'] = df.groupby('stock_id')['revenue'].pct_change(periods = 12) * 100
            df['cumulative_revenue_yoy'] = (df['cumulative_revenue'] / df['cumulative_revenue_last_year'] - 1) * 100

            # replace infinite values with NaN
            df.replace([np.inf, -np.inf], np.nan, inplace=True)

            # update the database
            update_query = '''
                UPDATE monthly_revenue
                SET revenue_last_year = ?,
                    cumulative_revenue = ?,
                    cumulative_revenue_last_year = ?,
                    mom = ?,
                    yoy = ?,
                    cumulative_revenue_yoy = ?
                WHERE stock_id = ? AND year = ? AND month = ?
            '''

            update_data = [
                (
                    row['revenue_last_year'] if pd.notna(row['revenue_last_year']) else None,
                    row['cumulative_revenue'] if pd.notna(row['cumulative_revenue']) else None,
                    row['cumulative_revenue_last_year'] if pd.notna(row['cumulative_revenue_last_year']) else None,
                    row['mom'] if pd.notna(row['mom']) else None,
                    row['yoy'] if pd.notna(row['yoy']) else None,
                    row['cumulative_revenue_yoy'] if pd.notna(row['cumulative_revenue_yoy']) else None,
                    row['stock_id'],
                    row['year'],
                    row['month']
                )
                for _, row in df.iterrows()
            ]

            cursor = conn.cursor()
            cursor.executemany(update_query, update_data)
            conn.commit()

    def get_revenue_by_id(self, stock_id, start_date = '2013-01-01', end_date = None):
        # convert date string to datetime object
        start = parse_date_string(start_date)
        # and get the year, month parts
        start_year, start_month = start.year, start.month

        # end year, month
        if end_date:
            end = parse_date_string(end_date)
        else:
            end = datetime.today()
        end_year, end_month = end.year, end.month

        # convert to comparable period format (YYYYMM)
        start_period = start_year * 100 + start_month
        end_period = end_year * 100 + end_month

        with self.get_connection() as conn:
            df = pd.read_sql_query('''
                SELECT *
                FROM monthly_revenue
                WHERE stock_id = ?
                  AND (year * 100 + month) BETWEEN ? AND ?
                ORDER BY year, month
            ''', conn, params = (stock_id, start_period, end_period))

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

            # get all tables in the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [table[0] for table in cursor.fetchall()]

            # for stock list table
            stock_list = {}
            # 1. Get total count
            cursor.execute('SELECT COUNT(*) FROM stock_list')
            stock_list['total_count'] = cursor.fetchone()[0]

            # 2. Get market distribution
            cursor.execute('''
                SELECT market, COUNT(*)
                FROM stock_list
                GROUP BY market
                ORDER BY market
            ''')
            stock_list['market_stats'] = dict(cursor.fetchall())

            # 3. Get last update time from metadata
            stock_list['last_updated'] = self.get_last_update_timestamp('stock_list')

            # for monthly revenue table
            monthly_revenue = {}
            # 1. Get total count
            cursor.execute('SELECT COUNT(*) FROM monthly_revenue')
            monthly_revenue['total_count'] = cursor.fetchone()[0]

            # 2. Get min and max year-month
            cursor.execute('SELECT MIN(year * 100 + month), MAX(year * 100 + month) FROM monthly_revenue')
            min_max_result = cursor.fetchone()
            monthly_revenue['min_year_month'] = min_max_result[0] if min_max_result[0] is not None else None
            monthly_revenue['max_year_month'] = min_max_result[1] if min_max_result[1] is not None else None
            
            # 3. Get last update time from metadata
            monthly_revenue['last_updated'] = self.get_last_update_timestamp('monthly_revenue')

        return {
            'database_path': self.db_path,
            'tables': tables,

            'stock_list': stock_list,
            'monthly_revenue': monthly_revenue
        }
