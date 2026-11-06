# 投资日历订阅（Investment Calendar）

一份可订阅到 iPhone / Mac 日历的投资事件日历，覆盖 A股、美股、港股相关的宏观数据、政策会议、公司财报、市场休市与产业会议。

所有事件均标注北京时间与数据来源，日期以官方发布日程为准。

## 订阅地址

优先使用 **GitHub Pages**（国内访问较稳定）：

```
https://suplinzy.github.io/investment-calendar/investment-calendar.ics
```

备用 **jsDelivr CDN**（国内有节点）：

```
https://cdn.jsdelivr.net/gh/Suplinzy/investment-calendar@main/investment-calendar.ics
```

原始地址（`raw.githubusercontent.com`，国内可能无法直连）：

```
https://raw.githubusercontent.com/Suplinzy/investment-calendar/main/investment-calendar.ics
```

### iPhone 添加订阅日历

设置 → 日历 → 账户 → 添加账户 → 其他 → 添加已订阅的日历 → 粘贴上面任一链接 → 存储。

### Mac 添加订阅日历

日历 App → 文件 → 新建日历订阅 → 粘贴链接 → 订阅。

## 文件结构

```
investment-calendar/
├── data/
│   └── events.json            # 事件主数据（唯一真相源，只追加不删）
├── gen_ics.py                 # 生成器：JSON -> .ics
├── investment-calendar.ics    # 订阅输出（每次全量重写）
└── README.md
```

## 更新机制

由本地自动化每月执行一次：

1. 联网核实下月官方日程（BLS / 美联储 / 国家统计局 / 央行 / 海关总署 / 交易所 / 财报 / 会展）
2. 将新事件**追加**到 `data/events.json`（历史事件永不删除）
3. 运行 `python3 gen_ics.py` 重新生成 `.ics`
4. `git commit` + `git push`
5. iPhone 在下一次同步时自动拉取最新内容

## 关键设计：稳定 UID

每个事件在 `data/events.json` 中有唯一的语义化 `key`，例如：

- `CN_CPI_2026-10`（中国 2026 年 10 月 CPI）
- `US_NFP_2026-10`（美国 2026 年 10 月非农）
- `CN_LPR_2026-11`（2026 年 11 月 LPR 报价）

输出的 `UID` 固定为 `<key>@investment-calendar`。

这样即使官方临时调整某个事件的日期，重新生成后 UID 不变，iPhone 会**更新**该事件而非**新增**重复事件。这是订阅日历最关键的技术保障。

## 事件分类

标题前缀用于在日历视图中快速辨识类别：

| 前缀 | 类别 | 内容 |
|------|------|------|
| 【国内】 | 国内宏观 | 中国 PMI、CPI、PPI、进出口、社融、工增社零、房价、工业企业利润 |
| 【海外】 | 海外宏观 | 美国非农、CPI、PPI、零售销售、PCE、GDP |
| 【政策】 | 政策会议 | FOMC 决议与纪要、褐皮书、LPR、中期选举 |
| 【财报】 | 公司财报 | 英伟达、苹果、高通等影响持仓 ETF 的龙头 |
| 【休市】 | 市场休市 | 美股/美债/港股休市与提前收盘 |
| 【会议】 | 会议展览 | APEC、进博会、高交会、车展、乌镇峰会 |

## 数据来源

- 美国劳工统计局（BLS）发布日程
- 美国经济分析局（BEA）
- 美联储（Federal Reserve）日程
- 国家统计局 2026 年主要统计信息发布日程
- 中国人民银行（LPR、金融数据）
- 海关总署
- NYSE / Nasdaq / HKEX 休市安排
- 各公司投资者关系页面
- 会议主办方官方日程

## 免责声明

本日历仅为公开信息整理，用于个人日程提醒，不构成任何投资建议。部分数据发布日期（如央行金融数据）为窗口预计值，以官方实际公告为准。
