import sqlite3
import pandas as pd
import sys
import os
from datetime import datetime

# add the parent directory for importing foo from sibling directory
# sys.path.append('..')
# then
from utils.ass import ensure_directory_exists, modification_time

class StockDatabase:
    """Database manager for stock data using SQLite"""

    def __init__ (self, db_path = 'storage/stock_data.db'):
        """Initialize database connection

        Args:
            db_path (str): Path to SQLite database file
        """
        ensure_directory_exists(db_path)

        self.db_path = db_path

    def get_connection (self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    ##################
    # metadata table #
    ##################

    def create_metadata_table(self):
        """Create metadata table to track table update times if it doesn't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    table_name TEXT PRIMARY KEY,
                    last_updated TIMESTAMP NOT NULL
                )
            ''')
            conn.commit()

    def update_table_timestamp(self, table_name, timestamp = None):
        """Update last_updated timestamp for specific table

        Args:
            timestamp (str): 'YYYY-MM-DD HH:MM:SS' ISO-8601 format
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create table if not exists
        self.create_metadata_table()

        # Update data to database
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (table_name, last_updated)
                VALUES (?, ?)
            ''', (table_name, timestamp))
            conn.commit()

    def get_last_update_time(self, table_name):
        """Get last update time for specific table

        Returns:
            str: Last updated time in 'YYYY-MM-DD HH:MM:SS' ISO-8601 format
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query('''
                SELECT last_updated
                FROM metadata
                WHERE table_name = ?
            ''', conn, params = (table_name,))

        return df['last_updated'][0] if not df.empty else None

    ####################
    # stock list table #
    ####################

    def create_stock_list_table(self):
        """Create stock_list table if it doesn't exist"""
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

    def import_stock_list_csv_to_database(self, csv_path):
        """Import stock list from CSV file to database

        Args:
            csv_path (str): Path to CSV file

        Returns:
            int: Number of records imported
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Read CSV file
        # df = pd.read_csv(csv_path, na_filter = False) # dont detect missing value markers (empty strings and the value of na_values)
        df = pd.read_csv(csv_path)

        # Create table if not exists
        self.create_stock_list_table()

        # Import data to database
        with self.get_connection() as conn:
            # Clear existing data
            cursor = conn.cursor()
            cursor.execute('DELETE FROM stock_list')

            # Insert new data
            df.to_sql('stock_list', conn, if_exists='append', index = False)

            # Update timestamps in metadata
            timestamp = datetime.fromtimestamp(modification_time(csv_path)).strftime('%Y-%m-%d %H:%M:%S')

            self.update_table_timestamp('stock_list', timestamp)

            conn.commit()

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
        """Get specific stock by stock_id

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
        """Search stocks by name or stock_id

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
            market (str): Market code (tse, otc, esb)

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

    def get_database_info(self):
        """Get database information

        Returns:
            dict: Database statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get total count
            cursor.execute('SELECT COUNT(*) FROM stock_list')
            total_count = cursor.fetchone()[0]

            # Get market distribution
            cursor.execute('''
                SELECT market, COUNT(*)
                FROM stock_list
                GROUP BY market
                ORDER BY market
            ''')
            market_stats = dict(cursor.fetchall())

            # Get last update time from metadata
            updated_at = self.get_last_update_time('stock_list')

        return {
            'database_path': self.db_path,

            # stock list table
            'total_stocks': total_count,
            'market_distribution': market_stats,
            'updated_at': updated_at
        }
