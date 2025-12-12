import sys
import requests
from io import StringIO
import os
from datetime import datetime, date

import pandas as pd

# add the parent directory to where the Python looks for modules
# for importing foo from sibling directory
#
# see https://www.geeksforgeeks.org/python-import-from-sibling-directory/
sys.path.append('..')
# then
from utils.logger import log, logger_start, logger_end
from utils.ass import wait, parse_date_string
from utils.ansiColors import Colors, use_color

# Data source:
#
# 公開資訊觀測站 (https://mops.twse.com.tw)
# 首頁 > 彙總報表 > 財務報表 > 財務報表 > 綜合損益表
# https://mops.twse.com.tw/mops/#/web/t163sb04
#
# 首頁 > 彙總報表 > 財務報表 > 財務報表 > 資產負債表
# https://mops.twse.com.tw/mops/#/web/t163sb05
#
# 首頁 > 彙總報表 > 財務報表 > 財務報表 > 現金流量表
# https://mops.twse.com.tw/mops/#/web/t163sb20
#
# 首頁 > 彙總報表 > 財務報表 > 財務比率分析 > 營益分析
# https://mops.twse.com.tw/mops/#/web/t163sb06


# Fetch the financial statement of listed companies for a specific market and quarter
#
# NOTE: There are multiple formats of a financial statement for the different industry sectors.
#       E.g. The 'Balance Sheet' report for all the listed companies will contain up to 6 formats
#       (DataFrames) which some items (columns) are different.
#       If the 'concat' is True (by default) the multiple DataFrames will be concatenated to one
#       in a long columns, must see parameter 'concat'
#
# param
#   market    - 'tse': Taiwan Stock Exchange
#               'otc': Over-The-Counter
#               'esb': Emerging Stock Board
#   year      - A.D. year
#   quarter   - 1: Q1, 2: Q2, 3: Q3, 4: Q4
#   statement - financial statement
#               'income':  Income Statement (Profit and Loss Statement) 損益表
#               'balance': Balance Sheet (Statement of Financial Position) 資產負債表
#               'cash':    Cash Flow Statement 現金流量表
#               'ratio':   Financial ratio 財務比率
#   sectors   - single sector
#               'basi': 金融業
#               'bd':   證券期貨業
#               'ci':   一般業
#               'fh':   金控業
#               'ins':  保險業
#               'mim':  異業
#               or list of above
#               or None for all sectors
#   concat    - True for concatenating different DataFrames of sectors with overlapping columns
#               and return everything in a DataFrame. Columns outside the intersection will be
#               filled with NaN values
#               False for return each DataFrame in a dictionary with key is the name of the sector
#
# return the result in pandas.DataFrame
#        or dictionary of pandas.DataFram(s) when concat = False
#
# raise an exception on failure
def fetch_financial_statements_in_market(
    market, year, quarter, statement, sectors=None, concat=True
):
    log(f'Downloading {market} {year} Q{quarter} {statement} statements...\n')

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
        # after this year TWSE had changed the HTML layout
        raise ValueError('Old HTML format is not supported')

    if quarter < 1 or quarter > 4:
        raise ValueError(f"Invalid quarter '{quarter}'")

    minguo_year = year - 1911

    if statement == 'income':
        data_id = '04'
    elif statement == 'balance':
        data_id = '05'
    elif statement == 'cash':
        data_id = '20'
    elif statement == 'ratio':
        data_id = '06'
    else:
        raise ValueError(f"Not support statement '{statement}'")

    if sectors is None:
        # 金融業, 證券期貨業, 一般業, 金控業, 保險業, 異業
        sectors = ['basi', 'bd', 'ci', 'fh', 'ins', 'mim']
    elif not isinstance(sectors, list):
        sectors = [sectors]

    # TBD: url = f'https://mops.twse.com.tw/mops/web/ajax_t163sb{data_id}' <- obsolete
    url = f'https://mopsov.twse.com.tw/mops/web/ajax_t163sb{data_id}'

    # print(url)

    parameter = {
        # 'encodeURIComponent': '1,
        # ? 'step': '1',
        'firstin': '1',
        # ? 'off': '1',
        # ! 'isQuery': 'Y',
        'TYPEK': market_id,
        'year': str(minguo_year),
        'season': '0' + str(quarter),
    }

    response = requests.post(url, data=parameter)

    # TODO: for Error: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
    #       https://stackoverflow.com/questions/10115126/python-requests-close-http-connection/15511852#15511852
    #       https://blog.csdn.net/qq_33446100/article/details/118113121

    if response.status_code != 200:
        raise Exception(f'Failed to download data, status_code = {response.status_code}')  # fmt: skip
    """
    response.text is a HTML text like
    ---------------------------------
    ...
    ---------------------------------
    or
    data N/A
    --------
    ...
    --------
    """
    # just for debug
    # print(response.text[:1000])
    #
    # just for debug
    # save the response data to a HTML file
    # with open(f'output/~{statement}_{market}_{year}_Q{quarter}.html', 'wb') as f:
    #    f.write(response.content)

    reason = None

    if not response.text or '查詢無資料' in response.text:
        raise Exception(f"No data found for '{year}Q{quarter}'")

    # replace all '--' to 0
    text = response.text.replace('>--</td>', '>0</td>')

    try:
        print('Parsing html...')

        dfs = pd.read_html(StringIO(text))

        n = len(dfs)

    except Exception as error:
        reason = str(error)

    if reason:
        # 'No tables found' likes
        raise Exception(reason)
    if n == 0:
        raise Exception(f"Data not available for '{year}Q{quarter}'")
    if n < 2:
        raise ValueError(f'Unexpected number of tables inside html, {n} < 2')

    if statement == 'ratio':
        # adjust dfs to be similar structure with other statements
        dfs = adjustRatioDfs(dfs)

    if concat:
        result = pd.DataFrame()  # an empty DataFrame
    else:
        result = {}  # an empty Dictionary

    for i in range(1, n):  # don't use dfs[0]
        df = dfs[i]

        sector = guessIndustrySector(df, market, i, n)

        df = adjustDf(df, statement)

        # 證券期貨業, 一般業, 異業
        if sector == 'bd_ci_min' and any(x in ['bd', 'ci', 'min'] for x in sectors):
            multiple_matched = True
        elif sector == '--':
            multiple_matched = True
        else:
            multiple_matched = False

        if sector in sectors or multiple_matched:
            if concat:
                df['Sector'] = sector

                result = pd.concat([result, df], ignore_index=True)
            else:
                result[sector] = df

    # just for debug
    # print(result)

    if concat:
        # move 'Sector' column to the last
        # col = result.pop('Sector')
        # result['Sector'] = col

        result = sortDfColumns(result, statement)

        log(f'  {len(result)} records\n')
    else:
        log(f'  {len(result)} sectors\n')

    return result


# Guess the sector accroding some rules
def guessIndustrySector(df, market, tbl_index, tbl_num):
    columns = df.columns

    # for income
    # use the unique column to guess...
    # pass 1
    for name in columns:
        if name == '0':
            return ''
        if name == '收益':
            return 'bd'  # 證券期貨業
        if name == '保險負債準備淨變動':
            return 'fh'  # 金控業
        if name == '原始認列生物資產及農產品之利益（損失）':
            return 'ci'  # 一般業
        if name == '收入':
            return 'mim'  # 異業
    # pass 2
    for name in columns:
        if name == '利息淨收益':
            return 'basi'  # 金融業
        if name == '營業收入':
            return 'ins'  # 保險業

    # for balance
    # pass 1
    # use the unique column to guess...
    for name in columns:
        if name == '0':
            return ''
        if name == '應付商業本票－淨額':
            return 'fh'  # 金控業
        if name == '應付金融債券':
            return 'basi'  # 金融業
        if name == '分離帳戶保險商品資產':
            return 'ins'  # 保險業

    # pass 2
    # for 證券期貨業, 一般業, 異業 are in the same column format
    for name in columns:
        if name == '流動資產':  # balance only
            # 1. use count of companies to guess
            #    a large number of them should be...
            if len(df) >= 500:
                return 'ci'  # 一般業

            # 2. use table number and index to guess
            #    according the html layout maybe...
            if market == 'tse' and tbl_num == 7:
                if tbl_index == 2:
                    return 'bd'  # 證券期貨業
                elif tbl_index == 3:
                    return 'ci'  # 一般業
                elif tbl_index == 6:
                    return 'min'  # 異業
            elif market == 'otc' and tbl_num == 3:  # 2016~
                if tbl_index == 1:
                    return 'bd'  # 證券期貨業
                elif tbl_index == 2:
                    return 'ci'  # 一般業
            elif market == 'otc' and tbl_num == 4:  # 2013~2015
                if tbl_index == 1:
                    return 'bd'  # 證券期貨業
                elif tbl_index == 2:
                    return 'ci'  # 一般業
                elif tbl_index == 3:
                    return 'min'  # 異業

            use_color(Colors.WARNING)
            log("  Warning: Industry sector is ambiguous - value set to 'bd_ci_min'\n")  # fmt: skip
            log(f'           market: {market}, tbl_num: {tbl_num}, tbl_index: {tbl_index}\n')  # fmt: skip
            use_color(Colors.RESET)

            # just for debug
            print('--')
            print(df.iloc[0, 0], df.iloc[0, 1])
            print('--')

            return 'bd_ci_min'  # maybe 證券期貨業, 一般業, 異業

    # for cash
    # for all are in the same columns format
    for name in columns:
        if name == '營業活動之淨現金流入（流出）':  # cash only
            # use count of companies to guess
            # a large number of them should be...
            if len(df) >= 500:
                return 'ci'

            return '--'  # all possible

    # for ratio
    for name in columns:
        if name == '營業收入 (百萬元)':  # ratio only
            return 'ci'  # only 一般業

    use_color(Colors.WARNING)
    log("  Warning: Unable to decide the industry sector - value set to '--'\n")  # fmt: skip
    log(f'           market: {market}, tbl_num: {tbl_num}, tbl_index: {tbl_index}\n')  # fmt: skip
    use_color(Colors.RESET)

    # just for debug
    print('--')
    print(df.iloc[0, 0], df.iloc[0, 1])
    print('--')

    # stop
    # raise Exception('Failed to guess the industry sector')
    # or keep going
    return '--'  # all possible?


# Adjust dataframes to be similar structure with other statements
def adjustRatioDfs(dfs):
    """
    There are 2 tables in dfs:

    dfs[0] <- There ara many header rows likes '公司代號 公司名稱 ...' in this table
    ------
        0        1        2                   3 ...
    0   公司代號 公司名稱 營業收入\n(百萬元)  毛利率(%)\n(營業毛利)/\n(營業收入) ...
    1   1101     台泥     105,588.49          20.18 ...
        ...
    15  1218     泰山     8,280.05            17.97   6.28    8.94    7.57
    16  公司代號 公司名稱 營業收入\n(百萬元)  毛利率(%)\n(營業毛利)/\n(營業收入) ...
    17  1219     福壽     10,559.02           9.12  ...
    18  1220     台榮     2,408.79            19.08 ...
        ...
    dfs[1] <- Useless table
    ------
    0   0
    1   合計：共 999 家
    2   註：
    ...
    """
    result = []

    # make a dummy dataframe in result[0]
    result.append(pd.DataFrame())

    # take dfs[0]
    df = dfs[0]

    header = df.loc[0, :].values.flatten().tolist()

    # remove all header rows
    df = df[df[0] != header[0]]

    # rename columns
    df.columns = header

    # reset index
    df = df.reset_index(drop=True)

    # add as result[1] (we will get data in dfs[1] later)
    result.append(df)

    return result


# NOTE: according to the pandas's doc the dict values for rename mapper must be unique (1-to-1).
#       but here, some of the values are the same, and there is no problem, because each renaming
#       takes only one of key1:valueA or key2:valueA, and there is no conflict (aka key1, key2
#       will not appear in the same renaming call)
income_columns_rename = {
    '公司代號': 'Code',
    '公司 代號': 'Code',
    '公司名稱': 'Name',
    # 收入
    '營業收入': '營業收入',  # no change
    '收益': '收益',  # no change
    '收入': '收入',  # no change
    '利息淨收益': '利息淨收益',  # no change
    '利息以外淨收益': '利息以外淨收益',  # no change
    '利息以外淨損益': '利息以外淨收益',
    '淨收益': '淨收益',  # no change -> to be removed (not used)
    # 支出
    '營業成本': '營業成本',  # no change
    '支出及費用': '支出及費用',  # no change
    '支出': '支出',  # no change
    '呆帳費用、承諾及保證責任準備提存': '呆帳費用、承諾及保證責任準備提存',  # no change
    '呆帳費用及保證責任準備提存（各項提存）': '呆帳費用、承諾及保證責任準備提存',
    '呆帳費用及保證責任準備提存': '呆帳費用、承諾及保證責任準備提存',
    '保險負債準備淨變動': '保險負債準備淨變動',  # no change
    # 其他收入
    '原始認列生物資產及農產品之利益（損失）': '原始認列生物資產及農產品之利益',
    '生物資產當期公允價值減出售成本之變動利益（損失）': '生物資產當期公允價值減出售成本之變動利益',
    # 毛利
    '營業毛利（毛損）': '營業毛利',
    '未實現銷貨（損）益': '未實現銷貨利益',
    '已實現銷貨（損）益': '已實現銷貨利益',
    '營業毛利（毛損）淨額': '營業毛利淨額',
    # 費用 其他損益
    '營業費用': '營業費用',  # no change
    '其他收益及費損淨額': '其他收益及費損',
    '營業利益': '營業利益',  # no change
    '營業利益（損失）': '營業利益',
    '營業外收入及支出': '營業外收入及支出',  # no change
    '營業外損益': '營業外收入及支出',
    # 稅前淨利
    '稅前淨利（淨損）': '稅前淨利',
    '繼續營業單位稅前純益（純損）': '繼續營業單位稅前淨利',
    '繼續營業單位稅前淨利（淨損）': '繼續營業單位稅前淨利',
    '繼續營業單位稅前損益': '繼續營業單位稅前淨利',
    '利益（淨損）': '利益',
    # 稅
    '所得稅費用（利益）': '所得稅費用',
    '所得稅（費用）利益': '所得稅費用',
    '所得稅利益（費用）': '所得稅費用',
    # 稅後淨利
    '繼續營業單位本期淨利（淨損）': '繼續營業單位本期淨利',
    '繼續營業單位本期純益（純損）': '繼續營業單位本期淨利',
    '繼續營業單位本期稅後淨利（淨損）': '繼續營業單位本期淨利',
    '停業單位損益': '停業單位損益',  # no change
    '合併前非屬共同控制股權損益': '合併前非屬共同控制股權損益',  # no change
    # 本期淨利 其他損益
    '本期淨利（淨損）': '本期淨利',
    '本期稅後淨利（淨損）': '本期淨利',
    '其他綜合損益': '本期其他綜合損益',
    '其他綜合損益（淨額）': '本期其他綜合損益',
    '其他綜合損益（稅後淨額）': '本期其他綜合損益',
    '本期其他綜合損益（稅後淨額）': '本期其他綜合損益',
    '其他綜合損益（稅後）': '本期其他綜合損益',
    '合併前非屬共同控制股權綜合損益淨額': '合併前非屬共同控制股權綜合損益',
    # 本期綜合損益
    '本期綜合損益總額': '本期綜合損益總額',  # no change
    '本期綜合損益總額（稅後）': '本期綜合損益總額',
    # 歸屬於
    '淨利（淨損）歸屬於母公司業主': '淨利歸屬於母公司業主',
    '淨利（損）歸屬於母公司業主': '淨利歸屬於母公司業主',
    '淨利（淨損）歸屬於共同控制下前手權益': '淨利歸屬於共同控制下前手權益',
    '淨利（損）歸屬於共同控制下前手權益': '淨利歸屬於共同控制下前手權益',
    '淨利（淨損）歸屬於非控制權益': '淨利歸屬於非控制權益',
    '淨利（損）歸屬於非控制權益': '淨利歸屬於非控制權益',
    # 歸屬於
    '綜合損益總額歸屬於母公司業主': '綜合損益總額歸屬於母公司業主',  # no change
    '綜合損益總額歸屬於共同控制下前手權益': '綜合損益總額歸屬於共同控制下前手權益',  # no change
    '綜合損益總額歸屬於非控制權益': '綜合損益總額歸屬於非控制權益',  # no change
    # EPS
    '基本每股盈餘（元）': '每股盈餘',
    #
    'Sector': 'Sector',  # extended
}
# after renaming columns
income_columns_remove = [
    '淨收益'  # not used
]
income_columns_sequence = list(income_columns_rename.values())
income_adjust = {
    'rename': income_columns_rename,
    'remove': income_columns_remove,
    'sequence': income_columns_sequence,
}

balance_columns_rename = {
    '公司代號': 'Code',
    '公司 代號': 'Code',
    '公司名稱': 'Name',
    # 資產
    '流動資產': '流動資產',  # no change
    '非流動資產': '非流動資產',  # no change
    '現金及約當現金': '現金及約當現金',  # no change
    '存放央行及拆借銀行同業': '存放央行及拆借同業',
    '存放央行及拆借金融同業': '存放央行及拆借同業',
    '透過損益按公允價值衡量之金融資產': '透過損益按公允價值衡量之金融資產',  # no change
    '備供出售金融資產－淨額': '備供出售金融資產',  # -> to be removed (*)
    '透過其他綜合損益按公允價值衡量之金融資產': '透過其他綜合損益按公允價值衡量之金融資產',  # no change
    '按攤銷後成本衡量之債務工具投資': '按攤銷後成本衡量之債務工具投資',  # no change
    '避險之金融資產': '避險之金融資產',  # no change
    '避險之衍生金融資產淨額': '避險之金融資產',
    '避險之衍生金融資產': '避險之金融資產',
    '附賣回票券及債券投資': '附賣回票券及債券投資',  # no change
    '附賣回票券及債券投資淨額': '附賣回票券及債券投資',
    '應收款項': '應收款項',  # no change
    '應收款項－淨額': '應收款項',
    '本期所得稅資產': '本期所得稅資產',  # no change
    '當期所得稅資產': '本期所得稅資產',
    '待出售資產': '待出售資產',  # no change
    '待出售資產－淨額': '待出售資產',
    'Unnamed: 12': '待分配予業主之資產',  # no change NOTE: in MOPS's t163sb05 and open data's t187ap07_O_fh.csv this is empty string
    '待分配予業主之資產（或處分群組）': '待分配予業主之資產',
    '待分配予業主之資產－淨額': '待分配予業主之資產',
    '貼現及放款－淨額': '貼現及放款',
    '持有至到期日金融資產－淨額': '持有至到期日金融資產',  # -> to be removed (*)
    '投資': '投資',  # no change
    '再保險合約資產': '再保險合約資產',  # no change
    '再保險合約資產－淨額': '再保險合約資產',
    '採用權益法之投資－淨額': '採用權益法之投資',
    '受限制資產－淨額': '受限制資產',
    '其他金融資產－淨額': '其他金融資產',
    '投資性不動產－淨額': '投資性不動產',
    '投資性不動產投資－淨額': '投資性不動產',
    '不動產及設備': '不動產及設備',  # no change
    '不動產及設備－淨額': '不動產及設備',
    '使用權資產': '使用權資產',  # no change
    '使用權資產－淨額': '使用權資產',
    '無形資產': '無形資產',  # no change
    '無形資產－淨額': '無形資產',
    '遞延所得稅資產': '遞延所得稅資產',  # no change
    '其他資產': '其他資產',  # no change
    '其他資產－淨額': '其他資產',
    '分離帳戶保險商品資產': '分離帳戶保險商品資產',  # no change
    '資產總計': '資產總計',  # no change
    '資產總額': '資產總計',
    '資產合計': '資產總計',
    # 負債
    '流動負債': '流動負債',  # no change
    '非流動負債': '非流動負債',  # no change
    '短期債務': '短期債務',  # no change
    '央行及銀行同業存款': '央行及同業存款',
    '央行及金融同業存款': '央行及同業存款',
    '央行及同業融資': '央行及同業融資',  # no change
    '透過損益按公允價值衡量之金融負債': '透過損益按公允價值衡量之金融負債',  # no change
    '避險之金融負債': '避險之金融負債',  # no change
    '避險之衍生金融負債－淨額': '避險之金融負債',
    '避險之衍生金融負債': '避險之金融負債',
    '附買回票券及債券負債': '附買回票券及債券負債',  # no change
    '應付商業本票－淨額': '應付商業本票',
    '應付款項': '應付款項',  # no change
    '本期所得稅負債': '本期所得稅負債',  # no change
    '當期所得稅負債': '本期所得稅負債',
    '與待出售資產直接相關之負債': '與待出售資產直接相關之負債',  # no change
    '存款及匯款': '存款及匯款',  # no change
    '應付債券': '應付債券',  # no change
    '應付金融債券': '應付債券',  # no change
    '應付公司債': '應付公司債',
    '其他借款': '其他借款',  # no change
    '特別股負債': '特別股負債',  # no change
    '其他金融負債': '其他金融負債',  # no change
    '以成本衡量之金融負債': '以成本衡量之金融負債',  # no change -> to be removed (*)
    '租賃負債': '租賃負債',  # no change
    '保險負債': '保險負債',  # no change
    '具金融商品性質之保險契約準備': '具金融商品性質之保險契約準備',  # no change
    '外匯價格變動準備': '外匯價格變動準備',  # no change
    '負債準備': '負債準備',  # no change
    '遞延所得稅負債': '遞延所得稅負債',  # no change
    '其他負債': '其他負債',  # no change
    '分離帳戶保險商品負債': '分離帳戶保險商品負債',  # no change
    '負債總計': '負債總計',  # no change
    '負債總額': '負債總計',
    '負債合計': '負債總計',
    # 權益
    '股本': '股本',  # no change
    '權益─具證券性質之虛擬通貨': '具證券性質之虛擬通貨權益',
    '權益－具證券性質之虛擬通貨': '具證券性質之虛擬通貨權益',
    '資本公積': '資本公積',  # no change
    '保留盈餘': '保留盈餘',  # no change
    '保留盈餘（或累積虧損）': '保留盈餘',
    '其他權益': '其他權益',  # no change
    '庫藏股票': '庫藏股票',  # no change
    '庫藏股': '庫藏股票',
    '歸屬於母公司業主之權益合計': '歸屬於母公司業主之權益合計',  # no change
    '歸屬於母公司業主權益合計': '歸屬於母公司業主之權益合計',
    '歸屬於母公司業主之權益': '歸屬於母公司業主之權益合計',
    '共同控制下前手權益': '共同控制下前手權益',  # no change
    '合併前非屬共同控制股權': '合併前非屬共同控制股權',  # no change
    '非控制權益': '非控制權益',  # no change
    '權益總計': '權益總計',  # no change
    '權益總額': '權益總計',
    '權益合計': '權益總計',
    '負債及權益總計': '負債及權益總計',  # no change -> to be removed (not used)
    '待註銷股本股數（單位：股）': '待註銷股本股數',
    '預收股款（權益項下）之約當發行股數（單位：股）': '預收股款之約當發行股數',
    '母公司暨子公司所持有之母公司庫藏股股數（單位：股）': '母公司暨子公司所持有之母公司庫藏股股數',
    '母公司暨子公司持有之母公司庫藏股股數（單位：股）': '母公司暨子公司所持有之母公司庫藏股股數',
    '每股參考淨值': '每股淨值',
    #
    'Sector': 'Sector',
}
# after renaming columns
balance_columns_remove = [
    '負債及權益總計',  # not used
    '備供出售金融資產',  # (*)
    '持有至到期日金融資產',  # (*)
    '以成本衡量之金融負債',  # (*)
]
# NOTE: (*) 配合IFRS9自107.1.1開始適用，本項目適用至107年度財務報告為止
balance_columns_sequence = list(balance_columns_rename.values())
balance_adjust = {
    'rename': balance_columns_rename,
    'remove': balance_columns_remove,
    'sequence': balance_columns_sequence,
}

cash_columns_rename = {
    '公司代號': 'Code',
    '公司 代號': 'Code',
    '公司名稱': 'Name',
    #
    '營業活動之淨現金流入（流出）': '營業活動之淨現金流入',
    '投資活動之淨現金流入（流出）': '投資活動之淨現金流入',
    '籌資活動之淨現金流入（流出）': '籌資活動之淨現金流入',
    '匯率變動對現金及約當現金之影響': '匯率變動對現金及約當現金之影響',  # no change
    '本期現金及約當現金增加（減少）數': '本期現金及約當現金增加數',
    '期初現金及約當現金餘額': '期初現金及約當現金',
    '期末現金及約當現金餘額': '期末現金及約當現金',
    #
    'Sector': 'Sector',
}
# after renaming columns
cash_columns_remove = []
cash_columns_sequence = list(cash_columns_rename.values())
cash_adjust = {
    'rename': cash_columns_rename,
    'remove': cash_columns_remove,
    'sequence': cash_columns_sequence,
}

ratio_columns_rename = {
    '公司代號': 'Code',
    '公司名稱': 'Name',
    '營業收入 (百萬元)': '營業收入',  # -> to be removed (not used)
    '毛利率(%) (營業毛利)/ (營業收入)': '毛利率',
    '營業利益率(%) (營業利益)/ (營業收入)': '營業利益率',
    '稅前純益率(%) (稅前純益)/ (營業收入)': '稅前純益率',
    '稅後純益率(%) (稅後純益)/ (營業收入)': '稅後純益率',
    #
    'Sector': 'Sector',
}
# after renaming columns
ratio_columns_remove = [
    '營業收入'  # not used
]
ratio_columns_sequence = list(ratio_columns_rename.values())
ratio_adjust = {
    'rename': ratio_columns_rename,
    'remove': ratio_columns_remove,
    'sequence': ratio_columns_sequence,
}

adjust_table = {
    'income': income_adjust,
    'balance': balance_adjust,
    'cash': cash_adjust,
    'ratio': ratio_adjust,
}


# Adjust dataframe
def adjustDf(df, statement):
    try:
        rename = adjust_table[statement]['rename']
        remove = adjust_table[statement]['remove']

    except KeyError:
        use_color(Colors.WARNING)
        log(f"  Warning: Not found '{statement}' in the adjust table\n")
        use_color(Colors.RESET)

        return df

    # check if exist column out of mapping table
    for name in df.columns:
        if name not in rename:
            use_color(Colors.WARNING)
            log(f"  Warning: Not found '{name}' in the rename table of '{statement}'\n")  # fmt: skip
            use_color(Colors.RESET)

    df = df.rename(columns=rename)  # , inplace = True)

    # remove redundant columns
    try:
        df = df.drop(remove, axis=1)

    except Exception:
        pass

    return df


# NOTE: must after renaming columns (aka adjustDf)
def sortDfColumns(df, statement):
    try:
        sequence = adjust_table[statement]['sequence']

    except KeyError:
        use_color(Colors.WARNING)
        log(f"  Warning: Not found '{statement}' in the adjust table\n")
        use_color(Colors.RESET)

        return df

    columns = df.columns.tolist()

    def getIndex(item):
        try:
            return sequence.index(item)

        except Exception:
            use_color(Colors.WARNING)
            log(f"  Warning: Not found '{item}' in sequence list\n")
            use_color(Colors.RESET)

            return len(sequence)

    columns.sort(key=getIndex)

    df = df[columns]

    return df


# Get the year and quarter of the last quarterly report
#
# return the year, quarter pair
#
# 註：依證券交易法第36條及證券期貨局相關函令規定，財務報告申報期限如下：
#     1. 一般行業申報期限：    第一季為5月15日，第二季為8月14日，第三季為11月14日，年度為3月31日。
#     2. 金控業申報期限：      第一季為5月30日，第二季為8月31日，第三季為11月29日，年度為3月31日。
#     3. 銀行及票券業申報期限：第一季為5月15日，第二季為8月31日，第三季為11月14日，年度為3月31日。
#     4. 保險業申報期限：      第一季為5月15日，第二季為8月31日，第三季為11月14日，年度為3月31日。
#     5. 證券業申報期限：      第一季為5月15日，第二季為8月31日，第三季為11月14日，年度為3月31日。
def get_last_report_year_quarter():
    curr_date = datetime.now().date()

    year = curr_date.year

    # retrieve the quarterly data after the deadline
    """
    quarter_range = [
        # beg, end, dec_year, the_quarter
        ('01-01', '03-30', 1, 3), # last year Q3 (7,8,9)
        ('03-31', '05-14', 1, 4), # last year Q4 (10,11,12) deadline: next year's 3/31
        ('05-15', '08-13', 0, 1), # this year Q1 (1,2,3)    deadline: 5/15 or 5/30
        ('08-14', '11-13', 0, 2), # this year Q2 (4,5,6)    deadline: 8/14 or 8/31
        ('11-14', '12-31', 0, 3)] # this year Q3 (7,8,9)    deadline: 11/14 or 11/29
    # or
    # retrieve the quarterly data 15 days before the deadline
    quarter_range = [
        # beg, end, dec_year, the_quarter
        ('01-01', '03-14', 1, 3),  # last year Q3 (7,8,9)
        ('03-15', '04-30', 1, 4),  # last year Q4 (10,11,12) deadline: next year's 3/31
        ('05-01', '07-31', 0, 1),  # this year Q1 (1,2,3)    deadline: 5/15 or 5/30
        ('08-01', '10-31', 0, 2),  # this year Q2 (4,5,6 )   deadline: 8/14 or 8/31
        ('11-01', '12-31', 0, 3),  # this year Q3 (7,8,9)    deadline: 11/14 or 11/29
    ]
    # or
    """
    # retrieve the quarterly data 29 or 30 days before the deadline
    quarter_range = [
        # beg, end, dec_year, the_quarter
        ('01-01', '03-01', 1, 3),  # last year Q3 (7,8,9)
        ('03-02', '04-14', 1, 4),  # last year Q4 (10,11,12) deadline: next year's 3/31
        ('04-15', '07-14', 0, 1),  # this year Q1 (1,2,3)    deadline: 5/15 or 5/30
        ('07-15', '10-14', 0, 2),  # this year Q2 (4,5,6 )   deadline: 8/14 or 8/31
        ('10-15', '12-31', 0, 3),  # this year Q3 (7,8,9)    deadline: 11/14 or 11/29
    ]

    # TODO: use timedelta to calc beg_date, end_date N days before the deadline

    quarter = 0

    for beg, end, dec_year, the_quarter in quarter_range:
        beg_date = date.fromisoformat(f'{year}-{beg}')
        end_date = date.fromisoformat(f'{year}-{end}')
        if beg_date <= curr_date <= end_date:
            year = year - dec_year
            quarter = the_quarter
            break

    if quarter == 0:
        raise Exception("Can't get the year, quarter for last report")

    return year, quarter

    """
    # current time
    curr_time = datetime.now()

    year = curr_time.year
    month = curr_time.month
    quarter = int((month - 1) / 3) + 1

    print(f'{year} {month} {quarter}')

    # check to adjust the market closing time
    if quarter == 1:
        year -= 1
        quarter = 4
    else:
        quarter -= 1

    return year, quarter
    """


# Fetch the quarterly reports for a specific quarter
#
# param
#   year      - A.D. year
#   quarter   - 1: Q1, 2: Q2, 3: Q3, 4: Q4
#   statement - financial statement
#               'income':  Income Statement (Profit and Loss Statement) 損益表
#               'balance': Balance Sheet (Statement of Financial Position) 資產負債表
#               'cash':    Cash Flow Statement 現金流量表
#               'ratio':   Financial ratio 財務比率
#
# return the result in pandas.DataFrame
#
# raise an exception on failure
def fetch_quarterly_reports(year, quarter, statement):
    try:
        reports_1 = fetch_financial_statements_in_market('tse', year, quarter, statement)  # fmt: skip
        wait(2, 5)
        reports_2 = fetch_financial_statements_in_market('otc', year, quarter, statement)  # fmt: skip

        # just for debug
        # reports_1.to_csv(f'{output_dir}/~{statement}_reports_tse_{year}Q{quarter}.csv', index = False)
        # reports_2.to_csv(f'{output_dir}/~{statement}_reports_otc_{year}Q{quarter}.csv', index = False)

        print('Concatenating data...')

        reports = pd.concat([reports_1, reports_2], ignore_index=True)

        # just for debug
        # print(reports)

    except Exception as error:
        use_color(Colors.FAIL)
        log(f'Error: {error}\n')
        use_color(Colors.RESET)

        raise Exception('Failed to get reports')

    log(f'Total {len(reports)} records\n')

    return reports


# Download the last quarterly reports
#
# This will download data and save to
# 'revenues_{YYYYMM}.csv' without return the data.
#
# param
#   statement  - financial statement
#                'income':  Income Statement (Profit and Loss Statement) 損益表
#                'balance': Balance Sheet (Statement of Financial Position) 資產負債表
#                'cash':    Cash Flow Statement 現金流量表
#                'ratio':   Financial ratio 財務比率
#   output_dir - directory where the CSV file will be saved
def download_last_quarterly_reports(statement, output_dir='.'):
    print('Fetching...')

    # last year, quarter
    year, quarter = get_last_report_year_quarter()

    # make an output directory
    os.makedirs(output_dir, exist_ok=True)

    # destination file
    path_name = f'{output_dir}/{statement}_reports_{year}Q{quarter}.csv'

    # fetch reports from remote
    reports = fetch_quarterly_reports(year, quarter, statement)

    # save data to file
    reports.to_csv(path_name, index=False)  # , encoding = 'utf-8-sig')

    print(f"Write to '{path_name}' successfully")


# Download the quarterly reports starting from a specific date
#
# This will check local file first or download data and save to
# '{statement}_reports_{YYYY}Q{Q}.csv' without return the data.
#
# param
#   statement  - financial statement
#                'income':  Income Statement (Profit and Loss Statement) 損益表
#                'balance': Balance Sheet (Statement of Financial Position) 資產負債表
#                'cash':    Cash Flow Statement 現金流量表
#                'ratio':   Financial ratio 財務比率
#   refetch    - whether to force refetch even if a local file exists
#   start_date - start date
#   output_dir - directory where the CSV file will be saved
def download_hist_quarterly_reports(
    statement, refetch=False, start_date='2013-01-01', output_dir='.'
):
    print('Fetching...')

    # start year, quarter
    start = parse_date_string(start_date)
    year = start.year
    quarter = int((start.month - 1) / 3) + 1

    # end year, quarter
    end_year, end_quarter = get_last_report_year_quarter()
    # or
    # end = parse_date_string(end_date)
    # end_year = end.year
    # end_quarter = int((end.month - 1) / 3) + 1

    # make an output directory
    os.makedirs(output_dir, exist_ok=True)

    downloaded = 0
    failed = 0
    count = 0

    while True:
        # destination file
        path_name = f'{output_dir}/{statement}_reports_{year}Q{quarter}.csv'

        # check local
        if not refetch and os.path.isfile(path_name) and os.path.getsize(path_name):
            log(f'[{year}Q{quarter}] {statement} reports already exists\n')

            delay = False
        else:
            log(f'[{year}Q{quarter}]\n')

            try:
                # fetch reports from remote
                reports = fetch_quarterly_reports(year, quarter, statement)

                # save data to file
                reports.to_csv(path_name, index=False)  # , encoding = 'utf-8-sig')

                downloaded += 1

            except Exception:
                failed += 1

            delay = True

        count += 1

        # to next quarter
        if year == end_year and quarter == end_quarter:
            break
        elif quarter == 4:
            year += 1
            quarter = 1
        else:
            quarter += 1

        # wait a while to avoid blocked
        if delay:
            wait(2, 10)

    log(f'\nTotal {count - failed} done, {downloaded} downloaded, {failed} failed\n')


def test():
    try:
        output_dir = '../_storage/openData/quarterly'

        logger_start(log_name='_quarterly', log_dir=output_dir, add_start_time_to_name=False)  # fmt: skip

        # test 1
        download_last_quarterly_reports('income', output_dir=output_dir)
        wait(2, 10)
        download_last_quarterly_reports('balance', output_dir=output_dir)
        wait(2, 10)
        download_last_quarterly_reports('cash', output_dir=output_dir)
        wait(2, 10)
        download_last_quarterly_reports('ratio', output_dir=output_dir)

        # test 2
        # download_hist_quarterly_reports('income', start_date = '2013-01-01', output_dir = output_dir)  # fmt: skip
        # log('\n')
        # download_hist_quarterly_reports('balance', start_date = '2013-01-01', output_dir = output_dir)  # fmt: skip
        # log('\n')
        # download_hist_quarterly_reports('cash', start_date = '2013-01-01', output_dir = output_dir)  # fmt: skip
        # log('\n')
        # download_hist_quarterly_reports('ratio', start_date = '2013-01-01', output_dir = output_dir)  # fmt: skip

    except Exception as error:
        print(f'Program terminated: {error}')

        logger_end()

        return

    time_elapsed = logger_end()

    print(f'({time_elapsed} elapsed)')

    print('Goodbye!')


if __name__ == '__main__':
    test()
