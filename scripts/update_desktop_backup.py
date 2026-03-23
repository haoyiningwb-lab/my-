#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil

WORKSPACE = Path("/Users/haoyining/.openclaw/workspace")
DESKTOP = Path.home() / "Desktop"
CN_DIR = DESKTOP / "备份"
EN_DIR = DESKTOP / "OpenClaw-Agent-Backups"
CN_LATEST = CN_DIR / "代理备份-最新.md"
EN_LATEST = EN_DIR / "agent-backup-latest.md"

IDENTITY = WORKSPACE / "IDENTITY.md"
USER = WORKSPACE / "USER.md"
MEMORY = WORKSPACE / "MEMORY.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def section(title: str, body: str) -> str:
    body = body.strip() if body else "(empty)"
    return f"## {title}\n\n{body}\n"


def render_cn(now: datetime) -> str:
    return "\n".join([
        "# 代理备份-最新",
        "",
        f"> 更新时间：{now.strftime('%Y-%m-%d %H:%M:%S %Z') or 'Asia/Shanghai'}",
        "> 说明：当出现重要变化，或用户明确要求增加备份时，主动更新本文件。",
        "",
        section("身份（来自 IDENTITY.md）", read_text(IDENTITY)),
        section("用户信息（来自 USER.md）", read_text(USER)),
        section("长期记忆与规则（来自 MEMORY.md）", read_text(MEMORY)),
        "## 维护规则\n\n- 本文件是桌面固定恢复备份。\n- 发生重要变化时应主动更新。\n- 如需双份同步，需同时更新 OpenClaw-Agent-Backups/agent-backup-latest.md。\n",
    ])


def render_en(now: datetime) -> str:
    return "\n".join([
        "# Agent Backup - Latest",
        "",
        f"> Updated: {now.isoformat(timespec='seconds')}",
        "> Rule: proactively refresh this backup when important context changes or when the user explicitly asks for another backup.",
        "",
        section("Identity (from IDENTITY.md)", read_text(IDENTITY)),
        section("User profile (from USER.md)", read_text(USER)),
        section("Long-term memory and rules (from MEMORY.md)", read_text(MEMORY)),
        "## Maintenance rules\n\n- This is a fixed Desktop recovery backup.\n- Refresh it proactively after important changes.\n- Keep it aligned with 备份/代理备份-最新.md.\n",
    ])


def archive_latest(latest: Path, archive_prefix: str, now: datetime) -> None:
    if latest.exists():
        archive = latest.parent / f"{archive_prefix}-{now.strftime('%Y-%m-%d-%H%M%S')}.md"
        shutil.copy2(latest, archive)


def main() -> None:
    now = datetime.now().astimezone()
    CN_DIR.mkdir(parents=True, exist_ok=True)
    EN_DIR.mkdir(parents=True, exist_ok=True)

    archive_latest(CN_LATEST, "代理备份", now)
    archive_latest(EN_LATEST, "agent-backup", now)

    CN_LATEST.write_text(render_cn(now), encoding="utf-8")
    EN_LATEST.write_text(render_en(now), encoding="utf-8")

    print(f"Updated: {CN_LATEST}")
    print(f"Updated: {EN_LATEST}")


if __name__ == "__main__":
    main()
