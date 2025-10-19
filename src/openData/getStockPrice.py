import sys
import os

import pandas as pd

# add the parent directory to where the Python looks for modules
# for importing foo from sibling directory
#
# see https://www.geeksforgeeks.org/python-import-from-sibling-directory/
sys.path.append('..')
# thenHelps
from utils.ass import get_last_market_close_day
from utils.getTradingHoliday import isTradingHoliday
from openData.getDailyPrices import get_daily_prices

data_pool = {
    # '20241101': daily_prices_of_20241101_in_DataFrame
}

# Get the stock price for a specific date from local files
#
# param
#   stock_id - specific stock id
#   date     - specific date in 'YYYYMMDD'
#   data_dir - directory containing the files
#
# return the result in pandas.Series
#        maybe an empty pandas.Series if failed
def get_stock_price_from_local (stock_id, date, data_dir):
    # read from data pool first
    df = data_pool.get(date, pd.DataFrame())    # default is an empty DataFrame

    result = pd.Series()    # an empty Series

    if df.empty:
        # not found in pool, try to read from file
        path_name = f'{data_dir}/prices_{date}.csv'

        if not os.path.isfile(path_name) or not os.path.getsize(path_name):
            # file not found or size is 0

            # get date of the last market close
            # NOTE: we use 14:55 for this is the TPEx releases its daily prices of the OTC market
            #       not early 13:50 which only the TSE market was released
            last_date = get_last_market_close_day(close_hour = 14, close_minute = 55)

            # just for debug
            # print(f'request date={date} last_date= {last_date}')

            if date == last_date:
                # we haven't gotten the last daily prices?
                # try to get
                try:
                    df, last_date = get_daily_prices()

                    # make an output directory
                    os.makedirs(data_dir, exist_ok = True)

                    # save to file for next time we can read it directly
                    file_name = f'{data_dir}/prices_{last_date}.csv'

                    try:
                        df.to_csv(file_name, index = False)

                    except:
                        # saving failed but who cares
                        pass

                except:
                    last_date = ''

            if date != last_date:
                if isTradingHoliday(date):
                    print(f'Warning: No trading on {date}')
                else:
                    print(f'Warning: Daily prices for {date} is not available')

                return result   # empty result
        else:
            # read the file
            try:
                df = pd.read_csv(path_name)

            except:
                # reading failed, df is still empty
                pass

        if df.empty:
            print(f'Warning: Fail to read \'{path_name}\' or data is empty')

            return result       # empty result

        # adjust data ...

        # remove unneeded columns
        df = df.drop(['Name', 'Market', 'Value'], axis = 1)

        # format date 'YYYYMMDD' -> 'YYYY-MM-DD'
        ymd = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
        # and insert it as a new 'Date' column at position 0
        df.insert(0, 'Date', ymd)

        # set index to the 'Stock_id' column so we can lookup stock_id by index
        df = df.set_index(['Stock_id'])

        # add to pool
        data_pool[date] = df

    # get the row of the stock_id
    try:
        result = df.loc[stock_id]

    except KeyError:
        print(f'Warning: Not found stock_id \'{stock_id}\' in the save of {date}')

        return result   # empty result

    # just for debug
    # print(result)

    return result

def test ():
    try:
        output_dir = '../_storage/openData'

        print('Test \'2330\' on \'20241212\'')
        prices = get_stock_price_from_local('2330', '20241212', data_dir = output_dir)
        print(prices)
        print('')

        print('Test \'2330\' on \'20241010\'')
        prices = get_stock_price_from_local('2330', '20241010', data_dir = output_dir)
        print(prices)
        print('')

        print('Test \'23xx\' on \'20241212\'')
        prices = get_stock_price_from_local('23xx', '20241212', data_dir = output_dir)
        print(prices)
        print('')

        print('Test \'1101\' on \'20241127\'')
        prices = get_stock_price_from_local('1101', '20241127', data_dir = output_dir)
        print(prices)
        print('')

        print('Test \'1101\' on \'20241101\'')
        prices = get_stock_price_from_local('1101', '20241101', data_dir = output_dir)
        print(prices)
        print('')

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    print('Goodbye!')

if __name__ == '__main__':
    test()
