# Whisky Price Dashboard AU

A local Streamlit dashboard for comparing whisky prices across Australian stores.

## What it does

- Compares prices across stores
- Shows the cheapest seller for each whisky
- Calculates price per 100mL
- Lets you filter by brand, whisky, store, stock, bottle size, and free-text search
- Supports a second CSV for price history trends
- Exports filtered results to CSV or Excel

## Quick start

```bash
cd whisky_price_dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown in the terminal.

## Files

- `app.py` — main dashboard
- `data/sample_whisky_prices.csv` — sample current-price dataset
- `data/sample_price_history.csv` — sample price-history dataset
- `scrapers/store_scraper_template.py` — starter template for your own store scrapers

## CSV format

### Current prices CSV

Required columns:

- `whisky`
- `expression`
- `brand`
- `age`
- `abv`
- `size_ml`
- `store`
- `state`
- `price_aud`
- `in_stock`
- `product_url`
- `last_seen`
- `source`

### History CSV

Required columns:

- `whisky`
- `store`
- `price_aud`
- `checked_at`

## How to expand it

### Option 1: Manual updates
Export prices from websites or paste them into the sample CSV.

### Option 2: Semi-automated
Use a small scraper per store and append fresh rows to the CSV. Start from `scrapers/store_scraper_template.py`.

### Option 3: Full history tracking
Create a scheduled job that:
1. Scrapes or updates current prices.
2. Writes the latest snapshot to `sample_whisky_prices.csv`.
3. Appends a record to `sample_price_history.csv`.

## Notes

- Postcode-based pricing is common in Australia, so final checkout price can differ.
- Some stores use anti-bot protection or client-side rendering. In those cases, manual CSV updates may be more reliable than scraping.
- Respect each retailer's terms before automating collection.


## GitHub + GitHub Actions Setup

This app is a Streamlit app. GitHub Actions can:
- run checks automatically on every push
- build and publish a Docker image to GitHub Container Registry (GHCR)

GitHub itself does **not** permanently host Streamlit apps the way it hosts static GitHub Pages sites.

### What is included
- `.github/workflows/ci.yml` — basic CI on push and pull requests
- `.github/workflows/docker-publish.yml` — builds and publishes a Docker image to GHCR
- `Dockerfile` — container image for deployment
- `.gitignore`

### Push to GitHub
```bash
git init
git add .
git commit -m "Initial whisky dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Run with Docker
```bash
docker build -t whisky-dashboard .
docker run -p 8501:8501 whisky-dashboard
```

Then open `http://localhost:8501`

### Deploy options
The easiest places to deploy this after pushing to GitHub are:
- Streamlit Community Cloud
- Render
- Railway
- Fly.io
- Azure Web App / AWS App Runner / ECS

If you want a fully automated deploy from GitHub Actions, connect the repo to a Docker-based host such as Render, Railway, Fly.io, or AWS App Runner.
