# Metabase 仪表盘模板（可直接照着搭）

## 仪表盘 1：首页总览

### 卡片 1：最新日期
数据表：`biz_summary_latest`
字段：`date`
聚合：最大值 / 文本展示

### 卡片 2：异常业务数
数据表：`fact_alerts`
聚合：`count(*)`

### 卡片 3：总进审量
数据表：`biz_summary_latest`
字段：`total_count`
聚合：求和

### 图表 1：最新状态分布
数据表：`biz_summary_latest`
维度：`status`
指标：`count(*)`
图表：柱状图 / 饼图

### 图表 2：分组总进审量
数据表：`biz_summary_latest`
维度：`biz_group`
指标：`sum(total_count)`
图表：横向条形图

## 仪表盘 2：趋势页

### 图表 1：总进审量趋势
数据表：`fact_daily_metrics`
维度：`date`
指标：`sum(total_count)`
图表：折线图

### 图表 2：平均推审率趋势
数据表：`fact_daily_metrics`
维度：`date`
指标：`avg(push_rate)`
图表：折线图

### 图表 3：平均违规率趋势
数据表：`fact_daily_metrics`
维度：`date`
指标：`avg(violation_rate)`
图表：折线图

### 图表 4：单业务近30天趋势
数据表：`biz_trend_30d`
筛选：`biz_name`
图表：折线图

## 仪表盘 3：异常排查页

### 表 1：最新异常列表
数据表：`fact_alerts`
列：
- biz_name
- biz_group
- status
- alert_level
- alert_reason
- freshness_days
- total_count
- push_rate
- violation_rate

### 表 2：最新快照明细
数据表：`biz_summary_latest`
列：
- biz_name
- biz_group
- status
- freshness_label
- total_count
- push_rate
- violation_rate
- total_vs_7d_pct_point

## 推荐筛选器
- 日期（date）
- 业务分组（biz_group）
- 业务（biz_name）
- 状态（status）
- 预警等级（alert_level）
