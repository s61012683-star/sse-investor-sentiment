# SSE Investor Sentiment

This repository contains a Python Notebook for collecting Eastmoney Stock Bar posts and analyzing investor sentiment for the Shanghai Composite Index.

## File

- `guba_sentiment_analysis.ipynb`: crawler, sentiment classification, daily information volume, sentiment index, and keyword analysis.

## Run

1. Install the dependencies:

   ```powershell
   pip install selenium zhipuai jieba
   ```

2. Replace `YOUR_ZHIPUAI_API_KEY` in the Notebook with your Zhipu API key.

3. Adjust the page numbers in `range(...)` before running. The correct pages depend on the target dates and will change as Eastmoney updates its pages. Find the first and last pages corresponding to the required dates in Guba, then update the range accordingly.

4. Run the cells in order.
