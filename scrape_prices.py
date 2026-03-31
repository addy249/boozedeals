
from __future__ import annotations

from pathlib import Path
from datetime import datetime, UTC
import re
import sys

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
INPUT_CSV = DATA_DIR / "sample_whisky_prices.csv"
OUTPUT_CSV = DATA_DIR / "live_prices.csv"

# Add exact product URLs here. Only rows with a verified product_url are refreshed.
# Keys must match the whisky and store columns in sample_whisky_prices.csv.
VERIFIED_URLS = {
    ("Glenfiddich 12YO", "BWS"): "https://bws.com.au/product/17621/glenfiddich-12-year-old-single-malt-scotch-whisky-700ml",
}

STORE_SELECTORS = {
    "BWS": [
        'text=/\$ ?\d{1,4}(\.\d{2})?/',
        '[data-testid*="price"]',
        '[class*="price"]',
        'meta[property="product:price:amount"]',
    ],
    "Dan Murphy's": [
        'text=/\$ ?\d{1,4}(\.\d{2})?/',
        '[data-testid*="price"]',
        '[class*="price"]',
    ],
    "Liquorland": [
        'text=/\$ ?\d{1,4}(\.\d{2})?/',
        '[data-testid*="price"]',
        '[class*="price"]',
    ],
    "First Choice": [
        'text=/\$ ?\d{1,4}(\.\d{2})?/',
        '[data-testid*="price"]',
        '[class*="price"]',
    ],
}

MONEY_RE = re.compile(r"\$ ?([0-9]{1,4}(?:\.[0-9]{2})?)")


def read_input() -> pd.DataFrame:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    if "product_url" not in df.columns:
        df["product_url"] = ""
    if "status" not in df.columns:
        df["status"] = ""
    return df


def clean_money(text: str) -> float | None:
    if not text:
        return None
    m = MONEY_RE.search(text.replace(",", ""))
    if not m:
        return None
    value = float(m.group(1))
    if 20 <= value <= 2000:
        return value
    return None


def extract_price_from_page(page, store: str) -> float | None:
    selectors = STORE_SELECTORS.get(store, [])
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(timeout=3000)
            text = locator.get_attribute("content") if selector.startswith("meta[") else locator.inner_text()
            price = clean_money(text or "")
            if price is not None:
                return price
        except Exception:
            pass

    # Fallback to page text
    try:
        text = page.content()
        values = [float(v) for v in MONEY_RE.findall(text.replace(",", ""))]
        values = [v for v in values if 20 <= v <= 2000]
        return values[0] if values else None
    except Exception:
        return None


def refresh_prices(df: pd.DataFrame) -> pd.DataFrame:
    refreshed = df.copy()
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="en-AU",
            timezone_id="Australia/Melbourne",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        for idx, row in refreshed.iterrows():
            whisky = str(row.get("whisky", ""))
            store = str(row.get("store", ""))
            verified_url = VERIFIED_URLS.get((whisky, store)) or str(row.get("product_url") or "").strip()

            if not verified_url:
                refreshed.at[idx, "status"] = "No verified URL"
                continue

            try:
                page.goto(verified_url, wait_until="domcontentloaded", timeout=45000)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass

                price = extract_price_from_page(page, store)
                if price is None:
                    refreshed.at[idx, "status"] = "Live parse failed"
                    refreshed.at[idx, "product_url"] = verified_url
                    continue

                refreshed.at[idx, "price_aud"] = float(price)
                refreshed.at[idx, "product_url"] = verified_url
                refreshed.at[idx, "last_seen"] = now
                refreshed.at[idx, "source"] = "saved_live_scrape"
                refreshed.at[idx, "status"] = "Verified live"
            except PlaywrightTimeoutError:
                refreshed.at[idx, "product_url"] = verified_url
                refreshed.at[idx, "status"] = "Live request timed out"
            except Exception as e:
                refreshed.at[idx, "product_url"] = verified_url
                refreshed.at[idx, "status"] = f"Live request failed: {type(e).__name__}"

        context.close()
        browser.close()

    return refreshed


def main() -> int:
    df = read_input()
    refreshed = refresh_prices(df)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    refreshed.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {OUTPUT_CSV}")
    ok = (refreshed["status"] == "Verified live").sum()
    print(f"Verified live rows: {ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
