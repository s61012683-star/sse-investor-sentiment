# SSE Investor Sentiment

本项目整理并重构了东方财富股吧文本爬取、GLM-4-Flash 情绪识别、每日指标计算和关键词统计代码，用于研究宏观政策讨论、社交媒体情绪与上证指数波动之间的关系。

项目主题参考：

> Investor Sentiment and SSE Index Volatility: Evidence from the "927" Policy Discussions

## Pipeline

```text
东方财富股吧帖子
    -> Selenium 爬虫
    -> GLM-4-Flash 情绪分类
    -> 每日信息量与情绪指数
    -> 关键词与词频
```

## Repository layout

```text
.
├─ src/
│  ├─ crawler.py       # 股吧帖子爬虫
│  ├─ sentiment.py     # GLM-4-Flash 情绪分类
│  ├─ metrics.py       # 每日信息量和情绪指数
│  └─ keywords.py      # jieba 分词与词频
├─ scripts/
│  └─ run_pipeline.py  # 管线入口
├─ .env.example
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## Setup

建议使用 Python 3.10 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

复制环境变量模板，并填写自己的智谱 API Key：

```powershell
Copy-Item .env.example .env
$env:ZHIPUAI_API_KEY="your_api_key"
$env:ZHIPUAI_MODEL="glm-4-flash"
```

`.env` 已在 `.gitignore` 中排除。不要把 API Key、Cookie 或账号信息写入代码。

## Usage

爬取指定页码和日期窗口的帖子：

```powershell
python scripts/run_pipeline.py crawl `
  --symbol zssh000001 `
  --start-page 31720 `
  --end-page 31774 `
  --start-date 2024-03-24 `
  --end-date 2025-03-24 `
  --output data/posts.jsonl
```

对帖子进行情绪分类：

```powershell
python scripts/run_pipeline.py sentiment `
  --input data/posts.jsonl `
  --output data/labeled_posts.jsonl
```

计算每日信息量和情绪指数：

```powershell
python scripts/run_pipeline.py metrics `
  --input data/labeled_posts.jsonl `
  --formula ratio `
  --output data/daily_metrics.csv
```

统计高频词：

```powershell
python scripts/run_pipeline.py keywords `
  --input data/labeled_posts.jsonl `
  --top-k 100 `
  --output data/keywords.csv
```

## Output schemas

`posts.jsonl`

```json
{"date":"2024-09-27","text":"帖子正文","source_url":"https://guba.eastmoney.com/list,zssh000001_31721.html"}
```

`labeled_posts.jsonl`

```json
{"date":"2024-09-27","text":"帖子正文","source_url":"https://guba.eastmoney.com/list,zssh000001_31721.html","sentiment":1}
```

`daily_metrics.csv` fields:

```text
date,info_count,positive,neutral,negative,sentiment_index
```

默认情绪指数采用论文中的口径：

```text
sentiment_index = (positive - negative) / (positive + negative)
```

如需复现 notebook 中的对数版本，可将 `--formula` 改为 `log-ratio`。

## Data and compliance

- 仓库不包含原始帖子、Excel、PPT、Word、压缩包或 API Key。
- 爬虫仅用于学术研究。运行前请确认目标网站的服务条款、访问频率限制和适用法律。
- 请合理设置页数、延时和请求频率，不要对目标网站造成额外负担。
- 原始帖子可能包含个人信息或敏感内容，公开数据前应完成脱敏并确认授权。

## Notes

原始课程材料中的 Python 代码位于 Notebook 内，且包含明文 API Key。本仓库仅保留重构后的主要代码，不提交原始 Notebook 和数据材料。原 Key 应立即在智谱平台作废并重新生成。
