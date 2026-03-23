-- 1) 异常业务数
SELECT COUNT(*) AS alert_count
FROM fact_alerts;

-- 2) 总进审量
SELECT SUM(total_count) AS total_review_count
FROM biz_summary_latest;

-- 3) 最新状态分布
SELECT status, COUNT(*) AS biz_count
FROM biz_summary_latest
GROUP BY status
ORDER BY status;

-- 4) 分组总进审量
SELECT biz_group, SUM(total_count) AS total_count
FROM biz_summary_latest
GROUP BY biz_group
ORDER BY total_count DESC;
