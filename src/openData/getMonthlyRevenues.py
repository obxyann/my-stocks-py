import os
import sys
from datetime import datetime
from io import StringIO

import pandas as pd
import requests

# add the parent directory to where the Python looks for modules
# for importing foo from sibling directory
#
# see https://www.geeksforgeeks.org/python-import-from-sibling-directory/
sys.path.append('..')
# then
from utils.ansiColors import Colors, use_color
from utils.ass import parse_date_string, wait
from utils.logger import log, logger_end, logger_start

# Data source:
#
# 公開資訊觀測站 (https://mops.twse.com.tw)
# 首頁 > 彙總報表 > 營運概況 > 每月營收 > 每月營收
# https://mops.twse.com.tw/mops/#/web/t21sc04_ifrs


# Fetch the monthly revenue of listed companies for a specific market and month
#
# param
#   market - 'tse': Taiwan Stock Exchange
#            'otc': Over-The-Counter
#            'esb': Emerging Stock Board
#   year   - A.D. year
#   month  - 1: Jan, 2: Feb, ..., 12: Dec
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def fetch_monthly_revenues_in_market(market, year, month):
    log(f'Downloading {market} {year}-{month:02} revenues...\n')

    if market == 'tse':
        market_id = 'sii'
    elif market == 'otc':
        market_id = 'otc'
    elif market == 'esb':
        market_id = 'rotc'
    else:
        raise ValueError(f"Not support market '{market}'")

    if year < 1962:
        # below the start year of TWSE
        raise ValueError(f"Invalid year '{year}'")

    if year < 2013:
        # after this year TWSE provides the CSV data of monthly revenues
        raise ValueError(f"Only HTML data is available in '{year}' which not supported")

    if month < 1 or month > 12:
        raise ValueError(f"Invalid month '{month}'")

    minguo_year = year - 1911

    file_name = f't21sc03_{minguo_year}_{month}.csv'

    # print(f'  {market_id}/{file_name}...')

    # TBD: url = f'https://mops.twse.com.tw/nas/t21/{market_id}/{file_name}' <- obsolete
    url = f'https://mopsov.twse.com.tw/nas/t21/{market_id}/{file_name}'

    # print(url)

    # TODO: for Error: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
    #       https://stackoverflow.com/questions/10115126/python-requests-close-http-connection/15511852#15511852
    #       https://blog.csdn.net/qq_33446100/article/details/118113121

    # method 1 (1/2): use Requests to get data and pass response.text into pd.read_csv (codes below at 2/2)

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f'Failed to download data, status_code = {response.status_code}')  # fmt: skip

    # NOTE: Requests will automatically decode content from the server
    #       It makes educated guesses about the encoding of the response based on the HTTP headers
    #       The text encoding guessed by Requests is used when you access response.text
    #
    #       see https://requests.readthedocs.io/en/latest/user/quickstart/#response-content

    # just for debug
    # print(response.encoding)
    # it shows ISO-8859-1
    # print(response.apparent_encoding)
    # it shows UTF-8-SIG

    # because in the response headers, the Content-Type is just 'text/plain' w/o charset value
    # Requests default uses 'ISO-8859-1' as the encoding (for HTML4) but it should be 'UTF-8'
    #
    # see https://stackoverflow.com/a/52615216
    #
    # override the encoding by real educated guess as provided by charset library
    response.encoding = response.apparent_encoding
    # or force to its real encoding
    # response.encoding = 'UTF-8'

    """
    response.text is a CSV text like
    ---------------------------------
    出表日期,資料年月,公司代號,公司名稱,產業別,營業收入-當月營收,營業收入-上月營收,營業收入-去年當月營收,營業收入-上月比較增減(%),營業收入-去年同月增減(%),累計營業收入-當月累計營收,累計營業收入-去年累計營收,累計營業收入-前期比較增減(%),備註
    "113/02/07","112/12","1101","台泥","水泥工業","9514039","8786909","12584154","8.275151136764931","-24.396673785142806","108614697","112968787","-3.8542416145443785","台泥12月合併營收較去年同期減少24.4%，主要是合併個體 和平電力依約進行一號機組之例行性歲修，致發電量減少所致。"
    "113/02/07","112/12","1102","亞泥","水泥工業","6313936","6915817","8340507","-8.702963077247418","-24.297935365320118","80175007","90344463","-11.256313516413286","-"
    "113/02/07","112/12","1103","嘉泥","水泥工業","283279","255428","228644","10.903659739730962","23.89522576581935","2911281","2253659","29.180190969441252","-"
    ...
    ---------------------------------
    or
    data N/A
    --------
    出表日期,資料年月,公司代號,公司名稱,產業別,營業收入-當月營收,營業收入-上月營收,營業收入-去年當月營收,營業收入-上月比較增減(%),營業收入-去年同月增減(%),累計營業收入-當月累計營收,累計營業收入-去年累計營收,累計營業收入-前期比較增減(%),備註
    --------
    """
    # just for debug
    # print(response.text[:1000])

    cols_to_use = ['公司代號', '公司名稱', '營業收入-當月營收', '備註']
    # NOTE: belows can be skipped, they can be calculated after retrieving the historical data
    #   '營業收入-上月比較增減(%)',
    #   '營業收入-去年當月營收',
    #   '營業收入-去年同月增減(%)',
    #   '累計營業收入-當月累計營收',
    #   '累計營業收入-去年累計營收',
    #   '累計營業收入-前期比較增減(%)'
    # ]

    reason = None

    try:
        # method 1 (2/2): use Requests to get data (codes above at 1/2)
        print('Parsing csv...')

        df = pd.read_csv(StringIO(response.text), index_col=False, usecols=cols_to_use)
        # or
        # method 2: pass url to read_csv directly
        # df = pd.read_csv(url, index_col = False, usecols = cols_to_use)

        df = df[cols_to_use].fillna(0)

    except Exception as error:
        reason = str(error)

    if reason:
        # 'No tables found' likes
        raise Exception(reason)
    if df.empty:
        raise Exception(f"Data not available for '{year}{month}'")

    # set new column names
    df.columns = ['Code', 'Name', 'Revenue', 'Note']
    # NOTE: belows can be missed, they can be calculated after retrieving the historical data
    #   'MoM',
    #   'Last_year',
    #   'YoY',
    #   'Cumulative',
    #   'Cum_last_year',
    #   'CumYoY'
    # ]

    # convert to proper type
    df['Note'] = df['Note'].astype('string')

    # just for debug
    # print(df)

    log(f'  {len(df)} records\n')

    return df


# Get the year and month of the last monthly revenue
#
# return the year, month pair
def get_last_revenue_year_month():
    # current time
    curr_time = datetime.now()

    year = curr_time.year
    month = curr_time.month

    # check to adjust the market closing time
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    return year, month


# Fetch the monthly revenues for a specific month
#
# param
#   year  - A.D. year
#   month - 1: Jan, 2: Feb, ..., 12: Dec
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def fetch_monthly_revenues(year, month):
    try:
        revenues_1 = fetch_monthly_revenues_in_market('tse', year, month)
        wait(2, 5)
        revenues_2 = fetch_monthly_revenues_in_market('otc', year, month)

        # just for debug
        # revenues_1.to_csv(f'{output_dir}/~revenues_tse_{year}{month:02}.csv', index = False)
        # revenues_2.to_csv(f'{output_dir}/~revenues_otc_{year}{month:02}.csv', index = False)

        print('Concatenating data...')

        revenues = pd.concat([revenues_1, revenues_2], ignore_index=True)

        # just for debug
        # print(revenues)

    except Exception as error:
        use_color(Colors.FAIL)
        log(f'Error: {error}\n')
        use_color(Colors.RESET)

        raise Exception('Failed to get revenues')

    log(f'Total {len(revenues)} records\n')

    return revenues


# Download the last monthly revenues
#
# This will download data and save to
# 'revenues_{YYYYMM}.csv' without return the data.
#
# param
#   output_dir - directory where the CSV file will be saved
def download_last_monthly_revenues(output_dir='.'):
    print('Fetching...')

    # last year, month
    year, month = get_last_revenue_year_month()

    # make an output directory
    os.makedirs(output_dir, exist_ok=True)

    # destination file
    path_name = f'{output_dir}/revenues_{year}{month:02}.csv'

    # fetch revenues from remote
    revenues = fetch_monthly_revenues(year, month)

    # save data to file
    revenues.to_csv(path_name, index=False)  # , encoding = 'utf-8-sig')

    print(f"Write to '{path_name}' successfully")


# Download the monthly revenues starting from a specific date
#
# This will check local file first or download data and save to
# 'revenues_{YYYYMM}.csv' without return the data.
#
# param
#   start_date - start date
#   output_dir - directory where the CSV file will be saved
#   refetch    - whether to force refetch even if a local file exists
def download_hist_monthly_revenues(
    start_date='2013-01-01', output_dir='.', refetch=False
):
    print('Fetching...')

    # start year, month
    start = parse_date_string(start_date)
    year, month = start.year, start.month

    # end year, month
    end_year, end_month = get_last_revenue_year_month()
    # or
    # end = parse_date_string(end_date)
    # end_year, end_month = end.year, end.month

    # make an output directory
    os.makedirs(output_dir, exist_ok=True)

    downloaded = 0
    failed = 0
    count = 0

    while True:
        # destination file
        path_name = f'{output_dir}/revenues_{year}{month:02}.csv'

        # check local
        if not refetch and os.path.isfile(path_name) and os.path.getsize(path_name):
            log(f'[{year}-{month:02}] revenues already exists\n')

            delay = False
        else:
            log(f'[{year}-{month:02}]\n')

            try:
                # fetch revenues from remote
                revenues = fetch_monthly_revenues(year, month)

                # save data to file
                revenues.to_csv(path_name, index=False)  # , encoding = 'utf-8-sig')

                downloaded += 1

            except Exception:
                failed += 1

            delay = True

        count += 1

        # to next month
        if year == end_year and month == end_month:
            break
        elif month == 12:
            year += 1
            month = 1
        else:
            month += 1

        # wait a while to avoid blocked
        if delay:
            wait(2, 10)

    log(f'\nTotal {count - failed} done, {downloaded} downloaded, {failed} failed\n')


def test():
    try:
        output_dir = '../_storage/openData/monthly'

        logger_start('_monthly', log_dir=output_dir, add_start_time_to_name=False)  # fmt: skip

        # test 1
        download_last_monthly_revenues(output_dir)

        # test 2
        # download_hist_monthly_revenues('2013-01-01', output_dir)

    except Exception as error:
        print(f'Program terminated: {error}')

        logger_end()

        return

    time_elapsed = logger_end()

    print(f'({time_elapsed} elapsed)')

    print('Goodbye!')


if __name__ == '__main__':
    test()
