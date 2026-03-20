# Common Screening Rules

縮排項目: 相似規則，可由父規則涵蓋 (缺值, 縮限, 同語意...)

## H 類

- H01: 近 N 期 XXX 出現近 M 期新高  (期間有一期)
       近 N 期 XXX 創近 M 期新高  (期間有一期)
- H02: 近 N 期 XXX 連續 M 期 > T              
       XXX 連續 M 期 > T 
       近 N 期 XXX > T  (連續)  
       近 N 期 XXX 最少 > T (連續)
- H03: 近 N 期 XXX 成長幅度連續 M 期 > T
       n-MA XXX 連續 M 期成長  (各期遞增)        
- H04: 近 N 期 XXX 成長幅度 > T  (期間成長幅度)   
       n-MA XXX 成長幅度 > T  (最新一期)
- H05: 近 N 期 XXX > 近 M 期平均  (各期 > 平均)  
       最新 XXX > 近 M 期平均
- H06: 近 N 期 XXX 平均 > T                      
- H07: 近 N 期 XXX 最小/最大 > T                

用例:
- H01_01: 近 N 個月營收創近 M 月新高  (近 N 個月中_有任何一個月_)  list_revenue_hit_new_high
- H01_02: 近 N 季營業利益率為近 M 季最大  (近 N 季中_有任何一季_)  list_opr_margin_is_max
- H02_03: 營收月增率連續 M 個月 > T%                 list_revenue_mom_above
- H02_04: 近 M 個月營收月增率 > T%  (全部)           list_revenue_mom_above
- H02_05: 營收年增率連續 M 個月 > T%                 list_revenue_yoy_above
- H02_06: 近 M 個月營收年增率 > T%  (全部)           list_revenue_yoy_above
- H02_07: 近 N 季營業利益率最少 > T%                 list_opr_margin_min_above
- H02_08: 近 N 季營業利益率 > T%                     list_opr_margin_above
- H02_09: 營業利益率季增率連續 M 季 > T%             list_opr_margin_qoq_above
- H02_10: 近 M 季營業利益率季增率 > T%  (全部)       list_opr_margin_qoq_above
- H02_11: 營業利益率年增率連續 M 季 > T%             list_opr_margin_yoy_above
- H02_12: 近 M 季營業利益率年增率 > T%  (全部)       list_opr_margin_yoy_above
- H03_13: N 個月平均(MA)營收連續 M 個月成長  (數值遞增)              list_revenue_ma_growth
- H03_14: N 個月平均(MA)累積營收年增率連續 M 個月成長  (年增率遞增)  list_accum_revenue_yoy_ma_growth
- H04_15: (最新一期) N 個月平均(MA)累積營收年增率成長幅度 > T%  (年增率遞增幅度)  list_accum_revenue_yoy_ma_growth_above
- H04_16: 近 N 個月股價成長幅度 > T%  (N 個月期間)   list_price_growth_above
- H05_17: 最新股價 > 近 N 個月月均價                 list_price_above_avg
- H06_18: 近 N 季稅後純益率平均 > T%                 list_net_margin_avg_above
- H07_19: 近 N 季營業利益率最小/最大 > T%            list_opr_margin_min_max_ratio_above

組合:
1. _穩定型成長股 (營收選股 - 營收成長趨勢、獲利指標持穩或上升）_

- H03_13: 12 個月平均(MA)營收連續 2 個月成長
- H02_05: 營收年增率連續 1 個月 > 40%
- H07_19: 近 8 季營業利益率最小/最大 > 60%
  or
  H01_02: 近 1 季營業利益率為近 8 季最大
  or
  H02_12: 近 2 季營業利益率年增率 > 0%
  or 
  H02_10: 近 3 季營業利益率季增率 > 0%
- H06_18: 近 1 季稅後純益率平均 > 0%
- H02_07: 近 4 季營業利益率最少 > 0%

2. _長期強勢成長股（營收創新高、股價多頭趨勢）_

- H01_01: 近 2 個月營收創近 12 個月新高
- H04_16: 6 個月股價成長幅度 > 25% (or 0%)

3. _短期強勢成長股（營收上升、股價走強）_

- H02_03: 營收月增率連續 1 個月 > 0%
- H03_14: 3 個月平均(MA)累積營收年增率連續 1 個月成長
- H04_16: 近 6 個月股價成長幅度 > 0%
- h05_17: 最新股價 > 近 2 個月月均價
or
- H02_03: 營收月增率連續 2 個月 > 0%
- h05_17: 最新股價 > 近 2 個月月均價
or
- H04_16: 近 6 個月股價成長幅度 > 0%

4. _衝刺型成長股_

- H03_13: 12 個月平均(MA)營收連續 1 個月成長
- H02_05: 營收年增率連續 1 個月 > 35%
- H03_14: 12 個月平均(MA)累積營收年增率連續 1 個月成長
- H04_15: (最新一期) 12 個月平均(MA)累積營收年增率成長幅度 > 2%

## F 類

- F01: (~H01) 近 N 期內有 K 期 XXX 創近 M 期新高
       (最新一期) n-MA XXX 創近 M 期新高
       最新 XXX 創 M 期新高
- F06: (=H06) 近 N 期 XXX 平均 > T
- F12: N 個月平均(MA)營收連續 K 期大於 M 個月平均(MA)營收
       (最新一期) N 個月平均(MA)營收大於 M 個月平均(MA)營收
 
用例:
- F01_01: (最新一期) N 個月平均(MA)營收創近 M 月新高  list_revenue_ma_hit_new_high
- F01_02: 近 N 日內有 K 日股價創近 M 日新高           list_price_hit_new_high_days
- F01_03: 最新股價創 M 日新高                         list_price_hit_new_high_days (N=1, K=1)   
- F06_04: 近 N 日成交量平均 > T 張                    list_volume_avg_above
- F12_00: (最新一期) N 個月平均(MA)營收大於 M 個月平均(MA)營收  list_revenue_ma_greater_than

組合:
1. _營收股價雙渦輪_

- F01_01: (最新一期) 2 個月平均(MA)營收創近 12 個月來新高
- F01_02: 近 5 日內有 2 日股價創近 200 日新高
- F06_04: 近  5 日成交量平均 > 500 張
- 以上選 (最新一期) 營收年增率前 10 強
  (買營收爆發)

2. _藏獒_

- F01_03: 最新股價創 250 日新高
- 排除: 營收連 3 個月衰退 10% 以上
- 排除: 12 個月內有至少 8 個月營收年增率 > 60%
  (月營收成長趨勢過老)
- 連續3個月 "月營收近12個月最小值/近月營收" < 0.8
  (確認營收底部，近月營收脫離近年谷底)
- H02_03: 營收月增率連續 3 個月 > -40%
- F06_04: 近 10 日成交量平均 > 200 張
- 以上選 10 日成交均量最小 5 個 
  (買比較冷門的股票)

