#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资日历 .ics 生成器

数据源：data/events.json（唯一真相源，只追加不删）
输出：investment-calendar.ics

核心设计：
1. UID 使用语义化稳定 key（如 CN_CPI_2026-10@investment-calendar），
   保证同一事件每次生成 UID 不变 —— 避免 iPhone 出现重复事件。
2. 全量重写输出文件，历史事件永久保留。
3. 所有时间按北京时间（Asia/Shanghai）写入。
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

TZ_CN = timezone(timedelta(hours=8))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "events.json")
OUT_FILE = os.path.join(BASE_DIR, "investment-calendar.ics")

# 标题前缀，用于在 iPhone 日历中快速辨识类别
CAT_PREFIX = {
    "国内宏观": "【国内】",
    "海外宏观": "【海外】",
    "政策会议": "【政策】",
    "公司财报": "【财报】",
    "市场休市": "【休市】",
    "会议展览": "【会议】",
}


def esc(text):
    """转义 ICS TEXT 类型的保留字符"""
    if not text:
        return ""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def fold(line):
    """RFC5545 折行：每行不超过 75 个八位组"""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    result = []
    cur = b""
    limit = 75
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > limit:
            result.append(cur.decode("utf-8"))
            cur = b
            limit = 74  # 续行首是一个空格，占 1 字节
        else:
            cur += b
    if cur:
        result.append(cur.decode("utf-8"))
    return "\r\n ".join(result)


def build_event(ev):
    """把单个事件转为 VEVENT 行列表"""
    key = ev["key"]
    date_str = ev["date"]
    allday = ev.get("allday", False) or ("time" not in ev)

    lines = ["BEGIN:VEVENT"]
    # UID 稳定：key + 域名
    lines.append(f"UID:{key}@investment-calendar")
    lines.append(f"DTSTAMP:{datetime.now(TZ_CN).strftime('%Y%m%dT%H%M%S')}Z")

    if allday:
        start = datetime.strptime(date_str, "%Y-%m-%d")
        # 多天事件用 end_date，否则默认 1 天
        if ev.get("end_date"):
            end = datetime.strptime(ev["end_date"], "%Y-%m-%d")
        else:
            end = start + timedelta(days=1)
        lines.append(f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}")
        lines.append(f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}")
    else:
        start = datetime.strptime(f"{date_str} {ev['time']}", "%Y-%m-%d %H:%M")
        start_local = start.replace(tzinfo=TZ_CN)
        dur = int(ev.get("duration_min", 30))
        end_local = start_local + timedelta(minutes=dur)
        lines.append(
            f"DTSTART;TZID=Asia/Shanghai:{start_local.strftime('%Y%m%dT%H%M%S')}"
        )
        lines.append(
            f"DTEND;TZID=Asia/Shanghai:{end_local.strftime('%Y%m%dT%H%M%S')}"
        )

    cat = ev.get("category", "")
    prefix = CAT_PREFIX.get(cat, "")
    lines.append(fold(f"SUMMARY:{esc(prefix + ev['title'])}"))
    lines.append(f"CATEGORIES:{esc(cat)}")

    # 描述 = 说明 + 影响板块 + 来源
    desc_parts = []
    if ev.get("desc"):
        desc_parts.append(ev["desc"])
    if ev.get("impact"):
        desc_parts.append(f"影响板块：{ev['impact']}")
    if ev.get("source"):
        desc_parts.append(f"数据来源：{ev['source']}")
    if desc_parts:
        lines.append(fold(f"DESCRIPTION:{esc(chr(10).join(desc_parts))}"))

    lines.append("TRANSP:OPAQUE")

    # 可选提醒：提前 N 分钟
    alarm = ev.get("alarm_min")
    if alarm is not None:
        lines.append("BEGIN:VALARM")
        lines.append("ACTION:DISPLAY")
        lines.append(fold(f"DESCRIPTION:{esc(ev['title'])}"))
        lines.append(f"TRIGGER:-PT{int(alarm)}M")
        lines.append("END:VALARM")

    lines.append("END:VEVENT")
    return lines


def main():
    if not os.path.exists(DATA_FILE):
        print(f"错误：找不到数据文件 {DATA_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    cal = data.get("calendar", {})
    events = data.get("events", [])

    def sort_key(e):
        return (e.get("date", ""), e.get("time", "00:00"), e.get("key", ""))

    events = sorted(events, key=sort_key)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{cal.get('prodid', '-//Lin//Investment Calendar//CN')}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        fold(f"X-WR-CALNAME:{esc(cal.get('name', '投资日历'))}"),
        f"X-WR-TIMEZONE:{cal.get('timezone', 'Asia/Shanghai')}",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H",
        "BEGIN:VTIMEZONE",
        "TZID:Asia/Shanghai",
        "BEGIN:STANDARD",
        "DTSTART:19700101T000000",
        "TZOFFSETFROM:+0800",
        "TZOFFSETTO:+0800",
        "TZNAME:CST",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]

    for ev in events:
        lines.extend(build_event(ev))

    lines.append("END:VCALENDAR")

    with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")

    cats = {}
    for e in events:
        c = e.get("category", "未分类")
        cats[c] = cats.get(c, 0) + 1

    print(f"生成完成：{len(events)} 个事件 -> {OUT_FILE}")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
