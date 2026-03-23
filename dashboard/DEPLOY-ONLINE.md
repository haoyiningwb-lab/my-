# 线上部署成品说明（10点自动更新版）

## 目标
- 每天 10:00 自动把最新数据同步到线上仓库
- Streamlit Cloud 读取仓库内 `dashboard/exports/` 数据
- 所有人打开同一链接，都能看到最新版本

## 线上运行入口
- `dashboard/app_cloud.py`

## 数据来源
- `dashboard/exports/*.csv`
- 线上页默认直接读取仓库内导出的 CSV 文件

## 本地同步脚本
- `dashboard/sync_to_repo.sh`

## 每天 10:00 自动更新流程
1. 本地自动化脚本先完成抓取和落地
2. 10:00 执行：
   ```bash
   cd /Users/haoyining/.openclaw/workspace/dashboard
   bash sync_to_repo.sh <仓库根目录> main
   ```
3. 脚本会自动：
   - 导出最新 CSV / DuckDB / SQLite
   - 提交 `dashboard/exports/`
   - push 到远程仓库
4. Streamlit Cloud 会读取仓库里的最新数据

## Streamlit Cloud 配置
- Repository: 你的 GitHub 仓库
- Main file path: `dashboard/app_cloud.py`
- Python version: 3.11+ 推荐

## 注意
- 线上版不能直接读取你本机 Desktop 文件
- 所以必须先把本地最新数据导出并同步进仓库
- 只要仓库数据更新，线上访问者看到的就是统一更新后的结果
