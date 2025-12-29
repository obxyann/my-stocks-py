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

def main():
    """Main test function"""
    try:
        # Initialize database
        db = initialize_database()
 
    except Exception as error:
        print(f'Program terminated: {error}')
        return

    print('\nGoodbye!')


if __name__ == '__main__':
    main()
