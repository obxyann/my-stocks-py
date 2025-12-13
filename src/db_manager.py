import argparse
import os
import sys

# add the parent directory for importing from sibling directory
sys.path.append('..')
# then
from database.stock import StockDatabase
from openData.getDailyPrices import (
    check_last_daily_prices_exist,
    download_last_daily_prices,
)
from openData.getMonthlyRevenues import download_hist_monthly_revenues
from openData.getQuarterlyReports import download_hist_quarterly_reports
from openData.getStockList import download_stock_list


def import_csv_to_db(csv_dir=None, db_path=None):
    """Import CSV data to database"""
    if csv_dir is None:
        csv_dir = 'storage'
    else:
        csv_dir = csv_dir.rstrip('/\\')

    try:
        db = StockDatabase(db_path) if db_path else StockDatabase()

        # import stock_list.csv
        print('Importing stock list from CSV to database...')

        csv_path = os.path.join(csv_dir, 'stock_list.csv')

        if not os.path.exists(csv_path):
            print(f'File not found: {csv_path}')
        else:
            count = db.import_stock_list_csv_to_database(csv_path)
            print(f'Successfully imported {count} records')

        # import {XXXX}_prices.csv
        print('\nImporting OHLC prices from CSV to database...')

        csv_folder = os.path.join(csv_dir, 'ohlc')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            count = db.import_ohlc_prices_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records')

        # import prices_{YYYYMMDD}.csv
        print('\nImporting daily prices from CSV to database...')

        csv_folder = os.path.join(csv_dir, 'daily')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            count = db.import_daily_prices_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records')

        # import revenues_{YYYYMM}.csv
        print('\nImporting monthly revenues from CSV to database...')

        csv_folder = os.path.join(csv_dir, 'monthly')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            count = db.import_monthly_revenue_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records')

            if count:
                print('\nCalcatuting and updating monthly revenues in database...')  # fmt: skip
                db.update_monthly_revenue_calculations()
                print('Successfully')

        # import xx_reports_{YYYY}Q{Q}.csv
        print('\nImporting quarterly reports from CSV to database:')

        csv_folder = os.path.join(csv_dir, 'quarterly')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            # import balance_reports_{YYYY}Q{Q}.csv
            print('\nImporting balance reports...')
            count1 = db.import_quarterly_reports_csv_to_database(csv_folder, 'balance_reports')
            print(f'Successfully imported {count1} records')

            # import income_reports_{YYYY}Q{Q}.csv
            print('\nImporting income reports...')
            count2 = db.import_quarterly_reports_csv_to_database(csv_folder, 'income_reports')
            print(f'Successfully imported {count2} records')

            # import cash_reports_{YYYY}Q{Q}.csv
            print('\nImporting cash reports...')
            count3 = db.import_quarterly_reports_csv_to_database(csv_folder, 'cash_reports')
            print(f'Successfully imported {count3} records')

            # if count:
            #     print('\nCalcatuting and updating financial metrics in database...')
            #     db.update_financial_metrics_calculations()
            #     print('Successfully')

        return True

    except Exception as e:
        print(f'Import failed: {e}')
        return False


def download(refetch=False, output_dir=None):
    """Download fresh data and import to database"""
    if refetch:
        action = 'Downloading fresh'
    else:
        action = 'Downloading'

    if output_dir is None:
        output_dir = 'storage'
    else:
        output_dir = output_dir.rstrip('/\\')

    try:
        print(f'{action} stock list...')
        download_stock_list(refetch=refetch, output_dir=output_dir)
        # print('Done')

        print(f'\n{action} last daily prices...')
        dest_dir = os.path.join(output_dir, 'daily')
        if not refetch and not check_last_daily_prices_exist(dest_dir):
            download_last_daily_prices(output_dir=dest_dir)
        # print('Done')

        print(f'\n{action} monthly revenues...')
        dest_dir = os.path.join(output_dir, 'monthly')
        download_hist_monthly_revenues(refetch=refetch, start_date='2013-01-01', output_dir=dest_dir)  # fmt: skip
        # print('Done')

        print(f'\n{action} quarterly reports...')
        dest_dir = os.path.join(output_dir, 'quarterly')
        download_hist_quarterly_reports('income', refetch=refetch, start_date = '2013-01-01', output_dir = dest_dir)  # fmt: skip
        print('')
        download_hist_quarterly_reports('balance', refetch=refetch, start_date = '2013-01-01', output_dir = dest_dir)  # fmt: skip
        print('')
        download_hist_quarterly_reports('cash', refetch=refetch, start_date = '2013-01-01', output_dir = dest_dir)  # fmt: skip
        # print('Done')

        print('\nAll done!')

        return True

    except Exception as e:
        print(f'Download failed: {e}')
        return False


def show_db_info(db_path=None):
    """Show database information"""
    try:
        db = StockDatabase(db_path) if db_path else StockDatabase()

        info = db.get_database_info()

        print(f'Database path: {info["database_path"]}')
        print(f'Tables: {info["tables"]}')

        print(f'\nTotal stocks: {info["stock_list"]["total_count"]}')
        print('Market distribution:')
        for market, count in info['stock_list']['market_stats'].items():
            print(f'  {market}: {count}')
        print(f'Last updated: {info["stock_list"]["last_updated"]}')

        print(f'\nTotal monthly revenues: {info["monthly_revenue"]["total_count"]}')
        print(f'  min month: {info["monthly_revenue"]["min_year_month"]}')
        print(f'  max month: {info["monthly_revenue"]["max_year_month"]}')
        print(f'Last updated: {info["monthly_revenue"]["last_updated"]}')

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
    parser.add_argument('--db-path', help='database file path')

    subparsers = parser.add_subparsers(dest='command', help='available commands')

    # import command
    import_parser = subparsers.add_parser('import', help='import CSV to database')
    import_parser.add_argument('--from_folder', help='read from folder')

    # download command
    download_parser = subparsers.add_parser('download', help='download data')
    download_parser.add_argument('--refetch', action='store_true', help='refetch data')
    download_parser.add_argument('--to_folder', help='write to folder')

    # info command
    subparsers.add_parser('info', help='show database information')

    # search command
    search_parser = subparsers.add_parser('search', help='search stocks')
    search_parser.add_argument('keyword', help='search keyword')

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
