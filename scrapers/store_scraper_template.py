"""Template scraper for adding an Australian store.

Important:
- Check each retailer's terms of use before scraping.
- Some stores render prices with JavaScript, block bots, or vary pricing by postcode.
- For some shops, CSV import or manual update will be more reliable.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
import requests
from bs4 import BeautifulSoup


@dataclass
class PriceRow:
    whisky: str
    expression: str
    brand: str
    age: str
    abv: str
    size_ml: int
    store: str
    state: str
    price_aud: float
    in_stock: bool
    product_url: str
    last_seen: str
    source: str


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def scrape_example_product() -> dict:
    url = "https://example.com/product-page"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Replace these selectors with the real ones for the target store.
    product_name = soup.select_one("h1")
    price_el = soup.select_one(".price")
    stock_el = soup.select_one(".stock")

    row = PriceRow(
        whisky=product_name.get_text(strip=True) if product_name else "Unknown",
        expression="",
        brand="",
        age="",
        abv="",
        size_ml=700,
        store="Example Store",
        state="AU",
        price_aud=float(price_el.get_text(strip=True).replace("$", "")) if price_el else 0.0,
        in_stock=(stock_el and "in stock" in stock_el.get_text(" ", strip=True).lower()),
        product_url=url,
        last_seen=str(date.today()),
        source="scraper",
    )
    return asdict(row)
