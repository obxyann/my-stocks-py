import sys
import os
from datetime import datetime

# add the parent directory for importing foo from sibling directory
# sys.path.append('..')
# then
from database.stock import StockDatabase
from openData.getStockList import get_stock_list

def initialize_database ():
    """Initialize database and import CSV data if needed"""
    try:
        # Initialize database
        db = StockDatabase()
        
        # TODO: validate...

        return db
        
    except Exception as error:
        print(f'Database initialization failed: {error}')
        raise

def test_database (db):
    print("\n=== Database Information ===")
    info = db.get_database_info()
    print(f'Database path: {info['database_path']}')
    print(f'Table list: {info['tables']}')
    print('')

    print(f'Total stocks: {info['total_stocks']}')
    print(f'Market distribution:')        
    for market, count in info['market_distribution'].items():
        print(f'  {market}: {count}')
    print(f'Last update: {info['stock_list_updated_at']}')

def test_stock_list (db):
    """Test various database operations"""
    try:     
        print("\n=== Sample Stock List (First 10) ===")
        stock_list = db.get_stock_list()
        print(stock_list.head(10))
        
        print("\n=== Search Example: '台積' ===")
        search_results = db.search_stocks('台積')
        print(search_results)
        
        print("\n=== TSE Market Stocks (First 5) ===")
        tse_stocks = db.get_stocks_by_market('tse')
        print(tse_stocks.head(5))
        
        print("\n=== Semiconductor Industry Stocks ===")
        semiconductor_stocks = db.get_stocks_by_industry('半導體業')
        if not semiconductor_stocks.empty:
            print(semiconductor_stocks.head(5))
        else:
            print("No semiconductor stocks found (industry name might be different)")
        
    except Exception as error:
        print(f'Database operations failed: {error}')
        raise

def test_monthly_revenue(db):
    """Test function for monthly revenue data"""
    # Test retrieving data
    print("\nRetrieving data for stock 2330...")

    df = db.get_revenue_by_id('2330', '2025-01')

    if not df.empty:
        print(df)
        # print(df.head())
        # print("...")
        # print(df.tail())
    else:
        print("No data found for stock 2330.")

def test ():
    """Main test function"""
    try:
        output_dir = 'storage'

        # Test 1: Download fresh data
        # print("=== Downloading fresh stock list data ===")
        # df = get_stock_list(refetch = True, data_dir = output_dir)
        # print(f"Downloaded {len(df)} stocks")
        
        # print('--')
        # print(df)
        # print('--')

        # Initialize database
        db = initialize_database()  

        # Test 2: Database operations
        test_database(db)

        # Test 3: Stock List
        print("\n=== Testing Stock List ===")
        test_stock_list(db)
   
        # Test 3: Monthly revenue
        print("\n=== Testing Monthly Revenue ===")
        test_monthly_revenue(db)

        print('\n=== All tests completed successfully! ===')

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    print('Goodbye!')

if __name__ == '__main__':
    test()
