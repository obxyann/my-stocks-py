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
from openData.getDailyPrices import fetch_last_daily_prices, check_last_daily_prices_exist
from openData.getMonthlyRevenues import fetch_hist_monthly_revenues

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
            print(f'File not found: {csv_path}')
        else:
            print('Importing stock list from CSV to database...')
            count = db.import_stock_list_csv_to_database(csv_path)
            print(f'Successfully imported {count} records from stock_list.csv')

        # import prices_{YYYYMMDD}.csv
        csv_folder = os.path.join(csv_dir, 'daily')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            print('Importing daily prices from CSV to database...')
            count = db.import_daily_prices_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records from daily/prices_YYYYMM.csv')

        # import revenues_{YYYYMM}.csv
        csv_folder = os.path.join(csv_dir, 'monthly')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            print('Importing monthly revenues from CSV to database...')
            count = db.import_monthly_revenue_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records from monthly/revenues_YYYYMM.csv')

            print('Calcatuting and updating monthly revenues in database...\n(long time)')
            db.update_monthly_revenue_calculations()
            print('Successfully')

        return True

    except Exception as e:
        print(f'Import failed: {e}')
        return False

def download(refetch = False, output_dir = None):
    """Download fresh data and import to database"""
    if refetch == True:
        action = 'Downloading fresh'
    else:
        action = 'Downloading'

    if output_dir is None:
        output_dir = 'storage'
    else:
        output_dir = csv_dir.rstrip('/\\')

    try:
        print(f'{action} stock list...')
        get_stock_list(refetch = refetch, data_dir = output_dir)
        print(f'Done')

        print(f'\n{action} daily prices revenues...')
        dest_dir = os.path.join(output_dir, 'daily')
        if not refetch and not check_last_daily_prices_exist(dest_dir):
            fetch_last_daily_prices(output_dir = dest_dir)
        print(f'Done')

        print(f'\n{action} monthly revenues...')
        dest_dir = os.path.join(output_dir, 'monthly')
        fetch_hist_monthly_revenues(refetch = refetch, start_date = '2013-01-01', output_dir = dest_dir)
        print(f'Done')
        
        return True
        
    except Exception as e:
        print(f'Download failed: {e}')
        return False

def show_db_info(db_path = None):
    """Show database information"""
    try:
        db = StockDatabase(db_path) if db_path else StockDatabase()
        
        info = db.get_database_info()
        
        print(f'Database path: {info['database_path']}')
        print(f'Tables: {info['tables']}')

        print(f'\nTotal stocks: {info['stock_list']['total_count']}')
        print(f'Market distribution:')
        for market, count in info['stock_list']['market_stats'].items():
            print(f'  {market}: {count}')
        print(f'Last updated: {info['stock_list']['last_updated']}')

        print(f'\nTotal monthly revenues: {info['monthly_revenue']['total_count']}')
        print(f'  min month: {info['monthly_revenue']['min_year_month']}')
        print(f'  max month: {info['monthly_revenue']['max_year_month']}')
        print(f'Last updated: {info['monthly_revenue']['last_updated']}')
            
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
    parser = argparse.ArgumentParser(description = 'Stock Database Manager')
    parser.add_argument('--db-path', help = 'database file path')
    
    subparsers = parser.add_subparsers(dest ='command', help = 'available commands')
    
    # import command
    import_parser = subparsers.add_parser('import', help = 'import CSV to database')
    import_parser.add_argument('--from_folder', help = 'read from folder')
    
    # download command
    download_parser = subparsers.add_parser('download', help = 'download data')
    download_parser.add_argument('--refetch', action = 'store_true', help = 'refetch data')
    download_parser.add_argument('--to_folder', help = 'write to folder')

    # info command
    subparsers.add_parser('info', help = 'show database information')
    
    # search command
    search_parser = subparsers.add_parser('search', help = 'search stocks')
    search_parser.add_argument('keyword', help = 'search keyword')
    
    args = parser.parse_args()
    
    if args.command == 'import':
        import_csv_to_db(args.from_folder, args.db_path)
    elif args.command == 'download':
        download(args.refetch, args.to_folder)
    elif args.command == 'info':
        show_db_info(args.db_path)
    elif args.command == 'search':
        search_stocks(args.keyword, args.db_path)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
