"""Method A screening method - Revenue New High"""

from screening.list_metrics import (
    # 近 N 季稅後純益率(net_margin)平均 ＞ P%
    list_net_margin_avg_above,
    # 近 N 季營業利益率(opr_margin)為近 M 季最大
    list_opr_margin_is_max,
    # 近 N 季營業利益率(opr_margin)最少 ＞ P%
    list_opr_margin_min_above,
    # 近 N 季營業利益率(opr_margin)最小/最大 ＞ P%
    list_opr_margin_min_max_ratio_above,
    # 近 N 季營業利益率季增率(opr_margin_qoq)連續 M 季成長
    list_opr_margin_qoq_growth,
    # 近 N 季營業利益率年增率(opr_margin_yoy)連續 M 季成長
    list_opr_margin_yoy_growth,
)
from screening.list_price import (
    # 最新股價 > 近 N 個月月均價
    list_price_above_avg,
    # 近 N 個月股價漲幅 > P%
    list_price_growth_above,
)
from screening.list_revenue import (
    # N 個月平均累積營收年增率(revenue_ytd_yoy)連續 M 個月成長
    list_accum_revenue_yoy_ma_growth,
    # N 個月平均累積營收年增率(revenue_ytd_yoy)成長幅度 > P%
    list_accum_revenue_yoy_ma_growth_above,
    # 近 N 個月營收創近 M 月新高
    list_revenue_hit_new_high,
    # N 個月平均營收連續 M 個月成長
    list_revenue_ma_growth,
    # 營收月增率(revenue_mom)連續 N 個月 > P%
    list_revenue_mom_above,
    # 營收年增率(revenue_yoy)連續 N 個月 > P%
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
    # Revenue #
    ###########

    if test_case == 1:
        # 近 2 個月營收創近 1 年(12 個月)新高
        return list_revenue_hit_new_high(db, recent_n_months=2, lookback_m_months=12, input_df=input_df)

    if test_case == 2:
        # 12 個月平均營收連續 2 個月成長
        return list_revenue_ma_growth(db, ma_n_months=12, cont_m_months=2, input_df=input_df)

    if test_case == 3:
        # 營收月增率連續 2 個月 ＞ 0%
        return list_revenue_mom_above(db, cont_n_months=2, threshold=0, input_df=input_df)

    if test_case == 4:
        # 營收年增率連續 1 個月 ＞ 40%
        return list_revenue_yoy_above(db, cont_n_months=1, threshold=40, input_df=input_df)

    if test_case == 5:
        # 3 個月平均累積營收年增率連續 1 個月成長
        return list_accum_revenue_yoy_ma_growth(db, ma_n_months=3, cont_m_months=1, input_df=input_df)

    if test_case == 6:
        # 12 個月平均累積營收年增率成長幅度 ＞ 2%
        return list_accum_revenue_yoy_ma_growth_above(db, ma_n_months=12, threshold=2, input_df=input_df)

    #########
    # Price #
    #########

    if test_case == 7:
        # 近 6 個月股價漲幅 ＞ 0%
        return list_price_growth_above(db, recent_n_months=6, threshold=0, input_df=input_df)

    if test_case == 8:
        # 最新股價 ＞ 近 2 個月月均價
        return list_price_above_avg(db, recent_n_months=2, input_df=input_df)

    ###########
    # Metrics #
    ###########

    if test_case == 9:
        # 近 8 季營益率最小/最大 ＞ 60%
        return list_opr_margin_min_max_ratio_above(db, recent_n_quarters=8, threshold=60, input_df=input_df)

    if test_case == 10:
        # 近 1 季營業利益率為近 8 季最大
        return list_opr_margin_is_max(db, recent_n_quarters=1, lookback_m_quarters=8, input_df=input_df)

    if test_case == 11:
        # 近 2 季營業利益率年增率連續 2 季成長
        return list_opr_margin_yoy_growth(db, recent_n_quarters=2, cont_m_quarters=2, input_df=input_df)

    if test_case == 12:
        # 近 3 季營業利益率季增率連續 3 季成長
        return list_opr_margin_qoq_growth(db, recent_n_quarters=3, cont_m_quarters=3, input_df=input_df)

    if test_case == 13:
        # 近 1 季稅後純益率平均 ＞ 0%
        return list_net_margin_avg_above(db, recent_n_quarters=1, threshold=0, input_df=input_df)

    if test_case == 14:
        # 近 4 季營業利益率最少 ＞ 0%
        return list_opr_margin_min_above(db, recent_n_quarters=4, threshold=0, input_df=input_df)

    # Default fallback (e.g. if test_case is out of range)
    return list_revenue_hit_new_high(db, recent_n_months=2, lookback_m_months=12, input_df=input_df)

    # fmt: on


"""
------------------------
*穩定型成長股 (營收選股)
------------------------
    12 個月平均營收連續 2[1~6] 個月成長
    營收年增率連續 1[1~6] 個月 > 40[0%~40%]
    近 8[2~8] 季營益率最小/最大 > 60[30%~90%]
        保留近1季為近8季最大
        保留近 2[1~4] 季YoY成長
        保留近 3[1~7] 季QoQ成長
    近 1[1~8] 季純益率平均 > 0[-10%~15%]
    近 4[1~8] 季營益率最少 > 0[0%~40%]
"""


def list_method_steady(db, input_df=None):
    # 12 個月平均營收連續 2[1~6] 個月成長
    df = list_revenue_ma_growth(db, ma_n_months=12, cont_m_months=2, input_df=input_df)

    # 營收年增率連續 1[1~6] 個月 > 40[0%~40%]
    df = list_revenue_yoy_above(db, cont_n_months=1, threshold=40, input_df=df)

    # 近 8[2~8] 季營益率最小/最大 > 60[30%~90%]
    df1 = list_opr_margin_min_max_ratio_above(
        db, recent_n_quarters=8, threshold=60, input_df=df
    )

    # 保留近1季為近8季最大
    df2 = list_opr_margin_is_max(
        db, recent_n_quarters=1, lookback_m_quarters=8, input_df=df
    )

    # 保留近 2[1~4] 季YoY成長
    df3 = list_opr_margin_yoy_growth(
        db, recent_n_quarters=2, cont_m_quarters=2, input_df=df
    )

    # 保留近 3[1~7] 季QoQ成長
    df4 = list_opr_margin_qoq_growth(
        db, recent_n_quarters=3, cont_m_quarters=3, input_df=df
    )

    df = add_lists(df1, df2)
    df = add_lists(df, df3)
    df = add_lists(df, df4)

    # 近 1[1~8] 季純益率平均 > 0[-10%~15%]
    df = list_net_margin_avg_above(db, recent_n_quarters=1, threshold=0, input_df=df)

    # 近 4[1~8] 季營益率最少 > 0[0%~40%]
    df = list_opr_margin_min_above(db, recent_n_quarters=4, threshold=0, input_df=df)

    return df


"""
------------------------------------------
*長期強勢成長股（營收創新高、股價多頭趨勢）
------------------------------------------
    近 2[1~6] 個月營收創近 1[1~4] 年新高
    近 6[1~24] 個月股價漲幅 > 0[-25%~200%]
"""


def list_method_long(db, input_df=None):
    # 近 2[1~6] 個月營收創近 1[1~4] 年新高
    df = list_revenue_hit_new_high(
        db, recent_n_months=2, lookback_m_months=12, input_df=input_df
    )

    # 6[1~24] 個月股價漲幅 > 0[-25%~200%]
    df = list_price_growth_above(db, recent_n_months=6, threshold=0, input_df=df)

    return df


"""
------------------------------------
*短期強勢成長股（營收上升、股價走強）
------------------------------------
    營收月增率連續 1[1~6] 個月 > 0[~-10%~20%]
    3 個月累積營收年增率連續 1[1~6] 個月成長
    最新股價 > 近 2[1~11] 個月月均價
    or
    營收月增率連續 2[1~6] 個月 > 0[~-10%~20%]
    最新股價 > 近 2[1~11] 個月月均價
    or
    近 6[1~24] 個月股價漲幅 > 0[-25%~200%]
"""


def list_method_short(db, mode=1, input_df=None):
    if mode == 1:
        # 營收月增率連續 1[1~6] 個月 > 0[~-10%~20%]
        df = list_revenue_mom_above(db, cont_n_months=1, threshold=0, input_df=input_df)

        # 3 個月累積營收年增率連續 1[1~6] 個月成長
        df = list_accum_revenue_yoy_ma_growth(
            db, ma_n_months=3, cont_m_months=1, input_df=df
        )

        # 最新股價 > 近 2[1~11] 個月月均價
        df = list_price_above_avg(db, recent_n_months=2, input_df=df)
    elif mode == 2:
        # 營收月增率連續 2[1~6] 個月 > 0[~-10%~20%]
        df = list_revenue_mom_above(db, cont_n_months=2, threshold=0, input_df=df)

        # 最新股價 > 近 2[1~11] 個月月均價
        df = list_price_above_avg(db, recent_n_months=2, input_df=df)
    else:
        # 近 6[1~24] 個月股價漲幅 > 0[-25%~200%]
        df = list_price_growth_above(db, recent_n_months=6, threshold=0, input_df=df)

    return df


"""
------------
衝刺型成長股
------------
    12 個月平均營收連續 1[1~6] 個月成長
    營收年增率連續 1[1~6] 個月 > 35[0%~40%]
    12 個月累積營收年增率連續 1[1~6] 個月成長
    12 個月累積營收年增率成長幅度 > 2[1%~3%]
"""


def list_method_sprint(db, input_df=None):
    # 12 個月平均營收連續 1[1~6] 個月成長
    df = list_revenue_ma_growth(db, ma_n_months=12, cont_m_months=1, input_df=input_df)

    # 營收年增率連續 1[1~6] 個月 > 35[0%~40%]
    df = list_revenue_yoy_above(db, cont_n_months=1, threshold=35, input_df=df)

    # 12 個月累積營收年增率連續 1[1~6] 個月成長
    df = list_accum_revenue_yoy_ma_growth(
        db, ma_n_months=12, cont_m_months=1, input_df=df
    )

    # 12 個月累積營收年增率成長幅度 > 2[1%~3%]
    df = list_accum_revenue_yoy_ma_growth_above(
        db, ma_n_months=12, threshold=2, input_df=df
    )

    return df
