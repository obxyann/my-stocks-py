import argparse
import os

from database.stock import StockDatabase
from openData.getDailyPrices import (
    check_last_daily_prices_exist,
    download_last_daily_prices,
)
from openData.getMonthlyRevenues import (
    download_hist_monthly_revenues,
    download_last_monthly_revenues,
)
from openData.getQuarterlyReports import (
    download_hist_quarterly_reports,
    download_last_quarterly_reports,
)
from openData.getStockList import download_stock_list
from utils.ass import wait


def import_csv_to_db(csv_dir=None, db_path=None):
    """Import CSV data to database"""
    if csv_dir is None:
        csv_dir = 'storage'
    else:
        csv_dir = csv_dir.rstrip('/\\')

    try:
        db = StockDatabase(db_path) if db_path else StockDatabase()

        # import stock_list.csv
        print('Importing stock list to database...')

        csv_path = os.path.join(csv_dir, 'stock_list.csv')

        if not os.path.exists(csv_path):
            print(f'File not found: {csv_path}')
        else:
            count = db.import_stock_list_csv_to_database(csv_path)
            print(f'Successfully imported {count} records')

        # import business_type.csv
        print('\nImporting business type of stocks to database...')

        csv_folder = os.path.join(csv_dir, 'quarterly')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            count = db.import_business_type_csv_to_stocks(csv_folder)
            print(f'Successfully imported {count} records')

        # import {XXXX}_prices.csv
        print('\nImporting OHLC prices to database...')

        csv_folder = os.path.join(csv_dir, 'ohlc')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            count = db.import_ohlc_prices_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records')

        # import prices_{YYYYMMDD}.csv
        print('\nImporting daily prices to database...')

        csv_folder = os.path.join(csv_dir, 'daily')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            count = db.import_daily_prices_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records')

        # import revenues_{YYYYMM}.csv
        print('\nImporting monthly revenues to database...')

        csv_folder = os.path.join(csv_dir, 'monthly')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            count = db.import_monthly_revenue_csv_to_database(csv_folder)
            print(f'Successfully imported {count} records')

            if count:
                print('\nCalculating and updating monthly revenues in database...')  # fmt: skip
                db.update_monthly_revenue()
                print('Successfully')

        # import xx_reports_{YYYY}Q{Q}.csv
        print('\nImporting quarterly reports to database:')

        csv_folder = os.path.join(csv_dir, 'quarterly')

        if not os.path.isdir(csv_folder):
            print(f'Folder not found: {csv_folder}')
        else:
            # import balance_reports_{YYYY}Q{Q}.csv
            print('\nImporting balance reports...')
            count1 = db.import_quarterly_reports_csv_to_database(csv_folder, 'balance_reports', is_year_to_date=True)  # fmt: skip
            print(f'Successfully imported {count1} records')

            # import income_reports_{YYYY}Q{Q}.csv
            print('\nImporting income reports...')
            count2 = db.import_quarterly_reports_csv_to_database(csv_folder, 'income_reports', is_year_to_date=True)  # fmt: skip
            print(f'Successfully imported {count2} records')

            # import cash_reports_{YYYY}Q{Q}.csv
            print('\nImporting cash reports...')
            count3 = db.import_quarterly_reports_csv_to_database(csv_folder, 'cash_reports', is_year_to_date=True)  # fmt: skip
            print(f'Successfully imported {count3} records')

            if count1 or count2 or count3:
                print('\nCalculating and updating financial core table...')
                db.update_financial_core_from_ytd()
                print('Successfully')

            # if count1 or count2 or count3:
            print('\nCalcatuting and updating financial metrics in database...')
            db.update_financial_metrics()
            print('Successfully')

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
        download_stock_list(output_dir, refetch)
        # print('Done')

        print(f'\n{action} last daily prices...')
        dest_dir = os.path.join(output_dir, 'daily')
        if not refetch and not check_last_daily_prices_exist(dest_dir):
            download_last_daily_prices(dest_dir)
        # print('Done')

        print(f'\n{action} monthly revenues...')
        dest_dir = os.path.join(output_dir, 'monthly')
        download_hist_monthly_revenues('2013-01-01', dest_dir, refetch)  # fmt: skip

        print('\nRefreshing last monthly revenues...')
        download_last_monthly_revenues(dest_dir)
        # print('Done')

        print(f'\n{action} quarterly reports...')
        dest_dir = os.path.join(output_dir, 'quarterly')
        download_hist_quarterly_reports('income', '2013-01-01', dest_dir, refetch)  # fmt: skip
        print('')
        download_hist_quarterly_reports('balance', '2013-01-01', dest_dir, refetch)  # fmt: skip
        print('')
        download_hist_quarterly_reports('cash', '2013-01-01', dest_dir, refetch)  # fmt: skip

        print('\nRefreshing last quarterly reports...')
        download_last_quarterly_reports('income', output_dir)
        wait(2, 10)
        download_last_quarterly_reports('balance', output_dir)
        wait(2, 10)
        download_last_quarterly_reports('cash', output_dir)
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

        print(f'\nTotal daily prices: {info["daily_prices"]["total_count"]}')
        print(f'  min date: {info["daily_prices"]["min_date"]}')
        print(f'  max date: {info["daily_prices"]["max_date"]}')
        print(f'Last updated: {info["daily_prices"]["last_updated"]}')

        print(f'\nTotal monthly revenues: {info["monthly_revenue"]["total_count"]}')
        print(f'  min month: {info["monthly_revenue"]["min_year_month"]}')
        print(f'  max month: {info["monthly_revenue"]["max_year_month"]}')
        print(f'Last updated: {info["monthly_revenue"]["last_updated"]}')

        print(f'\nTotal financial core: {info["financial_core"]["total_count"]}')
        print(f'  min quarter: {info["financial_core"]["min_year_quarter"]}')
        print(f'  max quarter: {info["financial_core"]["max_year_quarter"]}')
        print(f'Last updated: {info["financial_core"]["last_updated"]}')

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
