from datetime import datetime, date

# import pandas as pd

# 市場開休市日期
# https://www.tpex.org.tw/zh-tw/announce/market/holiday.html (完整)
# https://www.twse.com.tw/zh/trading/holiday.html (近年)

# 紀念日及節日實施辦法
# https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0020033
#
# 開國紀念日 1/1
# 和平紀念日 2/28
# 兒童節     4/4
# 勞動節     5/1   (勞工放假)
# 教師節     9/28  (NOTE: since 2025)
# 國慶日     10/10
# 光復紀念日 10/25 (NOTE: since 2025)
# 行憲紀念日 12/25 (NOTE: since 2025)
#
# 民俗節日, 除春節放假三日外, 其餘均放假一日
# 春節       農 1/1
# 民族掃墓節 農 清明 (P.S. 國4/4或5或6）(*)
# 端午節     農 5/5
# 中秋節     農 8/15
# 農曆除夕   農 1/1 前一日 (農12/29 或 12/30)
#
# 補假原則:
#   1. 例假日為星期六者於前一個上班日補假, 為星期日者於次一個上班日補假
#   2. 但農曆除夕及春節放假日逢例假日，均於次一個上班日補假
#   3. 兒童節與民族掃墓節同一日時，於前一日放假。但逢星期四時，於後一日放假

# 台北市歷次天然災害停止上班上課訊息
# https://dop.gov.taipei/cp.aspx?n=EFE42F770DFD63FB

# NOTE: 2019 起周末(六,日)無論是否補班皆不開市, 2015~2018 周六補班獨步全球有開市(*), <2015 待確定
#       以下僅列非周末放假日, 如 2022-01-01 是周六, 本來就放假不列

trading_holiday_db = [
# 民國 108 年
'2019-01-01', # (二) 開國 (民國 108 年)
'2019-01-31', # (四) ^休市1
'2019-02-01', # (五) ^休市2
'2019-02-04', # (一) 除夕
'2019-02-05', # (二) 春節1
'2019-02-06', # (三) 春節2
'2019-02-07', # (四) 春節3
'2019-02-08', # (五) 調 0119(六) 補班 for 除夕+春節連假
'2019-02-28', # (四) 和平
'2019-03-01', # (五) 調 0223(六) 補班 for 和平連假
'2019-04-04', # (四) 兒童
'2019-04-05', # (五) 清明
'2019-05-01', # (三) 勞動
'2019-06-07', # (五) 端午
'2019-09-13', # (五) 中秋
'2019-10-10', # (四) 國慶
'2019-10-11', # (五) 調 1005(六) 補班 for 國慶連假
#
'2019-08-09', # (五) !颱 利奇馬
'2019-09-30', # (一) !颱 米塔
# 民國 109 年
'2020-01-01', # (三) 開國 (民國 109 年)
'2020-01-21', # (二) ^休市1
'2020-01-22', # (三) ^休市2
'2020-01-23', # (四) 調 0215(六) 補班 for 除夕+春節連假
'2020-01-24', # (五) 除夕
'2020-01-27', # (一) 春節3 (春節 0125六,0126日,0127一)
'2020-01-28', # (二) 補 0125春節1(逢六)
'2020-01-29', # (三) 補 0126春節2(逢日)
'2020-02-28', # (五) 和平
'2020-04-02', # (四) 補 0403(逢補清明) <- 補 0404兒童(逢清明)
'2020-04-03', # (五) 補 0404清明(逢六)
'2020-05-01', # (五) 勞動
'2020-06-25', # (四) 端午
'2020-06-26', # (五) 調 0620(六) 補班 for 端午連假
'2020-10-01', # (四) 中秋
'2020-10-02', # (五) 調 0926(六) 補班 for 中秋連假
'2020-10-09', # (五) 補 1010國慶(逢六)
# 民國 110 年
'2021-01-01', # (五) 開國 (民國 110 年)
'2021-02-08', # (一) ^休市1
'2021-02-09', # (二) ^休市2
'2021-02-10', # (三) 調 0220(六) 補班 for 除夕+春節連假
'2021-02-11', # (四) 除夕
'2021-02-12', # (五) 春節1 (春節 0212一,0213六,0214日)
'2021-02-15', # (一) 補 0213春節2(逢六)
'2021-02-16', # (二) 補 0214春節3(逢日)
'2021-03-01', # (一) 補 0228(逢日)和平
'2021-04-02', # (五) 補 0403(逢六) <- 補 0404兒童(逢清明)
'2021-04-05', # (一) 補 0404清明(逢日)
'2021-04-30', # (五) 補 0501勞動(逢六)
'2021-06-14', # (一) 端午
'2021-09-20', # (一) 調 0911(六) 補班 for 中秋連假
'2021-09-21', # (二) 中秋
'2021-10-11', # (一) 補 1010國慶(逢日)
'2021-12-31', # (五) 補 20220101開國(逢六) (民國 111 年)
# 民國 111 年
'2022-01-27', # (四) ^休市1
'2022-01-28', # (五) ^休市2
'2022-01-31', # (一) 除夕
'2022-02-01', # (二) 春節1
'2022-02-02', # (三) 春節2
'2022-02-03', # (四) 春節3
'2022-02-04', # (五) 調 0122(六) 補班 for 除夕+春節連假
'2022-02-28', # (一) 和平
'2022-04-04', # (一) 兒童
'2022-04-05', # (二) 清明
'2022-05-02', # (一) 補 0501勞動(逢日)
'2022-06-03', # (五) 端午
'2022-09-09', # (五) 補 0910中秋(逢六)
'2022-10-10', # (一) 國慶
# 民國 112 年
'2023-01-02', # (一) 補 0101開國(逢日) (民國 112 年)
'2023-01-18', # (三) ^休市1
'2023-01-19', # (四) ^休市2
'2023-01-20', # (五) 調 0107(六)補班 for 除夕+春節連假
'2023-01-23', # (一) 春節2 (春節 0122日,0123一,0124二)
'2023-01-24', # (二) 春節3
'2023-01-25', # (三) 補 0121除夕(逢六)
'2023-01-26', # (四) 補 0122春節1(逢日)
'2023-01-27', # (五) 調 0204(六)補班 for 除夕+春節連假
'2023-02-27', # (一) 調 0218(六)補班 for 和平連假
'2023-02-28', # (二) 和平
'2023-04-03', # (一) 調 0325(六)補班 for 兒童+清明連假
'2023-04-04', # (二) 兒童
'2023-04-05', # (三) 清明
'2023-05-01', # (一) 勞動
'2023-06-22', # (四) 端午
'2023-06-23', # (五) 調 0617(六)補班 for 端午連假
'2023-09-29', # (五) 中秋
'2023-10-09', # (一) 調 0923(六)補班 for 國慶連假
'2023-10-10', # (二) 國慶
#
'2023-08-03', # (四) !颱 卡努
# 民國 113 年
'2024-01-01', # (一) 開國 (民國 113 年)
'2024-02-06', # (二) ^休市1
'2024-02-07', # (三) ^休市2
'2024-02-08', # (四) 調 0217(六)補班 for 除夕+春節連假
'2024-02-09', # (五) 除夕
'2024-02-12', # (一) 春節3 (春節 0210六,0211日,0212一)
'2024-02-13', # (二) 補 0210春節1(逢六)
'2024-02-14', # (三) 補 0211春節2(逢日)
'2024-02-28', # (三) 和平
'2024-04-04', # (四) 兒童
'2024-04-05', # (五) 清明
'2024-05-01', # (三) 勞動
'2024-06-10', # (一) 端午
'2024-09-17', # (二) 中秋
'2024-10-10', # (四) 國慶
#
'2024-07-24', # (三) !颱 凱米1
'2024-07-25', # (四) !颱 凱米2
'2024-10-02', # (三) !颱 山陀兒1
'2024-10-03', # (四) !颱 山陀兒2
'2024-10-31', # (四) !颱 康芮
# 民國 114 年
'2025-01-01', # (三) 開國 (民國 114 年)
'2025-01-23', # (四) ^休市1
'2025-01-24', # (五) ^休市2
'2025-01-27', # (一) 調 0208(六)補班 for 除夕+春節連假
'2025-01-28', # (二) 除夕
'2025-01-29', # (三) 春節1
'2025-01-30', # (四) 春節2
'2025-01-31', # (五) 春節3
'2025-02-28', # (五) 和平
'2025-04-03', # (四) 補 0404兒童(逢清明)
'2025-04-04', # (五) 兒童/清明
'2025-05-01', # (四) 勞動
'2025-05-30', # (五) 補 0531端午(逢六)
'2025-09-29', # (一) 補 0928教師(逢日)
'2025-10-06', # (一) 中秋
'2025-10-10', # (五) 國慶
'2025-10-24', # (五) 補 1025光復(逢六)
'2025-12-25', # (四) 行憲
]

# for checking by rule (wait to implement)
# PLAN: by 紀念日及節日實施辦法 + 補假原則
#          農曆陽曆轉換表
#          24節氣表
# NOTE: 調假/災害假 -> 無法計算
'''
1. check date
non_trad_holiday = [
'01-01', # 開國
'02-28', # 和平
'04-04', # 兒童
'05-01', # 勞動
'09-28', # 教師 (NOTE: since 2025)
'10-10', # 國慶 
'10-25', # 光復 (NOTE: since 2025)
'12-25', # 行憲 (NOTE: since 2025)
]
2. convert to lunar calendar and check date
# below is in lunar calendar
trad_holiday = [
'01-01', # 春節1
'01-02', # 春節2
'01-03', # 春節3
'05-05', # 端午
'08-15', # 中秋
# below see Note(*)
# '12-27' or '12-26' or '01-01'-4d, # ^休市1 = 除夕 - 3 (六日者於前一個上班)
# '12-28' or '12-27' or '01-01'-3d, # ^休市2 = 除夕 - 2 (六日者於前一個上班)
# '12-30' or '12-29' or '01-01'-1d, # 除夕
]
3. compute the solar term 'Pure Brightness' of the year and check equal
# below is in 24 solar terms
# 'MM-DD', # 清明

NOTE: (*) the 'Lunar New Year's Eve' is the day before '01-01' but not always '12-30'
          https://www.peoplenews.tw/articles/f0e5c09575
'''

# return pandas.Series
def getTradingHoliday ():
    # TODO: read from csv or
    #       parse https://www.tpex.org.tw/zh-tw/announce/market/holiday.html and write to csv
    # or
    # return pd.Series(trading_holiday_db)
    # or
    pass

# param
#   the_date    'YYYYMMDD' or 'YYYY-MM-DD' or Date or DateTime
#
# return True or False
#        raise an exception when the_date is invalid format or out of the database range
def isTradingHoliday (the_date = None):
    if isinstance(the_date, str):
        try:
            d = date.fromisoformat(the_date)

        except Exception as error:
            raise Exception(error)
            # or
            # print(f'Error: {error}')
            #
            # return False
    elif isinstance(the_date, datetime):
        d = the_date.date()
    elif isinstance(the_date, date):
        d = the_date
    elif the_date == None:
        d = date.today()
    else:
        print(f'Error: Not a valid paramter \'{the_date}\'')
        return False

    # just for debug
    # print(f'Check {d} ({d.isoweekday()}) ...')

    weekday = d.weekday()   # 0~6

    # check if it is the weekend first
    if weekday == 5 or weekday == 6:
        # just for debug
        # print(f'This is weekend: {d.isoweekday()}')
        return True

    # check if listed in trading_holiday_db
    min_year = int(trading_holiday_db[0][0:4])
    max_year = int(trading_holiday_db[-1][0:4])

    if d.year < min_year or d.year > max_year:
        reason = f'Checking date only from {min_year}-01-01 to {max_year}-12-31'

        raise Exception(reason)
        # or
        # print(f'Warning: {reason}')
        #
        # return False
        # or
        # TODO: check by rule

    # get the date in ISO 8601 format 'YYYY-MM-DD'
    the_date = d.isoformat()

    for i in trading_holiday_db:
        if i == the_date:
            return True

    return False

def test ():
    try:
        # l = getTradingHoliday()
        # print(l)

        # test
        print('Test today')
        result = isTradingHoliday()
        print('  Holiday') if result else print('  Trading day')
        print('')

        print('Test \'20241201\'')
        result = isTradingHoliday('20241201')
        print('  Holiday') if result else print('  Trading day')
        print('')

        print('Test \'2024-01-01\'')
        result = isTradingHoliday('2024-01-01')
        print('  Holiday') if result else print('  Trading day')
        print('')

        print('Test datetime(2024, 1, 1)')
        result = isTradingHoliday(datetime(2024, 1, 1))
        print('  Holiday') if result else print('  Trading day')
        print('')

        print('Test date(2024, 1, 1)')
        result = isTradingHoliday(date(2024, 1, 1))
        print('  Holiday') if result else print('  Trading day')
        print('')

        try:
            print('Test date(2010, 1, 1)')
            result = isTradingHoliday(date(2010, 1, 1))
            print('  Holiday') if result else print('  Trading day')
        except Exception as error:
            print(error)
        print('')

        try:
            print('Test \'xx\'')
            result = isTradingHoliday('xx')
            print('  Holiday') if result else print('  Trading day')
        except Exception as error:
            print(error)
        print('')

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    print('Goodbye!')

if __name__ == '__main__':
    test()
