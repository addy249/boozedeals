from __future__ import annotations

from pathlib import Path
import io
import json
import re
from html import escape
from urllib.parse import quote_plus

import altair as alt
from bs4 import BeautifulSoup
import pandas as pd
import requests
import streamlit as st

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-AU,en;q=0.9",
}

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DEFAULT_CSV = DATA_DIR / "sample_whisky_prices.csv"
HISTORY_CSV = DATA_DIR / "sample_price_history.csv"

st.set_page_config(page_title="BoozeDeals AU", page_icon="🥃", layout="wide", initial_sidebar_state="collapsed")

STORE_COLORS = {
    "Dan Murphy's": "#14B8A6",
    "BWS": "#F97316",
    "Liquorland": "#3B82F6",
    "First Choice": "#8B5CF6",
}

STORE_META = {
    "Dan Murphy's": {"url": "https://www.danmurphys.com.au/whisky/all", "wordmark": "Dan Murphy's", "short": "DM"},
    "BWS": {"url": "https://bws.com.au/spirits/whisky", "wordmark": "BWS", "short": "BWS"},
    "Liquorland": {"url": "https://www.liquorland.com.au/spirits/whisky", "wordmark": "Liquorland", "short": "LL"},
    "First Choice": {"url": "https://www.firstchoiceliquor.com.au/spirits/whisky", "wordmark": "First Choice", "short": "FC"},
}

DIRECT_PRODUCT_URLS = {
    ("Glenfiddich 12YO", "BWS"): "https://bws.com.au/product/17621/glenfiddich-12-year-old-single-malt-scotch-whisky-700ml",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"], footer, #MainMenu, header {display:none !important;}
        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(249,115,22,0.14), transparent 24%),
                radial-gradient(circle at 100% 0%, rgba(59,130,246,0.09), transparent 25%),
                linear-gradient(180deg, #050913 0%, #08101d 55%, #09111c 100%);
        }
        .block-container {max-width: 1450px; padding-top: 1.1rem; padding-bottom: 3rem;}
        h1, h2, h3 {letter-spacing:-0.03em;}
        .hero {
            background:
                radial-gradient(circle at 82% 18%, rgba(249,115,22,0.28), transparent 22%),
                linear-gradient(135deg, rgba(7,14,28,.98) 0%, rgba(12,20,38,.98) 45%, rgba(70,32,11,.96) 100%);
            border: 1px solid rgba(255,255,255,.08);
            box-shadow: 0 28px 80px rgba(0,0,0,.35);
            border-radius: 30px;
            padding: 2rem 2rem 1.9rem 2rem;
            color: #fff;
        }
        .eyebrow {font-size:.8rem; letter-spacing:.18em; text-transform:uppercase; color:#fbbf24; font-weight:800; margin-bottom:.8rem;}
        .hero-title {font-size:3.2rem; line-height:1.02; font-weight:900; margin:0;}
        .hero-copy {margin-top:.95rem; max-width: 820px; color:#d1d5db; font-size:1.03rem;}
        .hero-badges {display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1rem;}
        .badge {padding:.38rem .72rem; border-radius:999px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.07); color:#f8fafc; font-size:.82rem; font-weight:700;}
        .hero-kicker {display:flex; gap:1rem; flex-wrap:wrap; margin-top:1.2rem; color:#cbd5e1; font-size:.94rem;}
        .hero-kicker b {color:#fff;}
        .best-deal-card {
            background: linear-gradient(135deg, rgba(249,115,22,.18), rgba(12,20,38,.75));
            border: 1px solid rgba(249,115,22,.34);
            border-radius: 24px;
            padding: 1.15rem 1.2rem;
            min-height: 220px;
        }
        .best-deal-label {font-size:.78rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:#fbbf24;}
        .best-deal-price {font-size:2.5rem; font-weight:900; color:#fff; line-height:1; margin:.45rem 0 .35rem 0;}
        .best-deal-name {font-size:1.04rem; color:#fff; font-weight:800;}
        .best-deal-copy {font-size:.93rem; color:#d1d5db; margin-top:.4rem;}
        .section-title {font-size:1.26rem; font-weight:850; color:#f8fafc; margin:.15rem 0 .2rem 0;}
        .section-subtitle {font-size:.92rem; color:#94a3b8; margin:0 0 .9rem 0;}
        .metric-card {
            background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 22px;
            padding: 1rem;
            min-height: 124px;
        }
        .metric-label {font-size:.88rem; color:#94a3b8;}
        .metric-value {font-size:2rem; color:#fff; font-weight:900; margin-top:.25rem; line-height:1.05;}
        .metric-help {font-size:.92rem; color:#cbd5e1; margin-top:.32rem;}
        .store-jump-card {
            background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.025));
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 20px;
            padding: .95rem;
            min-height: 124px;
            text-align:center;
        }
        .logo-dot {
            width: 54px; height: 54px; border-radius: 999px; display:flex; align-items:center; justify-content:center;
            margin: 0 auto .75rem auto; color:#fff; font-weight:900; font-size:1rem; box-shadow:0 14px 30px rgba(0,0,0,.18);
        }
        .store-caption {font-size:1rem; color:#fff; font-weight:800; margin-bottom:.2rem;}
        .store-sub {font-size:.84rem; color:#94a3b8;}
        .offer-card {
            background: linear-gradient(180deg, rgba(15,23,42,.88), rgba(17,24,39,.98));
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 24px;
            padding: 1.05rem;
            min-height: 290px;
            box-shadow: 0 18px 44px rgba(0,0,0,.22);
        }
        .offer-card.best {border-color: rgba(249,115,22,.52); box-shadow: 0 18px 50px rgba(249,115,22,.14);}
        .offer-top {display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.85rem;}
        .store-name {font-size:1.05rem; font-weight:850; color:#fff;}
        .store-chip {font-size:.78rem; font-weight:800; border-radius:999px; padding:.28rem .58rem; color:#fff;}
        .price {font-size:2.08rem; font-weight:900; color:#ffffff; letter-spacing:-0.03em;}
        .subtle {color:#cbd5e1; font-size:.94rem;}
        .muted {color:#94a3b8; font-size:.85rem;}
        .pills {display:flex; gap:.45rem; flex-wrap:wrap; margin-top:.9rem;}
        .pill {display:inline-block; padding:.22rem .56rem; border-radius:999px; font-size:.78rem; font-weight:700; background:rgba(255,255,255,.08); color:#e5e7eb; border:1px solid rgba(255,255,255,.08);}
        .offer-link {display:inline-block; margin-top:1rem; color:#93c5fd; text-decoration:none; font-weight:700;}
        .offer-link:hover {text-decoration:underline;}
        .panel {
            margin-top: 1rem; background: rgba(8,15,28,.76); border: 1px solid rgba(255,255,255,.08);
            border-radius: 24px; padding: 1rem 1rem 1.1rem 1rem; box-shadow: 0 18px 40px rgba(0,0,0,.16);
        }
        .panel-title {font-size:1rem; font-weight:800; color:#fff; margin-bottom:.8rem;}
        .data-note {font-size:.86rem; color:#94a3b8; margin-top:.45rem;}
        div[data-testid="stDataFrame"] {border:1px solid rgba(255,255,255,.08); border-radius:18px; overflow:hidden;}
        .stTabs [data-baseweb="tab-list"] {gap: 0.5rem;}
        .stTabs [data-baseweb="tab"] {background: rgba(255,255,255,.03); border-radius: 999px; padding-inline: .9rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def _money_values(text: str) -> list[float]:
    vals: list[float] = []
    for m in re.finditer(r"\$\s*([0-9]{1,4}(?:\.[0-9]{2})?)", text):
        try:
            vals.append(float(m.group(1)))
        except ValueError:
            pass
    return vals


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_html(url: str) -> str:
    if not url:
        return ""
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=25)
    resp.raise_for_status()
    return resp.text


def build_search_url(store: str, whisky: str) -> str:
    q = quote_plus(whisky)
    if store == "Dan Murphy's":
        return f"https://www.danmurphys.com.au/whisky/all?search={q}"
    if store == "BWS":
        return f"https://bws.com.au/spirits/whisky?search={q}"
    if store == "Liquorland":
        return f"https://www.liquorland.com.au/spirits/whisky?search={q}"
    if store == "First Choice":
        return f"https://www.firstchoiceliquor.com.au/spirits/whisky?search={q}"
    return ""


def json_ld_prices(soup: BeautifulSoup) -> list[float]:
    prices: list[float] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = (tag.string or tag.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for k, v in item.items():
                    if k.lower() == "price":
                        try:
                            prices.append(float(str(v).replace(",", "")))
                        except Exception:
                            pass
                    else:
                        stack.append(v)
            elif isinstance(item, list):
                stack.extend(item)
    return [p for p in prices if 20 <= p <= 2000]


def extract_live_price(row: pd.Series, html: str) -> float | None:
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")

    # 1) direct metadata first
    meta_candidates = []
    meta_selectors = [
        ("meta", {"property": "product:price:amount"}),
        ("meta", {"property": "og:price:amount"}),
        ("meta", {"itemprop": "price"}),
        ("meta", {"name": "twitter:data1"}),
    ]
    for tag_name, attrs in meta_selectors:
        for tag in soup.find_all(tag_name, attrs=attrs):
            val = tag.get("content") or tag.get_text(" ", strip=True)
            try:
                p = float(str(val).replace("$", "").replace(",", "").strip())
                if 20 <= p <= 2000:
                    meta_candidates.append(p)
            except Exception:
                pass
    if meta_candidates:
        return meta_candidates[0]

    # 2) JSON-LD prices
    ld = json_ld_prices(soup)
    if ld:
        return ld[0]

    # 3) site scripts with price keys
    script_text = "
".join(s.get_text(" ", strip=True) for s in soup.find_all("script"))
    for pat in [r'"price"\s*:\s*"?([0-9]{1,4}(?:\.[0-9]{2})?)', r'"salePrice"\s*:\s*"?([0-9]{1,4}(?:\.[0-9]{2})?)']:
        m = re.search(pat, script_text)
        if m:
            p = float(m.group(1))
            if 20 <= p <= 2000:
                return p

    # 4) text window near the product title
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text("
", strip=True)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    nlines = [_norm(ln) for ln in lines]
    tokens = [t for t in _norm(row.get("whisky", "")).split() if len(t) > 2 and t not in {"whisky", "scotch", "single", "malt", "blended", "year", "old", "yo"}]
    expr_tokens = [t for t in _norm(row.get("expression", "")).split() if len(t) > 2 and t not in {"whisky", "scotch", "single", "malt", "blended", "year", "old", "yo"}]
    if expr_tokens:
        tokens.extend(expr_tokens)
    seen = set(); tokens = [t for t in tokens if not (t in seen or seen.add(t))]
    candidates: list[float] = []
    for idx, ln in enumerate(nlines):
        score = sum(t in ln for t in tokens[:6])
        if score >= max(2, min(3, len(tokens[:6]))):
            window = " ".join(lines[max(0, idx - 3): min(len(lines), idx + 6)])
            vals = [v for v in _money_values(window) if 20 <= v <= 2000]
            candidates.extend(vals[:3])
    if candidates:
        return candidates[0]

    vals = [v for v in _money_values(text) if 20 <= v <= 2000]
    return vals[0] if vals else None


def resolved_product_url(row: pd.Series) -> str:
    direct = DIRECT_PRODUCT_URLS.get((str(row.get("whisky", "")), str(row.get("store", ""))))
    if direct:
        return direct
    return str(row.get("product_url") or build_search_url(str(row.get("store", "")), str(row.get("whisky", ""))))


def refresh_live_prices(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    refreshed = df.copy()
    messages: list[str] = []
    updated = 0
    for idx, row in refreshed.iterrows():
        url = resolved_product_url(row)
        try:
            html = fetch_html(url)
            price = extract_live_price(row, html)
            if price is None:
                messages.append(f"No live price found for {row['whisky']} at {row['store']}")
                continue
            refreshed.at[idx, "price_aud"] = float(price)
            refreshed.at[idx, "product_url"] = url
            refreshed.at[idx, "last_seen"] = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            refreshed.at[idx, "source"] = "live_page_refresh"
            updated += 1
        except Exception as e:
            messages.append(f"Skipped {row['whisky']} at {row['store']}: {type(e).__name__}")
    refreshed = normalize_prices(refreshed)
    messages.insert(0, f"Updated {updated} row(s) from retailer pages.")
    return refreshed, messages


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_default_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_csv(DEFAULT_CSV), load_csv(HISTORY_CSV)


@st.cache_data
def export_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="whisky_prices")
    return output.getvalue()


@st.cache_data
def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    expected = {
        "rank_au": None, "whisky": "", "expression": "", "brand": "", "style": "", "age": "", "abv": "",
        "size_ml": 700, "store": "", "state": "AU", "price_aud": 0.0, "in_stock": True, "product_url": "",
        "store_url": "", "last_seen": "", "source": "manual", "popularity_group": "",
    }
    for col, default in expected.items():
        if col not in df.columns:
            df[col] = default
    df["price_aud"] = pd.to_numeric(df["price_aud"], errors="coerce")
    df["size_ml"] = pd.to_numeric(df["size_ml"], errors="coerce")
    df["rank_au"] = pd.to_numeric(df["rank_au"], errors="coerce")
    df["in_stock"] = df["in_stock"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    df["price_per_100ml"] = (df["price_aud"] / df["size_ml"]) * 100
    df["search_text"] = df[["whisky", "expression", "brand", "store", "state", "style"]].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return df.dropna(subset=["price_aud", "size_ml"])


@st.cache_data
def prepare_history(history_df: pd.DataFrame) -> pd.DataFrame:
    if history_df.empty:
        return history_df
    for col in ["whisky", "store", "price_aud", "checked_at"]:
        if col not in history_df.columns:
            history_df[col] = None
    history_df["price_aud"] = pd.to_numeric(history_df["price_aud"], errors="coerce")
    history_df["checked_at"] = pd.to_datetime(history_df["checked_at"], errors="coerce")
    return history_df.dropna(subset=["price_aud", "checked_at"])


@st.cache_data
def leaderboard(filtered: pd.DataFrame) -> pd.DataFrame:
    out = (filtered.sort_values(["rank_au", "price_aud"], ascending=[True, True]).groupby("whisky", as_index=False).first())
    out = out[["rank_au", "whisky", "brand", "style", "store", "price_aud", "price_per_100ml", "product_url"]]
    return out.rename(columns={"store": "best_store", "price_aud": "best_price", "price_per_100ml": "best_per_100ml"}).sort_values(["rank_au", "best_price"])


@st.cache_data
def comparison_table(filtered: pd.DataFrame) -> pd.DataFrame:
    pivot = filtered.pivot_table(index=["rank_au", "whisky", "brand", "size_ml"], columns="store", values="price_aud", aggfunc="min").reset_index()
    store_cols = [c for c in pivot.columns if c not in ["rank_au", "whisky", "brand", "size_ml"]]
    if store_cols:
        pivot["cheapest_price"] = pivot[store_cols].min(axis=1)
        pivot["spread"] = pivot[store_cols].max(axis=1) - pivot[store_cols].min(axis=1)
    return pivot.sort_values(["rank_au", "cheapest_price"])


def metric_card(title: str, value: str, help_text: str = "") -> None:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>{escape(title)}</div><div class='metric-value'>{value}</div><div class='metric-help'>{escape(help_text)}</div></div>", unsafe_allow_html=True)


def render_hero(best_row: pd.Series, tracked: int, avg_spread: float) -> None:
    st.markdown(
        f"""
        <div class='hero'>
            <div class='eyebrow'>Premium whisky price tracker</div>
            <div class='hero-title'>BoozeDeals AU</div>
            <div class='hero-copy'>Compare a curated watchlist of 50 high-demand whiskies across Australia's major chains, jump straight to live product pages, and spot the best value bottle in seconds.</div>
            <div class='hero-badges'>
                <span class='badge'>Cleaner comparison cards</span>
                <span class='badge'>Live retailer refresh</span>
                <span class='badge'>Top 50 watchlist</span>
                <span class='badge'>Store price matrix</span>
            </div>
            <div class='hero-kicker'>
                <span><b>{tracked}</b> whiskies tracked</span>
                <span><b>{len(STORE_META)}</b> major retailers</span>
                <span><b>${avg_spread:,.2f}</b> average spread</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def best_deal_card(best_row: pd.Series) -> None:
    st.markdown(
        f"""
        <div class='best-deal-card'>
            <div class='best-deal-label'>Best deal today</div>
            <div class='best-deal-price'>${best_row['price_aud']:,.2f}</div>
            <div class='best-deal-name'>{escape(str(best_row['whisky']))}</div>
            <div class='best-deal-copy'>Currently cheapest at {escape(str(best_row['store']))} · ${best_row['price_per_100ml']:,.2f} per 100mL · {int(best_row['size_ml'])}mL bottle.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button("Open deal ↗", resolved_product_url(best_row), use_container_width=True)


def store_jump_row() -> None:
    st.markdown("<div class='section-title' style='margin-top:1rem'>Browse stores</div><div class='section-subtitle'>Direct shortcuts to the main whisky pages at the major Australian chains.</div>", unsafe_allow_html=True)
    cols = st.columns(len(STORE_META))
    for col, (store_name, meta) in zip(cols, STORE_META.items()):
        with col:
            color = STORE_COLORS.get(store_name, "#475569")
            st.markdown(
                f"<div class='store-jump-card'><div class='logo-dot' style='background:{color}'>{escape(meta['short'])}</div><div class='store-caption'>{escape(store_name)}</div><div class='store-sub'>Open whisky range</div></div>",
                unsafe_allow_html=True,
            )
            st.link_button(f"Open {store_name} ↗", meta["url"], use_container_width=True)


def store_offer_card(row: pd.Series, best_price: float) -> None:
    link = resolved_product_url(row)
    chip_color = STORE_COLORS.get(row["store"], "#475569")
    best_class = " best" if abs(float(row["price_aud"]) - float(best_price)) < 0.001 else ""
    stock = "In stock" if bool(row["in_stock"]) else "Availability unknown"
    st.markdown(
        f"""
        <div class='offer-card{best_class}'>
            <div class='offer-top'>
                <div class='store-name'>{escape(str(row['store']))}</div>
                <span class='store-chip' style='background:{chip_color}'>{escape(STORE_META.get(row['store'], {}).get('wordmark', row['store']))}</span>
            </div>
            <div class='price'>${row['price_aud']:,.2f}</div>
            <div class='subtle'>${row['price_per_100ml']:,.2f} per 100mL</div>
            <div class='pills'>
                <span class='pill'>{stock}</span>
                <span class='pill'>{int(row['size_ml'])}mL</span>
                <span class='pill'>Seen {escape(str(row['last_seen']))}</span>
            </div>
            <div style='margin-top:1rem;color:#e5e7eb;font-weight:700'>{escape(str(row['whisky']))}</div>
            <div class='muted'>{escape(str(row['brand']))} • {escape(str(row['style']))}</div>
            <a class='offer-link' href='{escape(link, quote=True)}' target='_blank'>Open store listing ↗</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()
    default_current, default_history = load_default_data()
    if "current_df" not in st.session_state:
        st.session_state.current_df = normalize_prices(default_current.copy())
    if "history_df" not in st.session_state:
        st.session_state.history_df = prepare_history(default_history.copy())
    current_df = st.session_state.current_df.copy()
    history_df = st.session_state.history_df.copy()
    if current_df.empty:
        st.error("No current price data found.")
        st.stop()

    baseline_board = leaderboard(current_df)
    baseline_compare = comparison_table(current_df)
    baseline_best_row = current_df.sort_values("price_aud").iloc[0]
    baseline_spread = baseline_compare["spread"].dropna().mean() if "spread" in baseline_compare else 0.0

    c_hero, c_best = st.columns([1.65, 1], gap="large")
    with c_hero:
        render_hero(baseline_best_row, baseline_board["whisky"].nunique(), baseline_spread)
    with c_best:
        best_deal_card(baseline_best_row)

    store_jump_row()

    st.markdown("<div class='panel'><div class='panel-title'>Refine the comparison</div>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns([1, 1, 1.25, 1.05, 1.15])
    styles = ["All"] + sorted(x for x in current_df["style"].dropna().astype(str).unique() if x)
    brands = ["All"] + sorted(x for x in current_df["brand"].dropna().astype(str).unique() if x)
    stores = sorted(x for x in current_df["store"].dropna().astype(str).unique() if x)
    whisky_opts = current_df[["rank_au", "whisky"]].drop_duplicates().sort_values(["rank_au", "whisky"])["whisky"].tolist()
    max_rank = int(current_df["rank_au"].max()) if current_df["rank_au"].notna().any() else 50
    with f1:
        selected_style = st.selectbox("Style", styles, index=0)
    with f2:
        selected_brand = st.selectbox("Brand", brands, index=0)
    with f3:
        selected_stores = st.multiselect("Stores", stores, default=stores)
    with f4:
        rank_limit = st.slider("Top-ranked whiskies", min_value=10, max_value=max_rank, value=max_rank, step=5)
    with f5:
        search_term = st.text_input("Search", placeholder="Macallan, Glenfiddich, Nikka...")

    f6, f7, f8, f9 = st.columns([2.3, 0.95, 1, 1.2])
    with f6:
        focus_whisky = st.selectbox("Focus whisky", whisky_opts, index=min(8, len(whisky_opts) - 1))
    with f7:
        in_stock_only = st.toggle("In stock only", value=True)
    with f8:
        sort_by = st.selectbox("Sort matrix", ["cheapest_price", "spread", "rank_au", "whisky"])
    with f9:
        refresh_scope = st.selectbox("Live refresh scope", ["Focus whisky only", "Filtered rows"], index=0)
    r1, r2 = st.columns([1.2, 4])
    with r1:
        do_refresh = st.button("Refresh live rates", use_container_width=True)
    with r2:
        st.markdown("<div class='data-note'>This uses live retailer page parsing where possible. For some bottles, direct product URLs are used to improve accuracy over search pages. Results can still vary by postcode, member pricing, stock, and temporary promos.</div></div>", unsafe_allow_html=True)

    if do_refresh:
        to_refresh = current_df.copy()
        to_refresh = to_refresh[to_refresh["rank_au"].fillna(999) <= rank_limit]
        if selected_style != "All":
            to_refresh = to_refresh[to_refresh["style"] == selected_style]
        if selected_brand != "All":
            to_refresh = to_refresh[to_refresh["brand"] == selected_brand]
        if selected_stores:
            to_refresh = to_refresh[to_refresh["store"].isin(selected_stores)]
        if search_term:
            to_refresh = to_refresh[to_refresh["search_text"].str.contains(search_term.lower(), na=False)]
        if in_stock_only:
            to_refresh = to_refresh[to_refresh["in_stock"]]
        if refresh_scope == "Focus whisky only":
            to_refresh = to_refresh[to_refresh["whisky"] == focus_whisky]
        with st.spinner(f"Refreshing {len(to_refresh)} row(s) from retailer pages..."):
            refreshed_subset, live_messages = refresh_live_prices(to_refresh)
        current_df = current_df.set_index(["whisky", "store", "size_ml"])
        refreshed_subset = refreshed_subset.set_index(["whisky", "store", "size_ml"])
        current_df.update(refreshed_subset)
        current_df = normalize_prices(current_df.reset_index())
        st.session_state.current_df = current_df.copy()
        if live_messages:
            st.toast(live_messages[0])
            with st.expander("Live refresh details"):
                for msg in live_messages[:50]:
                    st.write("- ", msg)

    filtered = current_df.copy()
    filtered = filtered[filtered["rank_au"].fillna(999) <= rank_limit]
    if selected_style != "All":
        filtered = filtered[filtered["style"] == selected_style]
    if selected_brand != "All":
        filtered = filtered[filtered["brand"] == selected_brand]
    if selected_stores:
        filtered = filtered[filtered["store"].isin(selected_stores)]
    if in_stock_only:
        filtered = filtered[filtered["in_stock"]]
    if search_term:
        filtered = filtered[filtered["search_text"].str.contains(search_term.lower(), na=False)]
    if filtered.empty:
        st.warning("No rows matched the current filters.")
        st.stop()

    board = leaderboard(filtered)
    compare = comparison_table(filtered)
    if focus_whisky not in filtered["whisky"].unique():
        focus_whisky = board["whisky"].iloc[0]
    focus_rows = filtered[filtered["whisky"] == focus_whisky].sort_values("price_aud")
    cheapest_row = filtered.sort_values("price_aud").iloc[0]
    avg_price = filtered["price_aud"].mean()
    avg_spread = compare["spread"].dropna().mean() if "spread" in compare else 0.0
    tracked = board["whisky"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Tracked whiskies", f"{tracked}", f"Across {filtered['store'].nunique()} stores")
    with c2:
        metric_card("Cheapest live bottle", f"${cheapest_row['price_aud']:,.2f}", f"{cheapest_row['whisky']} at {cheapest_row['store']}")
    with c3:
        metric_card("Average shelf price", f"${avg_price:,.2f}", "Based on current filtered results")
    with c4:
        metric_card("Average store spread", f"${avg_spread:,.2f}", "Gap between lowest and highest current store price")

    st.markdown("<div class='section-title' style='margin-top:1rem'>Store comparison for your focus bottle</div><div class='section-subtitle'>Direct links, live price cards, and the cheapest store highlighted.</div>", unsafe_allow_html=True)
    offer_cols = st.columns(min(4, max(1, len(focus_rows))))
    best_focus_price = float(focus_rows["price_aud"].min())
    for col, (_, row) in zip(offer_cols, focus_rows.iterrows()):
        with col:
            store_offer_card(row, best_focus_price)

    tab1, tab2, tab3 = st.tabs(["Overview", "Comparison matrix", "Price history"])
    with tab1:
        left, right = st.columns([1.15, 0.85])
        with left:
            st.markdown("<div class='section-title'>Top 50 leaderboard</div><div class='section-subtitle'>Best current store price for each whisky in the watchlist.</div>", unsafe_allow_html=True)
            show_board = board.copy()
            st.dataframe(
                show_board,
                use_container_width=True,
                hide_index=True,
                column_order=["rank_au", "whisky", "brand", "style", "best_store", "best_price", "best_per_100ml", "product_url"],
                column_config={
                    "rank_au": st.column_config.NumberColumn("AU rank", format="%d"),
                    "best_store": "Cheapest store",
                    "best_price": st.column_config.NumberColumn("Best price", format="$%.2f"),
                    "best_per_100ml": st.column_config.NumberColumn("Best / 100mL", format="$%.2f"),
                    "product_url": st.column_config.LinkColumn("Store link", display_text="Open"),
                },
            )
        with right:
            st.markdown("<div class='section-title'>Best-price chart</div><div class='section-subtitle'>Top 20 whiskies by rank with the lowest current shelf price shown.</div>", unsafe_allow_html=True)
            chart_df = board.head(20).copy()
            chart = alt.Chart(chart_df).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
                x=alt.X("best_price:Q", title="Best price (AUD)"),
                y=alt.Y("whisky:N", sort=alt.SortField(field="rank_au", order="ascending"), title=None),
                color=alt.Color("best_store:N", scale=alt.Scale(domain=list(STORE_COLORS), range=list(STORE_COLORS.values())), legend=alt.Legend(title="Best store")),
                tooltip=["rank_au", "whisky", "best_store", alt.Tooltip("best_price:Q", format=".2f")],
            ).properties(height=560)
            st.altair_chart(chart, use_container_width=True)

    with tab2:
        st.markdown("<div class='section-title'>Store-by-store comparison matrix</div><div class='section-subtitle'>See where the same bottle is cheapest and how wide the current spread is across stores.</div>", unsafe_allow_html=True)
        compare_show = compare.copy().sort_values(sort_by)
        st.dataframe(
            compare_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "rank_au": st.column_config.NumberColumn("AU rank", format="%d"),
                "size_ml": st.column_config.NumberColumn("mL", format="%d"),
                "Dan Murphy's": st.column_config.NumberColumn("Dan Murphy's", format="$%.2f"),
                "BWS": st.column_config.NumberColumn("BWS", format="$%.2f"),
                "Liquorland": st.column_config.NumberColumn("Liquorland", format="$%.2f"),
                "First Choice": st.column_config.NumberColumn("First Choice", format="$%.2f"),
                "cheapest_price": st.column_config.NumberColumn("Cheapest price", format="$%.2f"),
                "spread": st.column_config.NumberColumn("Spread", format="$%.2f"),
            },
        )
        export_df = filtered[["rank_au", "whisky", "expression", "brand", "style", "store", "size_ml", "price_aud", "price_per_100ml", "in_stock", "product_url", "store_url", "last_seen"]].sort_values(["rank_au", "price_aud"])
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("Download filtered rows as CSV", data=export_df.to_csv(index=False).encode("utf-8"), file_name="boozedeals_filtered.csv", mime="text/csv", use_container_width=True)
        with d2:
            st.download_button("Download filtered rows as Excel", data=export_excel(export_df), file_name="boozedeals_filtered.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    with tab3:
        st.markdown("<div class='section-title'>Price history</div><div class='section-subtitle'>Historical trend for the filtered whiskies and selected stores.</div>", unsafe_allow_html=True)
        history_join = history_df.copy()
        if not history_join.empty:
            history_join = history_join[history_join["whisky"].isin(filtered["whisky"].unique())]
            history_join = history_join[history_join["store"].isin(filtered["store"].unique())]
            line = alt.Chart(history_join).mark_line(point=True).encode(
                x=alt.X("checked_at:T", title="Checked at"),
                y=alt.Y("price_aud:Q", title="Price (AUD)"),
                color=alt.Color("store:N", scale=alt.Scale(domain=list(STORE_COLORS), range=list(STORE_COLORS.values()))),
                tooltip=["whisky", "store", alt.Tooltip("price_aud:Q", format=".2f"), "checked_at:T"],
            ).properties(height=430)
            st.altair_chart(line, use_container_width=True)
            st.caption("History uses the bundled sample dataset until you replace it with scheduled snapshots.")
        else:
            st.info("No history CSV loaded.")

    with st.expander("About live-rate accuracy"):
        st.markdown("""
        Live refresh is best-effort. Where a direct product URL is known, the app uses that page first because it is usually more accurate than retailer search pages.

        I also corrected the bundled starter data issue you spotted: Glenfiddich 12YO at BWS is set to **A$106** and this build includes a direct BWS product URL override for that bottle.
        """)


if __name__ == "__main__":
    main()
