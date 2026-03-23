-- 1) 总进审量趋势
SELECT date, SUM(total_count) AS total_count
FROM fact_daily_metrics
GROUP BY date
ORDER BY date;

-- 2) 平均推审率趋势
SELECT date, AVG(push_rate) AS avg_push_rate
FROM fact_daily_metrics
GROUP BY date
ORDER BY date;

-- 3) 平均违规率趋势
SELECT date, AVG(violation_rate) AS avg_violation_rate
FROM fact_daily_metrics
GROUP BY date
ORDER BY date;

-- 4) 指定业务近30天趋势（按 Metabase 变量替换 {{biz_name}}）
SELECT date, biz_name, total_count, push_rate, violation_rate
FROM biz_trend_30d
WHERE biz_name = {{biz_name}}
ORDER BY date;
