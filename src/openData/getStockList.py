import sys
import requests
from io import StringIO
import re
import os
from datetime import datetime

import pandas as pd

# add the parent directory to where the Python looks for modules
# for importing foo from sibling directory
#
# see https://www.geeksforgeeks.org/python-import-from-sibling-directory/
sys.path.append('..')
# then
from utils.ass import file_is_old

# Download the stock list for a specific market
#
# param
#   market            - 'tse': Taiwan Stock Exchange,
#                       'otc': Over-The-Counter,
#                       'esb': Emerging Stock Board
#   include_warrant   - whether to include Warrants (認購(售)權證)
#   include_preferred - whether to include Preferred shares (特別股)
#   include_etn       - whether to include Exchange Traded Notes (ETN)
#   include_reit      - whether to include Real estate investment trusts (不動產投資信託)
#   include_abs       - whether to include Asset-backed securities (資產基礎證券)
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def download_stock_list_in_market (market,
        include_warrant = False,
        include_preferred = False,
        include_etn = False,
        include_reit = False,
        include_abs = False):
    print(f'Downloading html for listed companies in {market.upper()} ...')

    if market == 'tse':
        mode = 2
    elif market == 'otc':
        mode = 4
    elif market == 'esb':
        mode = 5
    else:
        raise ValueError(f'Not support market \'{market}\'')

    response = requests.get(f'https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}')

    if response.status_code != 200:
        raise Exception(f'Failed to download data, status_code = {response.status_code}')
    '''
    response.text is a HTML text(*) like
    ------------------------------------
    ....
    <table align=center>
      ...
    </table>
    <TABLE class='h4' align=center cellSpacing=3 cellPadding=2 width=750 border=0>
      <tr align=center>
        <td bgcolor=#D5FFD5>有價證券代號及名稱 </td>
        <td bgcolor=#D5FFD5>國際證券辨識號碼(ISIN Code)</td>
        <td bgcolor=#D5FFD5>上市日</td>
        <td bgcolor=#D5FFD5>市場別</td>
        <td bgcolor=#D5FFD5>產業別</td>
        <td bgcolor=#D5FFD5>CFICode</td>
        <td bgcolor=#D5FFD5>備註</td>
      </tr>
      <tr>
        <td bgcolor=#FAFAD2 colspan=7><B> 股票 <B> </td>
      </tr>
      <tr>
        <td bgcolor=#FAFAD2>1101 台泥</td>
        <td bgcolor=#FAFAD2>TW0001101004</td>
        <td bgcolor=#FAFAD2>1962/02/09</td>
        <td bgcolor=#FAFAD2>上市</td>
        <td bgcolor=#FAFAD2>水泥工業</td>
        <td bgcolor=#FAFAD2>ESVUFR</td>
        <td bgcolor=#FAFAD2></td>
      </tr>
      ...
    </table>
    ...
    ------------------------------------
    NOTE: (*) from the response headers, the Content-Type is 'text/html;charset=MS950'
              that the HTML text is MS950 (or CP950 or BIG5) encoding - 11/22/2024
    '''
    # just for debug
    # print(response.text[:1000])

    '''
    NOTE: Requests will automatically decode content from the server
          It makes educated guesses about the encoding of the response based on the HTTP headers
          The text encoding guessed by Requests is used when you access response.text

          see https://requests.readthedocs.io/en/latest/user/quickstart/#response-content
    '''

    print('Parsing html ...')

    # accroding to the Content-Type, the original HTML text is MS950 encoding
    # it seems read_html can read it (after Requests decoding) correctly - 11/22/2024
    df = pd.read_html(StringIO(response.text))[0]
    #
    # or
    # add parameter encoding = 'cp950' or 'big5' or 'big5-hkscs' into read_html
    # df = pd.read_html(StringIO(response.text), encoding = 'cp950')[0]
    '''
    return DataFrame is like
    ------------------------
      0                  1                           2          3      4        5       6
    0 有價證券代號及名稱 國際證券辨識號碼(ISIN Code) 上市日     市場別 產業別   CFICode 備註
    1 股票               股票                        股票       股票   股票     股票    股票
    2 1101　台泥         TW0001101004                1962/02/09 上市   水泥工業 ESVUFR  NaN
    3 1102　亞泥         TW0001102002                1962/06/08 上市   水泥工業 ESVUFR  NaN
    4 1103　嘉泥         TW0001103000                1969/11/14 上市   水泥工業 ESVUFR  NaN
    ...
    ------------------------
    '''
    # just for debug
    # print(df)

    # remove column 1, 2, 6 (NOTE: integer N interpreted as label not position)
    df = df.drop([1, 2, 6], axis = 1)

    # set new column names (integer label to string label)
    df.columns = ['Symbol_name', 'Market', 'Industry', 'CFI_code']

    # remove the 1st row [有價證券代號及名稱,市場別,產業別,CFICode]
    # remove row 0 (NOTE: integer 0 interpreted as label not position)
    df = df.drop(0)

    # just for debug
    # print(df)

    '''
    Type               CFI Code
    =================  =============== ======================================
    股票               ESVUFR/ES*      Equities -> Shares
    上市認購(售)權證   RW*             Entitlements (Rights) -> Warrants
    特別股             EP*             Equities -> Preferred shares
                       EF*             Equities -> Preferred convertible shares
    ETF                CEO*            Collective investment vehicles -> Exchange-traded funds (ETFs) | Open-End
    ETN                CMXXXU/CM*      Collective investment vehicles -> Miscellaneous
    臺灣存託憑證(TDR)  EDSDDR/ED*      Equities -> Depositary receipts on equities
    受益證券-不動產投資信託 CBCIXU/CB* Collective investment vehicles -> Real estate investment trusts (REITs)
    受益證券-資產基礎證券   DAFUFR/DA* Debt Instruments -> Asset-backed securities

    NOTE: https://en.wikipedia.org/wiki/ISO_10962
    '''
    def CFI_to_type (cfi):
        if cfi[0] == 'E' and cfi[1] == 'S': # ESVUFR
            return 's'      # as Share

        if cfi[0] == 'R' and cfi[1] == 'W': # RW*
            return 'w'      # as Warrant

        if cfi[0] == 'E' and cfi[1] == 'P': # EP*
            return 'ps'     # as Preferred Share

        if cfi[0] == 'E' and cfi[1] == 'F': # EF*
            return 'ps'     # as Preferred Share

        if cfi[0] == 'C' and cfi[1] == 'E': # CEO*
            return 'etf'    # as Exchange Traded Fund

        if cfi[0] == 'C' and cfi[1] == 'M': # CMXXXU
            return 'etn'    # as Exchange Traded Note

        if cfi[0] == 'E' and cfi[1] == 'D': # EDSDDR
            return 'tdr'    # as Taiwan Depositary Receipt

        if cfi[0] == 'C' and cfi[1] == 'B': # CBCIXU
            return 'reit'   # as Real Estate Investment Trust

        if cfi[0] == 'D' and cfi[1] == 'A': # DA*
            return 'abs'    # as Asset Backed Securities

        if re.match(r'[A-Z]{6}', cfi):
            print(f'Warning: No mapping rule for \'{cfi}\'')
        # else:
        #   print(f'Warning: Invalid CFI format for \'{cfi}\'')

        return '-'

    # add new 'Type' column from 'CFI_code'
    df['Type'] = df['CFI_code'].map(CFI_to_type)

    # remove '上市臺灣創新板' (TIB) rows
    # TODO: as an option includeTIB
    df = df[df['Market'] != '上市臺灣創新板']

    # set 'Market' column to new value
    # NOTE: '上市', '上市臺灣創新板' as 'tse' or '上市臺灣創新板' as 'tib'
    #       '上櫃' as 'otc'
    df['Market'] = market

    # remove unneeded rows
    def filter (type):
        if type == '-': # this is a label row like [股票,股票,...], [上市認購(售)權證,上市認購(售)權證,...], ...
            return False

        # check type
        if type == 'w':
            return include_warrant
        if type == 'ps':
            return include_preferred
        if type == 'etn':
            return include_etn
        if type == 'reit':
            return include_reit
        if type == 'abs':
            return include_abs

        return True

    df = df[[filter(a) for a in df['Type']]]

    # split Symbol_name column into two columns ('1234A\u3000XYZ' -> '1234A', 'XYZ')
    # df[['Symbol', 'Name']] = df['Symbol_name'].str.split('\u3000', n = 1, expand = True) <- see NOTE
    #
    # NOTE: got an strange td cell '4148&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&emsp;全宇生技-KY' in html
    #       which has multiple (half) spaces before the (full) 'EM Space' and
    #       those spaces will be removed to one \u0020 space (aka '4148 全宇生技-KY') after pd.read_html
    #       we need to use regex to split on \u3000 (normal cases) and also space (this case)
    #       - 20241130
    df[['Symbol', 'Name']] = df['Symbol_name'].str.split(r'\u3000| ', n = 1, expand = True)

    # reset index
    df.index = pd.RangeIndex(len(df.index))

    # just for debug
    # print(df)

    print(f'  Total {len(df)} records')

    # return only the columns needed and correct the order
    return df[['Symbol', 'Name', 'Market', 'Industry', 'Type']]
    # or
    # TODO: add an option to return as a compact list
    # return df[['Symbol', 'Name', 'Market']]

# Download the stock list (across all markets)
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def download_stock_list ():
    try:
        list_1 = download_stock_list_in_market('tse')
        list_2 = download_stock_list_in_market('otc')
        '''
        return DataFrame is like
        ------------------------
          Symbol Name Market Industry Type
        0 1101   台泥 tse    水泥工業 s
        1 1102   亞泥 tse    水泥工業 s
        2 1103   嘉泥 tse    水泥工業 s
        ...
        ------------------------
        '''

        print('Concatenating data ...')

        result = pd.concat([list_1, list_2], ignore_index = True)

        # just for debug
        # print(result)

    except Exception as error:
        print(f'Error: {error}')

        raise Exception('Failed to get stock list')

    print(f'  Total {len(result)} records')

    return result

# Get the stock list
#
# This will try to read from local file 'stock_list.csv' first. If the file is missing or old
# then calls download_stock_list.
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def get_stock_list (refetch = False, data_dir = '.'):
    path_name = f'{data_dir}/stock_list.csv'

    try:
        if (refetch or
            file_is_old(path_name, hour = 14, minute = 35) or
            file_is_old(path_name, hour = 16, minute = 35) or
            file_is_old(path_name, hour = 18, minute = 35)):

            stock_list = download_stock_list()

            # make an output directory
            os.makedirs(data_dir, exist_ok = True)

            # save data to file
            stock_list.to_csv(path_name, index = False)

            print(f'  Write to \'{path_name}\' successfully')
        else:
             stock_list = pd.read_csv(path_name, index_col = False)

    except Exception as error:
        raise Exception(error)

    return stock_list

def test ():
    try:
        output_dir = '../_storage/openData'

        start_time = datetime.now()

        # test 1
        df = get_stock_list(data_dir = output_dir)

        # test 2
        # df = get_stock_list(refetch = True, data_dir = output_dir)

        print('--')
        print(df)
        print('--')

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    # NOTE: It's risky to measure elapsed time by two datetime.now() because
    #       datetime.now() may be changed by like network time syncing, daylight savings switchover
    #       or the user twiddling the clock
    end_time = datetime.now()

    time_elapsed = end_time - start_time

    print(f'({time_elapsed} elapsed)')

    print('Goodbye!')

if __name__ == '__main__':
    test()
