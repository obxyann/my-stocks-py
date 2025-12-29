from database.stock import StockDatabase


def initialize_database():
    """Initialize database and import CSV data if needed"""
    try:
        # Initialize database
        db = StockDatabase()

        # TODO: validate...

        return db

    except Exception as error:
        print(f'Database initialization failed: {error}')
        raise


def test_database(db):
    """Dump short information of database"""
    info = db.get_database_info()
    print(f'Database info:\n{info}')


def test_stock_list(db):
    """Test various database operations"""
    try:
        # Test retrieving data
        print('• Retrieving stock list ...')
        stock_list = db.get_stocks()
        if not stock_list.empty:
            print(stock_list.head(5))
            print('...')
            print(stock_list.tail(5))
            print(f'Total {len(stock_list)} records')
        else:
            print('No stock list found')
            return

        print('\n• Searching: "台積"...')
        search_results = db.search_stocks('台積')
        if not search_results.empty:
            print(search_results)
            print(f'Total {len(search_results)} records')
        else:
            print('No search results found')

        print('\n• Retrieving TSE market stocks ...')
        tse_stocks = db.get_stocks_by_market('tse')
        if not tse_stocks.empty:
            print(tse_stocks.head(5))
            print('...')
            print(tse_stocks.tail(5))
            print(f'Total {len(tse_stocks)} records')
        else:
            print('No TSE stocks found')

        print('\n• Retrieving semiconductor industry stocks ...')
        semiconductor_stocks = db.get_stocks_by_industry('半導體業')
        if not semiconductor_stocks.empty:
            print(semiconductor_stocks.head(3))
            print('...')
            print(semiconductor_stocks.tail(3))
            print(f'Total {len(semiconductor_stocks)} records')
        else:
            print('No semiconductor stocks found')

        print('\n• Retrieving general industrial stocks ...')
        general_stocks = db.get_industrial_stocks()
        if not general_stocks.empty:
            print(general_stocks.head(5))
            print('...')
            print(general_stocks.tail(5))
            print(f'Total {len(general_stocks)} records')
        else:
            print('No general stocks found')

    except Exception as error:
        print(f'Database operations failed: {error}')
        raise


def test_daily_prices(db):
    """Test function for daily prices data"""
    try:
        # Test retrieving data
        print('• Retrieving daily prices for stock 2330 in 2025 ...')
        df = db.get_prices_by_code('2330', '2025-01-01', '2025-12-31')
        if not df.empty:
            print(df.head(3))
            print('...')
            print(df.tail(3))
        else:
            print('No data found for stock 2330')

        print('• Retrieving daily prices for stock 0050 in 2020 Jan...')
        df = db.get_prices_by_code('0050', '2020-01-01', '2020-01-31')
        if not df.empty:
            print(df.head(3))
            print('...')
            print(df.tail(3))
        else:
            print('No data found for stock 0050')

    except Exception as error:
        print(f'Database operations failed: {error}')
        raise


def test_monthly_revenue(db):
    """Test function for monthly revenue data"""
    try:
        # Test retrieving data
        print('• Retrieving monthly revenues in 2025 01~03 for stock 2330 ...')
        df = db.get_revenue_by_code('2330', '2025-01', '2025-03')
        if not df.empty:
            # print(df.head(3))
            # print('...')
            # print(df.tail(3))
            print(df.T)
        else:
            print('No data found for stock 2330')

    except Exception as error:
        print(f'Database operations failed: {error}')
        raise


def test_financial(db):
    """Test function for financial data"""
    try:
        # Test retrieving data
        print('• Retrieving financial data for stock 2330 in 2025 ...')
        df1 = db.get_financial_by_code('2330', '2025-01-01', '2025-12-31', year_to_date=True)  # fmt: skip
        df2 = db.get_financial_by_code('2330', '2025-01-01', '2025-12-31')
        if not df1.empty:
            print('YTD\n---')
            print(df1.T)
        else:
            print('No YTD data found for stock 2330')
        print('')
        if not df2.empty:
            print('Periodic\n--------')
            print(df2.T)
        else:
            print('No periodic data found for stock 2330')

    except Exception as error:
        print(f'Database operations failed: {error}')
        raise


def test_financial_metrics(db):
    """Test function for financial metrics"""
    try:
        # Test retrieving data
        print('• Retrieving financial metrics for stock 2330 in 2025 ...')
        df = db.get_financial_metrics_by_code('2330', '2025-01-01', '2025-12-31')
        if not df.empty:
            print(df.T)
        else:
            print('No financial metrics data found for stock 2330')

    except Exception as error:
        print(f'Database operations failed: {error}')
        raise


def test():
    """Main test function"""
    try:
        # output_dir = 'storage'

        # Test 1: Download fresh data
        # print('=== Downloading fresh stock list data ===')
        # df = get_stock_list(refetch = True, data_dir = output_dir)
        # print(f"Downloaded {len(df)} stocks')

        # print('--')
        # print(df)
        # print('--')

        # Initialize database
        db = initialize_database()

        # Test 2: Database operations
        print('\n=== Database information ===')
        test_database(db)

        # Test 3: Stock List
        print('\n=== Testing stock list table ===')
        test_stock_list(db)

        # Test 4: Daily prices
        print('\n=== Testing daily prices table ===')
        test_daily_prices(db)

        # Test 5: Monthly revenue
        print('\n=== Testing monthly revenue table ===')
        test_monthly_revenue(db)

        # Test 6: Financial data
        print('\n=== Testing financial data table ===')
        test_financial(db)

        # Test 7: Financial metrics
        print('\n=== Testing financial metrics table ===')
        test_financial_metrics(db)

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    print('\nGoodbye!')


if __name__ == '__main__':
    test()
