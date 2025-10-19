#!/usr/bin/env python3
"""
Database management utility for stock data
"""

import sys
import os
import argparse

# add the parent directory for importing from sibling directory
sys.path.append('..')
# then
from database.stock import StockDatabase
from openData.getStockList import get_stock_list

def import_csv_to_db(csv_dir = None, db_path = None):
    """Import CSV data to database"""
    if csv_dir is None:
        csv_dir = 'storage'
    else:
        csv_dir = csv_dir.rstrip('/\\')

    try:
        db = StockDatabase(db_path) if db_path else StockDatabase()

        # import stock_list.csv
        csv_path = os.path.join(csv_dir, 'stock_list.csv')
        
        if not os.path.exists(csv_path):
            print(f'stock_list.csv not found: {csv_path}')
        else:
            print('Importing stock list from CSV to database...')
            count = db.import_stock_list_csv_to_database(csv_path)
            print(f'Successfully imported {count} records from stock_list.csv')
        
        # import revenues_{YYYYMM}.csv
        csv_folder = os.path.join(csv_dir, 'monthly')

        if not os.path.isdir(csv_folder):
            print(f'monthly folder not found: {csv_folder}')
        else:
            print('Importing monthly revenues from CSV to database...')
            count = db.import_monthly_revenue_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records from monthly/revenues_YYYYMM.csv')

            print('Calcatuting and updating monthly revenues in database...')
            db.update_monthly_revenue_calculations()
            print('Successfully')

        return True

    except Exception as e:
        print(f'Import failed: {e}')
        return False

def download_and_import(db_path = None):
    """Download fresh data and import to database"""
    try:
        # download fresh data
        print('Downloading fresh stock list...')
        df = get_stock_list(refetch=True, data_dir = 'storage')
        print(f'Downloaded {len(df)} stocks')
        
        # import to database
        print('Importing to database...')
        db = StockDatabase(db_path) if db_path else StockDatabase()
        count = db.import_stock_list_csv_to_database('storage/stock_list.csv')
        print(f'Successfully imported {count} records to database')
        
        return True
        
    except Exception as e:
        print(f'Download and import failed: {e}')
        return False

def show_db_info(db_path=None):
    """Show database information"""
    try:
        db = StockDatabase(db_path) if db_path else StockDatabase()
        
        info = db.get_database_info()
        
        print('=== Database Information ===')
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
            
        return True
        
    except Exception as e:
        print(f'Failed to get database info: {e}')
        return False

def search_stocks(keyword, db_path=None):
    """Search stocks by keyword"""
    try:
        db = StockDatabase(db_path) if db_path else StockDatabase()
        results = db.search_stocks(keyword)
        
        if results.empty:
            print(f'No stocks found for keyword: {keyword}')
        else:
            print(f'Found {len(results)} stocks matching "{keyword}":')
            print(results.to_string(index=False))
            
        return True
        
    except Exception as e:
        print(f'Search failed: {e}')
        return False

def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(description='Stock Database Manager')
    parser.add_argument('--db-path', help='Database file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import CSV to database')
    import_parser.add_argument('--from_folder', help='From folder')
    
    # download command
    subparsers.add_parser('download', help='Download fresh data and import')
    
    # info command
    subparsers.add_parser('info', help='Show database information')
    
    # search command
    search_parser = subparsers.add_parser('search', help='Search stocks')
    search_parser.add_argument('keyword', help='Search keyword')
    
    args = parser.parse_args()
    
    if args.command == 'import':
        import_csv_to_db(args.from_folder, args.db_path)
    elif args.command == 'download':
        download_and_import(args.db_path)
    elif args.command == 'info':
        show_db_info(args.db_path)
    elif args.command == 'search':
        search_stocks(args.keyword, args.db_path)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
