# Metabase 接入说明

## 目标
使用 `dashboard/exports/dashboard.duckdb` 作为统一数据源，在 Metabase 中自由搭建图表与仪表盘。

## 当前推荐方式
Metabase 对 DuckDB 的原生支持不如 PostgreSQL / MySQL 稳定，因此推荐两条路：

### 路线 A（最快）
先使用导出的 CSV 文件，在外部数据库（PostgreSQL / SQLite 转存 / MySQL）中建表，再接入 Metabase。

### 路线 B（更轻量）
若你本地有支持 DuckDB 的查询中间层，也可以把 DuckDB 作为分析层，再定时同步到 Metabase 可连接的数据源。

## 建议优先接入的表
- `biz_summary_latest`：做首页总览、状态分布、最新异常列表
- `fact_alerts`：做预警页、待排查页
- `biz_trend_30d`：做趋势图
- `fact_daily_metrics`：做历史明细与钻取
- `dim_business`：做筛选器映射

## 推荐仪表盘结构
### 1. 首页总览
- 最新日期
- 异常业务数
- 红黄业务数
- 总进审量
- 平均推审率
- 平均违规率
- 最新状态分布

### 2. 趋势页
- 总进审量趋势
- 关键业务趋势
- 推审率 / 违规率趋势
- 7日均量对比

### 3. 异常页
- 今日异常列表
- 数据滞后列表
- 量级偏差排名
- 高推审率高违规率列表

## 导出步骤
```bash
cd /Users/haoyining/.openclaw/workspace/dashboard
python3 export_bi_data.py
python3 export_duckdb.py
```

输出目录：
- `exports/*.csv`
- `exports/dashboard.duckdb`
