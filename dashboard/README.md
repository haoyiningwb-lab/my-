# 业务数据看板（第一版）

## 目标
- 从本地落地的 xlsx 文件读取业务数据
- 生成总览、趋势、异常三类可视化页面
- 优先服务日常监控与异常排查

## 当前实现
- 数据源：`~/Desktop/全自动运行表格保存/*.xlsx`
- 技术栈：Streamlit + Plotly + openpyxl + pandas
- 页面内容：
  - 最新总览指标
  - 总进审量趋势
  - 推审率/违规率趋势
  - 最新状态分布
  - 异常业务清单
  - 业务明细表
  - 单业务趋势查看

## 启动方式
```bash
cd /Users/haoyining/.openclaw/workspace/dashboard
streamlit run app.py
```

## BI 通用数据导出
```bash
cd /Users/haoyining/.openclaw/workspace/dashboard
python3 export_bi_data.py
```

导出后会生成：
- `exports/fact_daily_metrics.csv`
- `exports/dim_business.csv`
- `exports/biz_summary_latest.csv`
- `exports/fact_alerts.csv`
- `exports/biz_trend_30d.csv`

这些文件可以直接拿去接 Metabase / Superset / Retool / Power BI / Tableau。

## DuckDB 导出
```bash
cd /Users/haoyining/.openclaw/workspace/dashboard
python3 export_duckdb.py
```

导出后会生成：
- `exports/dashboard.duckdb`

## SQLite 导出
```bash
cd /Users/haoyining/.openclaw/workspace/dashboard
python3 export_sqlite.py
```

导出后会生成：
- `exports/dashboard.sqlite`

## 文档
- `BI-DATA-MODEL.md`：通用数据模型说明
- `BI-TOOLS-SUGGESTION.md`：工具选择建议
- `METABASE-SETUP.md`：Metabase 接入建议
- `METABASE-DASHBOARD-TEMPLATE.md`：Metabase 仪表盘搭建模板
- `metabase_sql/`：Metabase 可直接参考的查询 SQL

## 下一步建议
- 增加规则配置页
- 增加日报回溯页
- 增加更精致的主题样式和品牌化配色
- 如果需要，我可以继续补 PostgreSQL 导出和一键启动脚本
