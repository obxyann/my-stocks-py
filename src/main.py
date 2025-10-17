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

def test_database_operations ():
    """Test various database operations"""
    try:
        # Initialize database
        db = initialize_database()
        
        print("\n=== Database Information ===")
        info = db.get_database_info()
        print(f'Database path: {info['database_path']}')
        print(f'Table list: {info['tables']}')
        print('');
        print('Stock List Table');
        print('----------------');
        print(f'Total stocks: {info['total_stocks']}')
        print(f'Market distribution:')        
        for market, count in info['market_distribution'].items():
            print(f'  {market}: {count}')
        print(f'Last update: {info['stock_list_updated_at']}')
        
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
        
        return db
        
    except Exception as error:
        print(f'Database operations failed: {error}')
        raise

def test ():
    """Main test function"""
    try:
        output_dir = 'storage'

        # Test 1: Traditional CSV approach (commented out)
        # df = get_stock_list(data_dir = output_dir)

        # Test 2: Download fresh data and import to database
        print("=== Downloading fresh stock list data ===")
        df = get_stock_list(refetch=False, data_dir=output_dir)
        print(f"Downloaded {len(df)} stocks")

        # Test 3: Database operations
        print("\n=== Testing Database Operations ===")
        db = test_database_operations()
        
        print('\n=== All tests completed successfully! ===')

        # print('--')
        # print(df)
        # print('--')

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    print('Goodbye!')

if __name__ == '__main__':
    test()
