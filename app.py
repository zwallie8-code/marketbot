name: Rank Stocks with GPT

on:
  workflow_dispatch:
  workflow_run:
    workflows: ["Update Stock Market Dataset"]
    types:
      - completed

jobs:
  rank-stocks:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Rank stocks with GPT
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/gpt_rank_stocks.py

      - name: Upload ranked stocks file
        uses: actions/upload-artifact@v4
        with:
          name: ranked-stocks
          path: output/ranked_stocks.csv

      - name: Commit and push results
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add output/ranked_stocks.csv
          git commit -m "Update ranked stocks [skip ci]" || echo "No changes to commit"
          git push origin main
