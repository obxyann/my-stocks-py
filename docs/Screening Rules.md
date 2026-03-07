# Screening Rules Documentation

## H 類

- H01: 近 N 期 XXX 出現近 M 期新高  (期間有一期)
- H02: 近 N 期 XXX 連續 M 期 > T              
       XXX 連續 M 期 > T 
       近 N 期 XXX > T  (連續)  
       近 N 期 XXX 最少 > T (連續)
- H03: 近 N 期 XXX 成長幅度連續 M 期 > T
       n-MA XXX 連續 M 期成長  (各期遞增)        
- H04: 近 N 期 XXX 成長幅度 > T  (期間成長幅度)   
       n-MA XXX 成長幅度 > T  (最新一期)                  
- H06: 近 N 期 XXX > 近 M 期平均  (各期 > 平均)  
       最新 XXX > 近 M 期平均
- H07: 近 N 期 XXX 平均 > T                      
- H08: 近 N 期 XXX 最小/最大 > T                

用例:
- H01: 近 N 個月營收創近 M 月新高  (P.S. 近 N 個月中_有任何一個月_)  list_revenue_hit_new_high
- H01: 近 N 季營業利益率為近 M 季最大  (P.S. 近 N 季中_有任何一季_)  list_opr_margin_is_max
- H02: 營收月增率連續 M 個月 > T%                 list_revenue_mom_above
- H02: 近 M 個月營收月增率 > T%  (P.S. 全部)      list_revenue_mom_above
- H02: 營收年增率連續 M 個月 > T%                 list_revenue_yoy_above
- H02: 近 M 個月營收年增率 > T%  (P.S. 全部)      list_revenue_yoy_above
- H02: 近 N 季營業利益率最少 > T%                 list_opr_margin_min_above
- H02: 近 N 季營業利益率 > T%                     list_opr_margin_above
- H02: 營業利益率季增率連續 M 季 > T%             list_opr_margin_qoq_above
- H02: 近 M 季營業利益率季增率 > T%  (P.S. 全部)  list_opr_margin_qoq_above
- H02: 營業利益率年增率連續 M 季 > T%             list_opr_margin_yoy_above
- H02: 近 M 季營業利益率年增率 > T%  (P.S. 全部)  list_opr_margin_yoy_above
- H03: N 個月平均(MA)營收連續 M 個月成長  (P.S. 數值遞增)              list_revenue_ma_growth
- H03: N 個月平均(MA)累積營收年增率連續 M 個月成長  (P.S. 年增率遞增)  list_accum_revenue_yoy_ma_growth
- H04: (最新一期) N 個月平均(MA)累積營收年增率成長幅度 > T%  (P.S. 年增率遞增幅度)  list_accum_revenue_yoy_ma_growth_above
- H04: 近 N 個月股價漲幅 > T%                     list_price_growth_above
- H06: 最新股價 > 近 N 個月月均價                 list_price_above_avg
- H07: 近 N 季稅後純益率平均 > T%                 list_net_margin_avg_above
- H08: 近 N 季營業利益率最小/最大 > T%            list_opr_margin_min_max_ratio_above

## F 類

用例:
- F11: (最新一期) N 個月平均(MA)營收創近 M 月新高  list_revenue_ma_hit_new_high
- F12: (最新一期) N 個月平均(MA)營收大於 M 個月平均(MA)營收  list_revenue_ma_greater_than
- F07: 近 N 日成交量平均 > T 張                    list_volume_avg_above

