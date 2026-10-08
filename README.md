# SSE Investor Sentiment

This repository contains the Python workflow for collecting Eastmoney Stock Bar posts and analyzing investor sentiment around major policy events.

## Files

- `guba_sentiment_analysis.ipynb`: the original Notebook with saved execution results.
- `guba_sentiment_analysis_clean.ipynb`: a code-only 20-page test version with outputs cleared.
- `requirements.txt`: Python packages required by the Notebook.

## Run

1. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

2. Replace `YOUR_ZHIPUAI_API_KEY` in the Notebook with your Zhipu API key.
3. For a small test, open `guba_sentiment_analysis_clean.ipynb` and run the cells in order.