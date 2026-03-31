from __future__ import annotations

from pathlib import Path
import io
import pandas as pd
import streamlit as st
import altair as alt

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets" / "stores"
DEFAULT_CSV = DATA_DIR / "sample_whisky_prices.csv"
HISTORY_CSV = DATA_DIR / "sample_price_history.csv"

st.set_page_config(
    page_title="BoozeDeals AU",
    page_icon="🥃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STORE_COLORS = {
    "Dan Murphy's": "#00A651",
    "BWS": "#F97316",
    "Liquorland": "#2563EB",
    "First Choice": "#7C3AED",
    "Harry Brown": "#C9A84C",
}


def local_logo_html(filename: str) -> str:
    path = ASSETS_DIR / filename
    if not path.exists():
        return ""
    svg = path.read_text(encoding="utf-8")
    return svg.replace("<svg", "<svg class='store-logo-svg'", 1)


STORE_META = {
    "Dan Murphy's": {
        "url": "https://www.danmurphys.com.au/whisky/all",
        "logo_html": local_logo_html("dan_murphys.svg"),
    },
    "BWS": {
        "url": "https://bws.com.au/spirits/whisky",
        "logo_html": local_logo_html("bws.svg"),
    },
    "Liquorland": {
        "url": "https://www.liquorland.com.au/spirits/whisky",
        "logo_html": local_logo_html("liquorland.svg"),
    },
    "First Choice": {
        "url": "https://www.firstchoiceliquor.com.au/spirits/whisky",
        "logo_html": local_logo_html("first_choice.svg"),
    },
    "Harry Brown": {
        "url": "https://harrybrown.com.au/category/spirits-and-liqueur",
        "logo_html": local_logo_html("harry_brown.svg"),
    },
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=DM+Sans:wght@300;400;500;600;700&display=swap');

[data-testid="stSidebar"], [data-testid="collapsedControl"], footer, #MainMenu, header {display:none !important;}

* { font-family: 'DM Sans', sans-serif; }

.stApp {
    background: #05080f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(14,165,92,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(124,58,237,0.07) 0%, transparent 60%);
}

.block-container { max-width: 1440px; padding: 0.5rem 1.5rem 3rem 1.5rem; }

.site-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.1rem 0 .9rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1.4rem;
}
.site-logo { display: flex; align-items: center; gap: .75rem; }
.site-logo-icon { font-size: 1.7rem; line-height: 1; }
.site-logo-text { font-family: 'Playfair Display', serif; font-size: 1.55rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em; }
.site-logo-text span { color: #C9A84C; }
.header-meta { display: flex; gap: 1.5rem; font-size: .83rem; color: #64748b; }
.header-meta b { color: #94a3b8; }

.stats-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; margin-bottom: 1.2rem; }
.stat-card { background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: 1.05rem 1.15rem; position: relative; overflow: hidden; }
.stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 16px 16px 0 0; }
.stat-card.green::before { background: linear-gradient(90deg, #00A651, transparent); }
.stat-card.amber::before { background: linear-gradient(90deg, #C9A84C, transparent); }
.stat-card.blue::before { background: linear-gradient(90deg, #3B82F6, transparent); }
.stat-card.purple::before { background: linear-gradient(90deg, #8B5CF6, transparent); }
.stat-label { font-size: .76rem; color: #64748b; text-transform: uppercase; letter-spacing: .1em; font-weight: 600; margin-bottom: .4rem; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.85rem; font-weight: 700; color: #f1f5f9; line-height: 1; }
.stat-sub { font-size: .76rem; color: #475569; margin-top: .3rem; }

.best-deal-banner {
    background: linear-gradient(135deg, rgba(14,165,92,0.12) 0%, rgba(201,168,76,0.08) 50%, rgba(5,8,15,0.8) 100%);
    border: 1px solid rgba(14,165,92,0.25); border-radius: 20px; padding: 1.2rem 1.5rem;
    margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
}
.bd-tag { background: rgba(14,165,92,0.15); border: 1px solid rgba(14,165,92,0.3); color: #4ade80; font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .14em; padding: .3rem .65rem; border-radius: 999px; white-space: nowrap; }
.bd-name { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin-top: .45rem; }
.bd-sub { font-size: .83rem; color: #94a3b8; margin-top: .15rem; }
.bd-price { font-family: 'Playfair Display', serif; font-size: 2.2rem; font-weight: 900; color: #4ade80; letter-spacing: -.03em; white-space: nowrap; }
.bd-per { font-size: .75rem; color: #64748b; margin-top: .15rem; text-align: right; }
.bd-cta { display: inline-flex; align-items: center; gap: .45rem; background: rgba(14,165,92,0.18); border: 1px solid rgba(14,165,92,0.35); color: #4ade80; font-weight: 700; font-size: .85rem; padding: .6rem 1.1rem; border-radius: 10px; text-decoration: none; white-space: nowrap; }
.bd-cta:hover { background: rgba(14,165,92,0.28); }

.stores-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: .6rem; margin-bottom: 1.4rem; }
.store-pill { display: flex; align-items: center; justify-content: center; gap: .6rem; padding: .7rem .8rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; text-decoration: none; transition: all .2s; min-height: 62px; }
.store-pill:hover { background: rgba(255,255,255,0.065); border-color: rgba(255,255,255,0.13); transform: translateY(-1px); }
.store-pill-name { font-size: .8rem; font-weight: 700; }
.store-logo-wrap { height: 28px; display:flex; align-items:center; }
.store-logo-svg { max-height: 24px; width: auto; max-width: 100px; }

.filter-panel { background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.07); border-radius: 18px; padding: .9rem 1.1rem 1rem 1.1rem; margin-bottom: 1.25rem; }
.filter-title { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .12em; color: #475569; margin-bottom: .75rem; }

.metric-card { background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: .95rem 1.05rem .9rem 1.05rem; min-height: 108px; }
.metric-label { font-size: .76rem; color: #64748b; text-transform: uppercase; letter-spacing: .1em; font-weight: 600; }
.metric-value { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #f1f5f9; font-weight: 700; margin-top: .25rem; line-height: 1; }
.metric-help { font-size: .76rem; color: #475569; margin-top: .3rem; }

.offer-card { background: rgba(10,14,26,0.85); border: 1px solid rgba(255,255,255,0.07); border-radius: 20px; padding: 1.1rem; min-height: 240px; display: flex; flex-direction: column; }
.offer-card.best { border-color: rgba(74,222,128,0.35); background: linear-gradient(180deg, rgba(14,165,92,0.07), rgba(10,14,26,0.9)); }
.offer-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: .7rem; }
.store-chip { font-size: .7rem; font-weight: 800; border-radius: 999px; padding: .22rem .52rem; }
.best-badge { font-size: .68rem; font-weight: 800; color: #4ade80; background: rgba(74,222,128,0.12); border: 1px solid rgba(74,222,128,0.25); border-radius: 999px; padding: .18rem .5rem; }
.offer-price { font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 800; color: #f1f5f9; line-height: 1; margin-bottom: .2rem; }
.offer-per { font-size: .78rem; color: #64748b; margin-bottom: .75rem; }
.offer-name { font-size: .9rem; font-weight: 700; color: #e2e8f0; margin-bottom: .15rem; }
.offer-brand { font-size: .78rem; color: #64748b; }
.offer-pills { display: flex; gap: .35rem; flex-wrap: wrap; margin-top: auto; padding-top: .8rem; }
.pill { display: inline-block; padding: .18rem .5rem; border-radius: 999px; font-size: .7rem; font-weight: 700; background: rgba(255,255,255,0.06); color: #94a3b8; border: 1px solid rgba(255,255,255,0.07); }
.pill.green { background: rgba(74,222,128,0.1); color: #4ade80; border-color: rgba(74,222,128,0.2); }
.pill.red { background: rgba(239,68,68,0.1); color: #f87171; border-color: rgba(239,68,68,0.2); }
.offer-link { font-size: .78rem; color: #60a5fa; text-decoration: none; font-weight: 700; margin-top: .6rem; display: inline-block; }
.offer-link:hover { text-decoration: underline; }

.section-head { margin: .2rem 0 .9rem 0; }
.section-title { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: #f1f5f9; line-height: 1.2; }
.section-sub { font-size: .8rem; color: #475569; margin-top: .2rem; }

div[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 14px !important; overflow: hidden !important; }
div[data-testid="stDownloadButton"] button, div.stButton > button { border-radius: 10px !important; font-weight: 700 !important; }

.stSelectbox label, .stMultiSelect label, .stSlider label, .stTextInput label, .stToggle label {
    color: #64748b !important; font-size: .78rem !important; font-weight: 600 !important;
    text-transform: uppercase !important; letter-spacing: .08em !important;
}

.gap { height: .75rem; }
@media (max-width: 900px) {
    .stats-bar { grid-template-columns: repeat(2, 1fr); }
    .stores-row { grid-template-columns: repeat(3, 1fr); }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


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
def leaderboard(filtered: pd.DataFrame) -> pd.DataFrame:
    return (
        filtered.sort_values(["rank_au", "price_aud"], ascending=[True, True])
        .groupby("whisky", as_index=False)
        .first()[["rank_au", "whisky", "brand", "style", "store", "price_aud", "price_per_100ml", "product_url"]]
        .rename(columns={"store": "best_store", "price_aud": "best_price", "price_per_100ml": "best_per_100ml"})
        .sort_values(["rank_au", "best_price"])
    )


@st.cache_data
def comparison_table(filtered: pd.DataFrame) -> pd.DataFrame:
    pivot = filtered.pivot_table(
        index=["rank_au", "whisky", "brand", "size_ml"],
        columns="store", values="price_aud", aggfunc="min"
    ).reset_index()
    store_cols = [c for c in pivot.columns if c not in ["rank_au", "whisky", "brand", "size_ml"]]
    if store_cols:
        pivot["cheapest_price"] = pivot[store_cols].min(axis=1)
        pivot["spread"] = pivot[store_cols].max(axis=1) - pivot[store_cols].min(axis=1)
    return pivot.sort_values(["rank_au", "cheapest_price"])


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
def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    expected = {
        "rank_au": None, "whisky": "", "expression": "", "brand": "", "style": "",
        "age": "", "abv": "", "size_ml": 700, "store": "", "state": "AU",
        "price_aud": 0.0, "in_stock": True, "product_url": "", "store_url": "",
        "store_logo": "", "last_seen": "", "source": "manual", "popularity_group": "",
    }
    for col, default in expected.items():
        if col not in df.columns:
            df[col] = default
    df["price_aud"] = pd.to_numeric(df["price_aud"], errors="coerce")
    df["size_ml"] = pd.to_numeric(df["size_ml"], errors="coerce")
    df["rank_au"] = pd.to_numeric(df["rank_au"], errors="coerce")
    df["in_stock"] = df["in_stock"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    df["price_per_100ml"] = (df["price_aud"] / df["size_ml"]) * 100
    df["search_text"] = (
        df[["whisky", "expression", "brand", "store", "state", "style"]]
        .fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    )
    return df.dropna(subset=["price_aud", "size_ml"])


def render_logo(store_name: str) -> str:
    html = STORE_META.get(store_name, {}).get("logo_html", "")
    if html:
        return f"<div class='store-logo-wrap'>{html}</div>"
    return f"<div style='font-weight:800;color:#f8fafc;font-size:.8rem'>{store_name}</div>"


def stores_row() -> None:
    cards = []
    for store_name, meta in STORE_META.items():
        color = STORE_COLORS.get(store_name, "#475569")
        cards.append(
            f"<a class='store-pill' href='{meta['url']}' target='_blank'>"
            f"{render_logo(store_name)}"
            f"<span class='store-pill-name' style='color:{color}'>{store_name}</span>"
            f"</a>"
        )
    st.markdown(f"<div class='stores-row'>{''.join(cards)}</div>", unsafe_allow_html=True)


def site_header(tracked: int, stores_count: int, avg_spread: float) -> None:
    st.markdown(
        f"<div class='site-header'>"
        f"<div class='site-logo'>"
        f"<span class='site-logo-icon'>🥃</span>"
        f"<span class='site-logo-text'>Booze<span>Deals</span> AU</span>"
        f"</div>"
        f"<div class='header-meta'>"
        f"<span><b>{tracked}</b> whiskies tracked</span>"
        f"<span><b>{stores_count}</b> retailers</span>"
        f"<span>Avg spread <b>${avg_spread:,.2f}</b></span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def best_deal_banner(best_row: pd.Series) -> None:
    link = best_row.get("product_url") or STORE_META.get(best_row["store"], {}).get("url") or "#"
    st.markdown(
        f"<div class='best-deal-banner'>"
        f"<div>"
        f"<span class='bd-tag'>🔥 Best deal today</span>"
        f"<div class='bd-name'>{best_row['whisky']}</div>"
        f"<div class='bd-sub'>{best_row['store']} · {int(best_row['size_ml'])}mL</div>"
        f"</div>"
        f"<div style='text-align:right'>"
        f"<div class='bd-price'>${best_row['price_aud']:,.2f}</div>"
        f"<div class='bd-per'>${best_row['price_per_100ml']:,.2f} / 100mL</div>"
        f"</div>"
        f"<a class='bd-cta' href='{link}' target='_blank'>Go to deal ↗</a>"
        f"</div>",
        unsafe_allow_html=True,
    )


def stats_bar(tracked: int, cheapest: pd.Series, avg_price: float, avg_spread: float, stores_count: int) -> None:
    name = cheapest['whisky']
    name_short = name[:26] + "…" if len(name) > 26 else name
    st.markdown(
        f"<div class='stats-bar'>"
        f"<div class='stat-card green'><div class='stat-label'>Lowest price</div><div class='stat-value'>${cheapest['price_aud']:,.2f}</div><div class='stat-sub'>{name_short}</div></div>"
        f"<div class='stat-card amber'><div class='stat-label'>Avg shelf price</div><div class='stat-value'>${avg_price:,.0f}</div><div class='stat-sub'>Across filtered results</div></div>"
        f"<div class='stat-card blue'><div class='stat-label'>Whiskies tracked</div><div class='stat-value'>{tracked}</div><div class='stat-sub'>Across {stores_count} retailers</div></div>"
        f"<div class='stat-card purple'><div class='stat-label'>Avg store spread</div><div class='stat-value'>${avg_spread:,.2f}</div><div class='stat-sub'>High vs low gap</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def store_offer_card(row: pd.Series, best_price: float) -> None:
    link = row.get("product_url") or STORE_META.get(row["store"], {}).get("url") or "#"
    chip_color = STORE_COLORS.get(row["store"], "#475569")
    is_best = float(row["price_aud"]) == float(best_price)
    best_class = " best" if is_best else ""
    in_stock = bool(row["in_stock"])
    stock_class = "green" if in_stock else "red"
    stock_label = "In stock" if in_stock else "Unavailable"
    best_badge = "<span class='best-badge'>★ Best price</span>" if is_best else ""
    st.markdown(
        f"<div class='offer-card{best_class}'>"
        f"<div class='offer-top'>"
        f"{render_logo(row['store'])}"
        f"<div style='display:flex;align-items:center;gap:.4rem'>{best_badge}"
        f"<span class='store-chip' style='background:{chip_color}22;color:{chip_color};border:1px solid {chip_color}44'>{row['store']}</span>"
        f"</div></div>"
        f"<div class='offer-price'>${row['price_aud']:,.2f}</div>"
        f"<div class='offer-per'>${row['price_per_100ml']:,.2f} per 100mL</div>"
        f"<div class='offer-name'>{row['whisky']}</div>"
        f"<div class='offer-brand'>{row['brand']} · {row['style']} · {int(row['size_ml'])}mL</div>"
        f"<div class='offer-pills'><span class='pill {stock_class}'>{stock_label}</span><span class='pill'>Seen {row['last_seen']}</span></div>"
        f"<a class='offer-link' href='{link}' target='_blank'>View listing ↗</a>"
        f"</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()
    default_current, default_history = load_default_data()
    current_df = normalize_prices(default_current.copy())
    history_df = prepare_history(default_history.copy())

    if current_df.empty:
        st.error("No current price data found.")
        st.stop()

    baseline_board = leaderboard(current_df)
    baseline_compare = comparison_table(current_df)
    baseline_best_row = current_df.sort_values("price_aud").iloc[0]
    baseline_spread = baseline_compare["spread"].dropna().mean() if "spread" in baseline_compare else 0.0

    site_header(baseline_board["whisky"].nunique(), current_df["store"].nunique(), baseline_spread)
    best_deal_banner(baseline_best_row)
    stores_row()

    # ── FILTERS ──
    st.markdown("<div class='filter-panel'><div class='filter-title'>Refine the comparison</div>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns([1, 1, 1.4, 1.1, 1.1])
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
        rank_limit = st.slider("Top N whiskies", min_value=10, max_value=max_rank, value=max_rank, step=5)
    with f5:
        search_term = st.text_input("Search", placeholder="Macallan, Nikka, Lark…")

    f6, f7, f8 = st.columns([2.5, 1, 1])
    with f6:
        focus_whisky = st.selectbox("Focus bottle (store comparison)", whisky_opts, index=min(6, len(whisky_opts) - 1))
    with f7:
        in_stock_only = st.toggle("In stock only", value=True)
    with f8:
        sort_by = st.selectbox("Sort matrix by", ["cheapest_price", "spread", "rank_au", "whisky"])
    st.markdown("</div>", unsafe_allow_html=True)

    # ── FILTER DATA ──
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

    stats_bar(tracked, cheapest_row, avg_price, avg_spread, filtered["store"].nunique())

    # ── FOCUS BOTTLE CARDS ──
    st.markdown(
        f"<div class='section-head'>"
        f"<div class='section-title'>Store comparison — {focus_whisky}</div>"
        f"<div class='section-sub'>All current store listings · best price highlighted · select a different bottle above</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    offer_cols = st.columns(min(5, max(1, len(focus_rows))))
    best_focus_price = float(focus_rows["price_aud"].min())
    for col, (_, row) in zip(offer_cols, focus_rows.iterrows()):
        with col:
            store_offer_card(row, best_focus_price)

    st.markdown("<div class='gap'></div>", unsafe_allow_html=True)

    # ── TABS ──
    overview_tab, compare_tab, history_tab = st.tabs(["📋 Leaderboard & Chart", "📊 Price Matrix", "📈 Price History"])

    with overview_tab:
        left, right = st.columns([1.05, 0.95])
        with left:
            st.markdown(
                "<div class='section-head'><div class='section-title'>Leaderboard</div>"
                "<div class='section-sub'>Best current store price for each whisky in the watchlist.</div></div>",
                unsafe_allow_html=True,
            )
            show_board = board.copy()
            show_board["best_price"] = show_board["best_price"].map(lambda x: f"${x:,.2f}")
            show_board["best_per_100ml"] = show_board["best_per_100ml"].map(lambda x: f"${x:,.2f}")
            st.dataframe(
                show_board,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "product_url": st.column_config.LinkColumn("Store link", display_text="Open ↗"),
                    "rank_au": st.column_config.NumberColumn("Rank", format="%d"),
                    "best_store": "Best store",
                    "best_price": "Best price",
                    "best_per_100ml": "/ 100mL",
                },
            )
        with right:
            st.markdown(
                "<div class='section-head'><div class='section-title'>Price chart</div>"
                "<div class='section-sub'>Top 20 by rank — lowest current price.</div></div>",
                unsafe_allow_html=True,
            )
            chart_df = board.head(20).copy()
            chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                .encode(
                    x=alt.X("best_price:Q", title="Best price (AUD)"),
                    y=alt.Y("whisky:N", sort="-x", title=None),
                    color=alt.Color(
                        "best_store:N",
                        scale=alt.Scale(domain=list(STORE_COLORS.keys()), range=list(STORE_COLORS.values())),
                        legend=alt.Legend(title="Cheapest store"),
                    ),
                    tooltip=["rank_au", "whisky", "best_store", alt.Tooltip("best_price:Q", format=".2f")],
                )
                .properties(height=540)
                .configure_view(strokeWidth=0, fill="#05080f")
                .configure_axis(labelColor="#64748b", titleColor="#475569", gridColor="rgba(255,255,255,0.05)")
                .configure_legend(labelColor="#94a3b8", titleColor="#64748b")
            )
            st.altair_chart(chart, use_container_width=True)

    with compare_tab:
        st.markdown(
            "<div class='section-head'><div class='section-title'>Store-by-store price matrix</div>"
            "<div class='section-sub'>Same bottle across every retailer — spot the best deal and widest spread.</div></div>",
            unsafe_allow_html=True,
        )
        compare_show = compare.copy().sort_values(sort_by)
        numeric_cols = [c for c in compare_show.columns if c in STORE_META or c in ["cheapest_price", "spread"]]
        for col in numeric_cols:
            compare_show[col] = compare_show[col].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
        st.dataframe(compare_show, use_container_width=True, hide_index=True)

        export_df = filtered[[
            "rank_au", "whisky", "expression", "brand", "style", "store",
            "size_ml", "price_aud", "price_per_100ml", "in_stock",
            "product_url", "store_url", "last_seen"
        ]].sort_values(["rank_au", "price_aud"])
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "⬇ Download as CSV",
                data=export_df.to_csv(index=False).encode("utf-8"),
                file_name="boozedeals_filtered.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "⬇ Download as Excel",
                data=export_excel(export_df),
                file_name="boozedeals_filtered.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with history_tab:
        st.markdown(
            "<div class='section-head'><div class='section-title'>Price history</div>"
            "<div class='section-sub'>Historical trend across filtered whiskies and selected stores.</div></div>",
            unsafe_allow_html=True,
        )
        history_join = history_df.copy()
        if not history_join.empty:
            history_join = history_join[history_join["whisky"].isin(filtered["whisky"].unique())]
            history_join = history_join[history_join["store"].isin(filtered["store"].unique())]
            line = (
                alt.Chart(history_join)
                .mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X("checked_at:T", title="Date"),
                    y=alt.Y("price_aud:Q", title="Price (AUD)"),
                    color=alt.Color(
                        "store:N",
                        scale=alt.Scale(domain=list(STORE_COLORS.keys()), range=list(STORE_COLORS.values())),
                    ),
                    tooltip=["whisky", "store", alt.Tooltip("price_aud:Q", format=".2f"), "checked_at:T"],
                )
                .properties(height=420)
                .configure_view(strokeWidth=0, fill="#05080f")
                .configure_axis(labelColor="#64748b", titleColor="#475569", gridColor="rgba(255,255,255,0.05)")
            )
            st.altair_chart(line, use_container_width=True)
        else:
            st.info("No history data available. Connect a scraper to populate this view.")

    with st.expander("ℹ About BoozeDeals AU"):
        st.markdown("""
**BoozeDeals AU** tracks a curated list of 50 high-demand whiskies across Australia's major chain retailers:
Dan Murphy's, BWS, Liquorland, First Choice, and **Harry Brown**.

**Harry Brown** is a large-format independent liquor retailer (part of the LMG network) with stores in QLD, VIC, and WA.
They typically offer competitive pricing and a broad range comparable to Dan Murphy's.

Prices are indicative and based on regular monitoring. Always verify at the retailer before purchasing.
        """)


if __name__ == "__main__":
    main()
