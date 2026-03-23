-- 1) 最新异常列表
SELECT biz_name, biz_group, status, alert_level, alert_reason,
       freshness_days, total_count, push_rate, violation_rate, source_file
FROM fact_alerts
ORDER BY CASE alert_level WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
         freshness_days DESC,
         total_count DESC;

-- 2) 最新快照明细
SELECT biz_name, biz_group, status, freshness_label,
       total_count, push_rate, violation_rate,
       total_vs_7d_pct_point, push_vs_7d_pct_point, vio_vs_7d_pct_point
FROM biz_summary_latest
ORDER BY status, biz_group, biz_name;
