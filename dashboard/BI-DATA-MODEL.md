# 看板通用数据模型

这套模型用于支持 Metabase / Superset / Retool / Power BI / Tableau 等工具自由搭建。

## 1. fact_daily_metrics
按日、按业务的明细事实表。

核心字段：
- date
- biz_name
- biz_group
- total_count
- push_rate
- violation_rate
- review_count
- reject_count
- error_value
- base_status
- total_7d_avg
- push_rate_7d_avg
- violation_rate_7d_avg
- total_vs_7d_pct
- push_vs_7d_pct
- vio_vs_7d_pct
- source_file

适用：趋势图、历史回溯、明细分析。

## 2. dim_business
业务维表。

核心字段：
- business_name
- business_group
- default_status
- latest_source_file

适用：筛选器、业务分组、映射说明。

## 3. biz_summary_latest
最新日期快照表。

核心字段：
- biz_name
- biz_group
- date
- status
- freshness_days
- freshness_label
- total_count
- push_rate
- violation_rate
- review_count
- reject_count
- error_value
- total_7d_avg
- push_rate_7d_avg
- violation_rate_7d_avg
- total_vs_7d_pct_point
- push_vs_7d_pct_point
- vio_vs_7d_pct_point
- source_file

适用：首页总览、异常列表、最新状态分布。

## 4. fact_alerts
预警/异常表。

核心字段：
- date
- biz_name
- biz_group
- status
- alert_level
- alert_reason
- freshness_days
- total_count
- push_rate
- violation_rate
- source_file

适用：异常页、预警列表、待排查列表。

## 5. biz_trend_30d
近 30 天趋势表。

适用：单业务趋势、多业务趋势、7日均对比。
