"""Method A screening method - Revenue New High"""

from screening.list_metrics import (
    # 近 N 季稅後純益率(net_margin)平均 ＞ P%
    list_net_margin_average_threshold,
    # 近 N 季營業利益率(opr_margin)最小／最大 ＞ P%
    list_opr_margin_extremum_threshold,
    # 近 N 季營業利益率(opr_margin)最少 ＞ P%
    list_opr_margin_min_threshold,
    # 近 N 季營業利益率季增率(opr_margin_qoq)連續 M 季成長
    list_opr_margin_qoq_growth_continuous,
    # 近 N 季營業利益率(opr_margin)為近 M 季最大
    list_opr_margin_recent_is_max,
    # 近 N 季營業利益率年增率(opr_margin_yoy)連續 M 季成長
    list_opr_margin_yoy_growth_continuous,
)
from screening.list_price import (
    # 最新股價 ＞ 近 N 個月月均價
    list_price_above_avg,
    # 近 N 個月股價漲幅 ＞ p%
    list_price_growth,
)
from screening.list_revenue import (
    # N 個月累積營收年增率連續 M 個月成長
    list_revenue_accumulated_growth,
    # N 個月累積營收年增率成長幅度 > p%
    list_revenue_accumulated_growth_exceeds,
    # 3/12 個月平均營收連續 N 個月成長
    list_revenue_continuous_growth,
    # 營收月增率連續 N 個月 ＞ P%
    list_revenue_mom_growth,
    # 近 N 個月營收創近 M 月新高
    list_revenue_new_high,
    # 營收年增率連續 N 個月 ＞ P%
    list_revenue_yoy_growth,
)


def list_method_a(db, input_df=None):
    """Get stock list using Method A (Revenue New High)

    Args:
        db (StockDatabase): Database instance
        input_df (pd.DataFrame): Optional input list to filter
            If provided, filter only stocks in this list and accumulate scores.
            If None, use get_industrial_stocks as default.

    Returns:
        pd.DataFrame: DataFrame with columns ('code', 'name', 'score')
    """
    # return list_revenue_new_high(
    #     db, recent_months=3, lookback_months=12, input_df=input_df
    # )

    return list_revenue_continuous_growth(db, ma_type=12, n_months=2, input_df=input_df)
