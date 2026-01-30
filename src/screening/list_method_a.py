"""Method A screening method - Revenue New High"""

from screening.list_metrics import (
    # 近 N 季稅後純益率(net_margin)平均 ＞ P%
    list_net_margin_avg_above,
    # 近 N 季營業利益率(opr_margin)最少 ＞ P%
    list_opr_margin_min_above,
    # 近 N 季營業利益率(opr_margin)最小/最大 ＞ P%
    list_opr_margin_min_max_ratio_above,
    # 近 N 季營業利益率季增率(opr_margin_qoq)連續 M 季成長
    list_opr_margin_qoq_cont_growth,
    # 近 N 季營業利益率(opr_margin)為近 M 季最大
    list_opr_margin_recent_is_max,
    # 近 N 季營業利益率年增率(opr_margin_yoy)連續 M 季成長
    list_opr_margin_yoy_cont_growth,
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


def list_method_a(db, test_case=1, input_df=None):
    """Get stock list using Method A (Revenue New High)

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
        return list_price_growth_above(db, n_months=6, p_percent=0, input_df=input_df)

    if test_case == 8:
        # 最新股價 ＞ 近 2 個月月均價
        return list_price_above_avg(db, n_months=2, input_df=input_df)

    ###########
    # Metrics #
    ###########

    if test_case == 9:
        # 近 8 季營益率最小/最大 ＞ 60%
        return list_opr_margin_min_max_ratio_above(db, n_quarters=8, threshold=60, input_df=input_df)

    if test_case == 10:
        # 近 1 季營業利益率為近 8 季最大
        return list_opr_margin_recent_is_max(db, n_quarters=1, m_lookback=8, input_df=input_df)

    if test_case == 11:
        # 近 2 季營業利益率年增率連續 2 季成長
        return list_opr_margin_yoy_cont_growth(db, n_quarters=2, m_quarters=2, input_df=input_df)

    if test_case == 12:
        # 近 3 季營業利益率季增率連續 3 季成長
        return list_opr_margin_qoq_cont_growth(db, n_quarters=3, m_quarters=3, input_df=input_df)

    if test_case == 13:
        # 近 1 季稅後純益率平均 ＞ 0%
        return list_net_margin_avg_above(db, n_quarters=1, threshold=0, input_df=input_df)

    if test_case == 14:
        # 近 4 季營業利益率最少 ＞ 0%
        return list_opr_margin_min_above(db, n_quarters=4, threshold=0, input_df=input_df)

    # Default fallback (e.g. if test_case is out of range)
    return list_revenue_hit_new_high(db, recent_months=2, lookback_months=12, input_df=input_df)

    # fmt: on
