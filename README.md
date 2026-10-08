# SSE Investor Sentiment

This repository contains the original Python workflow for collecting Eastmoney Stock Bar posts and analyzing investor sentiment around major policy events.

## Files

- `guba_sentiment_analysis.ipynb`: the original Notebook code.
- `requirements.txt`: Python packages required by the Notebook.

## Run

1. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

2. Replace `YOUR_ZHIPUAI_API_KEY` in the Notebook with your Zhipu API key.
3. Open the Notebook and run the cells in order.

The Notebook uses Selenium, GLM-4-Flash, and jieba for crawling, sentiment classification, daily index construction, and keyword counting.