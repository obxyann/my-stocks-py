import os
import re
import sys
from datetime import datetime

import pandas as pd
import requests

# add the parent directory to where the Python looks for modules
# for importing foo from sibling directory
#
# see https://www.geeksforgeeks.org/python-import-from-sibling-directory/
sys.path.append('..')
# then
from utils.ansiColors import Colors, use_color
from utils.ass import (
    get_date_from_path_name,
    get_last_market_close_day,
    parse_date_string,
)
from utils.getTradingHoliday import isTradingHoliday
from utils.logger import log, logger_end, logger_start


# Download the (latest) daily prices file in TWSE (Taiwan Stock Exchange)
#
# param
#   output_dir - directory where the CSV file will be saved
#
# return the full path of the saved file 'STOCK_DAY_ALL_{YYYYMMDD}.csv'
#
# raise an exception on failure
def download_daily_prices_in_twse(output_dir='.'):
    log('Downloading TWSE daily prices...\n')

    # get the last daily trading prices
    #
    # NOTE: not support specific date
    url = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data'

    file_name = ''

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f'Failed to download data. status_code = {response.status_code}')  # fmt: skip

    # get the download file name
    """
    response.headers = {
    ...
    'Content-Disposition': 'attachment; filename="STOCK_DAY_ALL_20241106.csv"'
    ...
    }

    see:
    https://stackoverflow.com/questions/31804799/how-to-get-pdf-filename-with-python-requests
    https://stackoverflow.com/questions/37060344/how-to-determine-the-filename-of-content-downloaded-with-http-in-python
    """
    header_value = response.headers.get('Content-Disposition', '')

    if len(header_value):
        found = re.findall(r'filename=\"(.+)\"', header_value)

        if len(found):
            file_name = found[0]
        else:
            # The 'Content-Disposition' header didn't contain the 'filename=' text
            reason = "Can't get the file name. Not found 'filename=' in 'Content-Disposition' header"
    else:
        # Response didn't contain the 'Content-Disposition' header
        reason = "Can't get the file name. No 'Content-Disposition' header"

    if not len(file_name):
        raise Exception(reason)

    """
    response.content(*) is like
    ---------------------------
    證券代號,證券名稱,成交股數,成交金額,開盤價,最高價,最低價,收盤價,漲跌價差,成交筆數
    "0050","元大台灣50","17354391","3397786573","194.05","198.05","193.50","195.20","1.5500","18071"
    ...
    "9958","世紀鋼","1949510","408493516","212.50","213.00","208.00","209.00","-1.0000","2757"
    (this is an empty line)
    ---------------------------
    NOTE: this is binary data (for following open file as "wb")
          on the other hand uses response.text for textual data
    """

    # make an output directory
    os.makedirs(output_dir, exist_ok=True)

    # save the response data to a CSV file
    with open(f'{output_dir}/{file_name}', 'wb') as f:
        f.write(response.content)

    print(f"  '{file_name}' downloaded successfully")

    return f'{output_dir}/{file_name}'


# Download the (latest) daily prices file in TPEx (Taipei Exchange)
#
# A temporary file 'RSTA3104_{YYYMMDD}.csv.tmp' is created during the process and is removed
# upon successful completion.
#
# param
#   output_dir      - directory where the CSV file will be saved
#   include_warrant - whether to include Warrants (認購(售)權證)
#
# return the full path of the saved file 'RSTA3104_{YYYMMDD}.csv', where YYY is Minguo year
# not A.D. year
#
# raise an exception on failure
def download_daily_prices_in_tpex(output_dir='.', include_warrant=False):
    log('Downloading TPEx daily prices...\n')

    # get the last daily trading prices
    #
    # NOTE: also support specific date
    #       like
    #       https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?data=2024/11/07&id=&response=json
    #       https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?data=2024/11/07&id=&response=csv
    url = 'https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?data=&id=&response=csv'

    file_name = ''

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f'Failed to download data. status_code = {response.status_code}')  # fmt: skip

    # get the download file name
    """
    response.headers = {
    ...
    'Content-Disposition': 'attachment; filename="RSTA3104_1131107.csv"'
    ...
    }
    https://stackoverflow.com/questions/31804799/how-to-get-pdf-filename-with-python-requests
    https://stackoverflow.com/questions/37060344/how-to-determine-the-filename-of-content-downloaded-with-http-in-python
    """
    header_value = response.headers.get('Content-Disposition', '')

    if len(header_value):
        found = re.findall(r'filename=\"(.+)\"', header_value)

        if len(found):
            file_name = found[0]
        else:
            # The 'Content-Disposition' header didn't contain the 'filename=' text
            reason = "Can't get the file name. Not found 'filename=' in 'Content-Disposition' header"
    else:
        # Response didn't contain the 'Content-Disposition' header
        reason = "Can't get the file name. No 'Content-Disposition' header"

    if not len(file_name):
        raise Exception(reason)

    """
    response.content is like
    ------------------------
    上櫃股票行情(含等價、零股、盤後、鉅額交易)
    資料日期:113/11/07
    "代號","名稱","收盤","漲跌","開盤","最高","最低","均價","成交股數","成交金額(元)","成交筆數","最後買價","最後買量(千股)","最後賣價","最後賣量(千股)","發行股數","次日參考價","次日漲停價","次日跌停價"
    "006201","元大富櫃50","24.28","+0.17","24.13","24.32","24.00","24.20","181,457","4,392,097","135","24.25","3","24.28","1","15,946,000","24.28","26.70","21.86"
    ...
    "70003U","福華凱基3B售01"," ---","--- ","---","---","---","2.22","0","0","0","2.64","30","0.00","0","5,000,000","3.07","3.80","2.34"
    ...
    "9962","有益","15.55","+0.05","15.60","15.90","15.40","15.60","140,599","2,192,671","84","15.45","6","15.60","2","90,220,260","15.55","17.10","14.00"
    (this is an empty line)
    管理股票
    "代號","名稱","收盤","漲跌","開盤","最高","最低","均價","成交股數","成交金額(元)","成交筆數","最後買價","最後買量(千股)","最後賣價","最後賣量(千股)","發行股數","次日參考價","次日漲停價","次日跌停價"
    (this is an empty line)
    上櫃家數,"831",
    總成交金額,"90,336,756,510",
    總成交股數,"805,151,234",
    總成交筆數,"651,781",
    (this is an empty line)
    ------------------------
    """

    # make an output directory
    os.makedirs(output_dir, exist_ok=True)

    # save the content of the response to a temp file
    temp_file = f'{output_dir}/{file_name}.tmp'

    with open(temp_file, 'wb') as f:
        f.write(response.content)

    # remove useless lines
    #
    # from temp file
    with open(temp_file, 'rt', encoding='cp950') as temp:  # , newline = '\r\n')
        # to csv file
        with open(f'{output_dir}/{file_name}', 'wb') as csv:
            count = 0
            # read line by line
            for line in temp:
                if count < 2:
                    # skip the first 2 lines
                    count += 1
                    continue

                # NOTE: '\n', '\r', or '\r\n' are translated to \n when open a file in text mode w/o newline option
                if line == '\n':
                    # once meet an empty line
                    break

                # replace " ---","--- ","---" -> "" or "0"
                # line = re.sub(r'"[ |-]+"', '""', line)
                # or
                line = re.sub(r'\" ?-{3} ?\"', '"0"', line)

                # replace all "12,345,678","1,234.5" likes -> "12345678","1234.5"
                line = re.sub(
                    r'\"[0-9]{1,3}(,[0-9]{3})+(\.[0-9]+)?\"',
                    lambda x: x.group(0).replace(',', ''),
                    line,
                )

                if not include_warrant:
                    # check if this is leaded by a warrant code like "700000"~"739999", "70000P"~"73999P" or U,T,F,Q
                    # match = re.search(r'^\"7[0-3][0-9]{3}[0-9PUTFQ].*\"$', line)
                    # or
                    # match = re.search(r'^\"7[0-3][0-9]{3}[0-9PUTFQ]', line)
                    # or
                    match = re.match(r'\"7[0-3][0-9]{3}[0-9PUTFQ]', line)
                else:
                    match = None

                if not match:
                    # write this line to csv file
                    csv.write(line.encode('utf-8'))

    try:
        # remove temp file
        os.unlink(temp_file)

    except OSError:
        print(f"  Warning: Can't remove '{temp_file}'\n")

    print(f"  '{file_name}' downloaded successfully")

    return f'{output_dir}/{file_name}'


# Read the TWSE (latest) daily prices from the prices file
#
# If the file does not exist, download it automatically.
#
# param
#   data_dir        - directory containing or for the downloaded file
#   remove_download - whether to delete the downloaded file after use
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def read_twse_daily_prices(data_dir='.', remove_download=True):
    # get date
    last_date = get_last_market_close_day(
        close_hour=13, close_minute=50
    )  # or after 13:37

    # check whether the file has been downloaded (if it hasn't been removed yet)
    path_name = f'{data_dir}/STOCK_DAY_ALL_{last_date}.csv'

    if not os.path.isfile(path_name) or not os.path.getsize(path_name):
        # download the file
        path_name = download_daily_prices_in_twse(output_dir=data_dir)

    try:
        file_date = get_date_from_path_name(path_name)

        log(f'Reading TWSE daily prices on {file_date} saved...\n')

        cols_to_use = [
            '證券代號',
            '證券名稱',
            '開盤價',
            '最高價',
            '最低價',
            '收盤價',
            '成交股數',
            '成交金額',
        ]
        prices = pd.read_csv(path_name, index_col=False, usecols=cols_to_use)

        prices = prices[cols_to_use].fillna(0)

        # set new column names
        prices.columns = [
            'Code',
            'Name',
            'Open',
            'High',
            'Low',
            'Close',
            'Volume',
            'Value',
        ]

        # add 'Market' column
        prices['Market'] = 'tse'

        # convert to appropriate types
        # prices[['Open', 'High', 'Low', 'Close']] = prices[['Open', 'High', 'Low', 'Close']].astype('float32')
        # prices[['Volume', 'Value']] = prices[['Volume', 'Value']].astype('uint32')
        # or
        prices[['Volume', 'Value']] = prices[['Volume', 'Value']].astype('int64')
        # MEMO: use Panda's 'Int64' instead of python's 'int64' to avoid NaN exception

        # just for debug
        # print(prices)

        if remove_download:
            try:
                # remove download
                os.unlink(path_name)

            except OSError:
                use_color(Colors.WARNING)
                log(f"  Warning: Can't remove '{path_name}'\n")
                use_color(Colors.RESET)

    except Exception as error:
        use_color(Colors.FAIL)
        log(f'  Error: {error}\n')
        use_color(Colors.RESET)

        raise Exception('Failed to get daily prices')

    log(f'  {len(prices)} records\n')

    return prices, file_date


# Read the TPEx (latest) daily prices from the prices file
#
# If the file does not exist, download it automatically.
#
# param
#   data_dir        - directory containing or for the downloaded file
#   remove_download - whether to delete the downloaded file after use
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def read_tpex_daily_prices(data_dir='.', remove_download=True):
    # get date
    last_date = get_last_market_close_day(
        close_hour=14, close_minute=55, min_guo_year=True
    )  # or after 14:51

    # check whether the file has been downloaded (if it hasn't been removed yet)
    path_name = f'{data_dir}/RSTA3104_{last_date}.csv'

    if not os.path.isfile(path_name) or not os.path.getsize(path_name):
        # download the file
        path_name = download_daily_prices_in_tpex(output_dir=data_dir)

    try:
        file_date = get_date_from_path_name(path_name)

        log(f'Reading TPEx daily prices on {file_date} saved...\n')

        cols_to_use = [
            '代號',
            '名稱',
            '開盤',
            '最高',
            '最低',
            '收盤',
            '成交股數',
            '成交金額(元)',
        ]
        prices = pd.read_csv(path_name, usecols=cols_to_use)

        prices = prices[cols_to_use].fillna(0)

        # set new column names
        prices.columns = [
            'Code',
            'Name',
            'Open',
            'High',
            'Low',
            'Close',
            'Volume',
            'Value',
        ]

        # add 'Market' column
        prices['Market'] = 'otc'

        # convert to appropriate types
        # prices[['Open', 'High', 'Low', 'Close']] = prices[['Open', 'High', 'Low', 'Close']].astype('float32')
        # prices[['Volume', 'Value']] = prices[['Volume', 'Value']].astype('uint32')
        # or
        prices[['Volume', 'Value']] = prices[['Volume', 'Value']].astype('int64')
        # MEMO: use Panda's 'Int64' instead of python's 'int64' to avoid NaN exception
        # just for debug
        # print(prices)

        if remove_download:
            try:
                # remove download
                os.unlink(path_name)

            except OSError:
                use_color(Colors.WARNING)
                log(f"  Warning: Can't remove '{path_name}'\n")
                use_color(Colors.RESET)

    except Exception as error:
        use_color(Colors.FAIL)
        log(f'  Error: {error}\n')
        use_color(Colors.RESET)

        raise Exception('Failed to get daily prices')

    log(f'  {len(prices)} records\n')

    return prices, file_date


# Fetch the (latest) daily prices
#
# After the function returns, the files downloaded during period will be removed.
#
# param
#   temp_dir - directory for the temp files
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def fetch_daily_prices(temp_dir='.'):
    try:
        prices_1, date_1 = read_twse_daily_prices(data_dir=temp_dir)
        prices_2, date_2 = read_tpex_daily_prices(data_dir=temp_dir)

        # just for debug
        # prices_1.to_csv(f'{temp_dir}/~prices_tse_{date_1}.csv', index = False)
        # prices_2.to_csv(f'{temp_dir}/~prices_otc_{date_2}.csv', index = False)

        if date_1 == date_2:
            print('Concatenating data...')

            prices = pd.concat([prices_1, prices_2], ignore_index=True)

            # just for debug
            # print(prices)
        else:
            if date_1 > date_2:
                exchange = 'TPEx'
            else:
                exchange = 'TWSE'
            use_color(Colors.WARNING)
            log(f'Warning: There is data ({exchange}) waiting to be updated\n')
            use_color(Colors.RESET)

            raise Exception(f"Can't concatenate data with different dates {date_1}, {date_2}")  # fmt: skip

    except Exception as error:
        use_color(Colors.FAIL)
        log(f'Error: {error}\n')
        use_color(Colors.RESET)

        raise Exception('Failed to get prices')

    log(f'Total {len(prices)} records\n')

    return prices, date_1


# Download the last daily prices
#
# This will try to get data from remote and save to
# 'prices_{YYYYMMDD}.csv' without return the data.
#
# param
#   output_dir - directory where the CSV file will be saved
def download_last_daily_prices(output_dir='.'):
    print('Fetching...')

    # make an output directory
    os.makedirs(output_dir, exist_ok=True)

    # fetch prices from remote
    prices, this_date = fetch_daily_prices()  # data_dir = output_dir)

    # destination file
    path_name = f'{output_dir}/prices_{this_date}.csv'

    # save data to file
    prices.to_csv(path_name, index=False)

    print(f"Write to '{path_name}' successfully")


# Check if the local file of last daily prices exists or not
def check_last_daily_prices_exist(data_dir='.'):
    print('Checking local...')

    # get today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # and last market close day
    last_close = parse_date_string(
        get_last_market_close_day(close_hour=14, close_minute=55)
    )

    year, month, day = last_close.year, last_close.month, last_close.day

    if today != last_close:
        use_color(Colors.WARNING)
        if isTradingHoliday(today):
            print('Warning: This is not a trading day')
        else:
            print('Warning: The market is not closed today')
        print(f'         Try to get the last trading day ({year}-{month:02}-{day:02}?) prices')  # fmt: skip
        use_color(Colors.RESET)

    # local file
    path_name = f'{data_dir}/prices_{year}{month:02}{day:02}.csv'

    # check local
    if os.path.isfile(path_name) and os.path.getsize(path_name):
        log(f'[{year}-{month:02}-{day:02}] prices already exists\n')

        return True
    # else:
    return False


def test():
    try:
        output_dir = '../_storage/openData/daily'

        logger_start(log_name='_daily', log_dir=output_dir, add_start_time_to_name=False)  # fmt: skip

        download_last_daily_prices(output_dir=output_dir)

    except Exception as error:
        print(f'Program terminated: {error}')

        logger_end()

        return

    time_elapsed = logger_end()

    print(f'({time_elapsed} elapsed)')

    print('Goodbye!')


if __name__ == '__main__':
    test()
