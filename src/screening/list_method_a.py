"""Method A screening method"""

import pandas as pd

from screening.list_metrics import (
    # 近 N 季稅後純益率(net_margin)平均 ＞ T%
    list_net_margin_avg_above,
    # 近 N 季營業利益率(opr_margin)為近 M 季最大
    list_opr_margin_is_max,
    # 近 N 季營業利益率(opr_margin)最少 ＞ T%
    list_opr_margin_min_above,
    # 近 N 季營業利益率(opr_margin)最小/最大 ＞ T%
    list_opr_margin_min_max_ratio_above,
    # 近 N 季營業利益率季增率(opr_margin_qoq)連續 M 季成長
    list_opr_margin_qoq_growth,
    # 近 N 季營業利益率年增率(opr_margin_yoy)連續 M 季成長
    list_opr_margin_yoy_growth,
)
from screening.list_price import (
    # 最新股價(price) > 近 N 個月月均價
    list_price_above_avg,
    # 近 N 個月股價(price)漲幅 > T%
    list_price_growth_above,
    # 近 N 日成交量平均 > T 張
    list_volume_avg_above,
)
from screening.list_revenue import (
    # N 個月平均(MA)累積營收年增率(revenue_ytd_yoy)連續 M 個月成長
    list_accum_revenue_yoy_ma_growth,
    # N 個月平均(MA)累積營收年增率(revenue_ytd_yoy)成長幅度 > T%
    list_accum_revenue_yoy_ma_growth_above,
    # 近 N 個月營收(revenue)創近 M 月新高
    list_revenue_hit_new_high,
    # N 個月平均(MA)營收(revenue)連續 M 個月成長
    list_revenue_ma_growth,
    # 營收月增率(revenue_mom)連續 N 個月 > T%
    list_revenue_mom_above,
    # 營收年增率(revenue_yoy)連續 N 個月 > T%
    list_revenue_yoy_above,
)
from screening.operation import add_lists


def list_method_test(db, test_case=1, input_df=None):
    """Get stock list with test case

    Args:
        db (StockDatabase): Database instance
        test_case (int): Case number to execute (1-14)
        input_df (pd.DataFrame): Optional input list to filter
            If provided, filter only stocks in this list and accumulate scores.
            If None, use get_industrial_stocks as default.

    Returns:
        pd.DataFrame: DataFrame with columns ('code', 'name', 'score')
    """
    # fmt: off

    ###########
    # Metrics #
    ###########

    if test_case == 1:
        print('# 近 8 季營業利益率(opr_margin)最小/最大 > 60%')
        return list_opr_margin_min_max_ratio_above(db, recent_n_quarters=8, threshold=60, input_df=input_df)

    if test_case == 2:
        print('# 近 1 季營業利益率(opr_margin)為近 8 季最大')
        return list_opr_margin_is_max(db, recent_n_quarters=1, lookback_m_quarters=8, input_df=input_df)

    if test_case == 3:
        print('# 近 2 季營業利益率年增率(YoY)連續 2 季成長')
        return list_opr_margin_yoy_growth(db, recent_n_quarters=2, cont_m_quarters=2, input_df=input_df)

    if test_case == 4:
        print('# 近 3 季營業利益率季增率(QoQ)連續 3 季成長')
        return list_opr_margin_qoq_growth(db, recent_n_quarters=3, cont_m_quarters=3, input_df=input_df)

    if test_case == 5:
        print('# 近 1 季稅後純益率平均 > 0%')
        return list_net_margin_avg_above(db, recent_n_quarters=1, threshold=0, input_df=input_df)

    if test_case == 6:
        print('# 近 4 季營業利益率最少 > 0%')
        return list_opr_margin_min_above(db, recent_n_quarters=4, threshold=0, input_df=input_df)

    #########
    # Price #
    #########

    if test_case == 11:
        print('# 近 6 個月股價漲幅 > 20%')
        return list_price_growth_above(db, recent_n_months=6, threshold=20, input_df=input_df)

    if test_case == 12:
        print('# 最新股價 > 近 2 個月月均價')
        return list_price_above_avg(db, recent_n_months=2, input_df=input_df)

    if test_case == 13:
        print('# 近 5 日成交量平均 > 500 張')
        return list_volume_avg_above(db, recent_n_days=5, threshold=500, input_df=input_df)

    ###########
    # Revenue #
    ###########

    if test_case == 21:
        print('# 近 2 個月營收創近 1 年新高')
        return list_revenue_hit_new_high(db, recent_n_months=2, lookback_m_months=12, input_df=input_df)

    if test_case == 22:
        print('# 12 個月平均(MA)營收連續 2 個月成長')
        return list_revenue_ma_growth(db, ma_n_months=12, cont_m_months=2, input_df=input_df)

    if test_case == 23:
        print('# 營收月增率(MoM)連續 2 個月 > 0%')
        return list_revenue_mom_above(db, cont_n_months=2, threshold=0, input_df=input_df)

    if test_case == 24:
        print('# 營收年增率(YoY)連續 1 個月 > 40%')
        return list_revenue_yoy_above(db, cont_n_months=1, threshold=40, input_df=input_df)

    if test_case == 25:
        print('# 3 個月平均(MA)累積營收年增率(YoY)連續 1 個月成長')
        return list_accum_revenue_yoy_ma_growth(db, ma_n_months=3, cont_m_months=1, input_df=input_df)

    if test_case == 26:
        print('# 12 個月平均(MA)累積營收年增率(YoY)成長幅度 > 2%')
        return list_accum_revenue_yoy_ma_growth_above(db, ma_n_months=12, threshold=2, input_df=input_df)

    print('# No test case')

    return pd.DataFrame(columns=['code', 'name', 'score'])


def list_method_steady(db, input_df=None):
    """穩定型成長股 (營收選股 - 營收成長趨勢、獲利指標持穩或上升）

    - 12 個月平均營收連續 2 個月成長
    - 營收年增率連續 1 個月 > 40%
    - 近 8 季營益率最小/最大 > 60%
        保留(或)近 1 季為近 8 季最大
        保留(或)近 2 季YoY成長
        保留(或)近 3 季QoQ成長
    - 近 1 季純益率平均 > 0%
    - 近 4 季營益率最少 > 0%
    """
    print('# 12 個月平均(MA)營收連續 2 個月成長')
    df = list_revenue_ma_growth(db, ma_n_months=12, cont_m_months=2, input_df=input_df)

    print('# 營收年增率(YoY)連續 1 個月 > 40%')
    df = list_revenue_yoy_above(db, cont_n_months=1, threshold=40, input_df=df)

    print('# 近 8 季營益率最小/最大 > 60%')
    df1 = list_opr_margin_min_max_ratio_above(
        db, recent_n_quarters=8, threshold=60, input_df=df
    )

    print('# (+) 近 1 季營益率為近 8 季最大')
    df2 = list_opr_margin_is_max(
        db, recent_n_quarters=1, lookback_m_quarters=8, input_df=df
    )

    print('# (+) 近 2 季營益率年增率(YoY)成長')
    df3 = list_opr_margin_yoy_growth(
        db, recent_n_quarters=2, cont_m_quarters=2, input_df=df
    )

    print('# (+) 近 3 季營益率季增率(QoQ)成長')
    df4 = list_opr_margin_qoq_growth(
        db, recent_n_quarters=3, cont_m_quarters=3, input_df=df
    )

    df = add_lists(df1, df2)
    df = add_lists(df, df3)
    df = add_lists(df, df4)

    print('# 近 1 季純益率平均 > 0%')
    df = list_net_margin_avg_above(db, recent_n_quarters=1, threshold=0, input_df=df)

    print('# 近 4 季營益率最少 > 0%')
    df = list_opr_margin_min_above(db, recent_n_quarters=4, threshold=0, input_df=df)

    print('# Done')
    return df


def list_method_long(db, input_df=None):
    """長期強勢成長股（營收創新高、股價多頭趨勢）

    - 近 2 個月營收創近 1 年新高
    - 近 6 個月股價漲幅 > 25% (or 0%)
    """
    print('# 近 2 個月營收創近 1 年新高')
    df = list_revenue_hit_new_high(
        db, recent_n_months=2, lookback_m_months=12, input_df=input_df
    )

    print('# 6 個月股價漲幅 > 25%')
    df = list_price_growth_above(db, recent_n_months=6, threshold=25, input_df=df)

    print('# Done')
    return df


def list_method_short(db, mode=1, input_df=None):
    """短期強勢成長股（營收上升、股價走強）

    - 營收月增率連續 1 個月 > 0%
    - 3 個月累積營收年增率連續 1 個月成長
    - 近 6 個月股價漲幅 > 0%
    - 最新股價 > 近 2 個月月均價
    or
    - 營收月增率連續 1 個月 > 0%
    - 3 個月累積營收年增率連續 1 個月成長
    - 最新股價 > 近 2 個月月均價
    or
    - 營收月增率連續 2 個月 > 0%
    - 最新股價 > 近 2 個月月均價
    or
    - 近 6 個月股價漲幅 > 0%
    """
    if mode == 1:
        print('# 營收月增率(MoM)連續 1 個月 > 0%')
        df = list_revenue_mom_above(db, cont_n_months=1, threshold=0, input_df=input_df)

        print('# 3 個月平均(MA)累積營收年增率(YoY)連續 1 個月成長')
        df = list_accum_revenue_yoy_ma_growth(
            db, ma_n_months=3, cont_m_months=1, input_df=df
        )

        print('# 近 6 個月股價漲幅 > 0%')
        df = list_price_growth_above(db, recent_n_months=6, threshold=0, input_df=df)

        print('# 最新股價 > 近 2 個月月均價')
        df = list_price_above_avg(db, recent_n_months=2, input_df=df)
    elif mode == 2:
        print('# 營收月增率(MoM)連續 2 個月 > 0%')
        df = list_revenue_mom_above(db, cont_n_months=2, threshold=0, input_df=df)

        print('# 最新股價 > 近 2 個月月均價')
        df = list_price_above_avg(db, recent_n_months=2, input_df=df)
    else:
        print('# 近 6 個月股價漲幅 > 0%')
        df = list_price_growth_above(db, recent_n_months=6, threshold=0, input_df=df)

    print('# Done')
    return df


def list_method_sprint(db, input_df=None):
    """衝刺型成長股

    - 12 個月平均營收連續 1 個月成長
    - 營收年增率連續 1 個月 > 35%
    - 12 個月累積營收年增率連續 1 個月成長
    - 12 個月累積營收年增率成長幅度 > 2%
    """
    print('# 12 個月平均(MA)營收連續 1 個月成長')
    df = list_revenue_ma_growth(db, ma_n_months=12, cont_m_months=1, input_df=input_df)

    print('# 營收年增率(YoY)連續 1 個月 > 35%')
    df = list_revenue_yoy_above(db, cont_n_months=1, threshold=35, input_df=df)

    print('# 12 個月平均(MA)累積營收年增率(YoY)連續 1 個月成長')
    df = list_accum_revenue_yoy_ma_growth(
        db, ma_n_months=12, cont_m_months=1, input_df=df
    )

    print('# 12 個月平均(MA)累積營收年增率(YoY)成長幅度 > 2%')
    df = list_accum_revenue_yoy_ma_growth_above(
        db, ma_n_months=12, threshold=2, input_df=df
    )

    print('# Done')
    return df
