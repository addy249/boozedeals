from __future__ import annotations

from pathlib import Path
import io
import pandas as pd
import streamlit as st
import altair as alt

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DEFAULT_CSV = DATA_DIR / "sample_whisky_prices.csv"
HISTORY_CSV = DATA_DIR / "sample_price_history.csv"

st.set_page_config(
    page_title="BoozeDeals AU",
    page_icon="🥃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STORE_COLORS = {
    "Dan Murphy's": "#14B8A6",
    "BWS": "#F97316",
    "Liquorland": "#3B82F6",
    "First Choice": "#8B5CF6",
}

STORE_META = {
    "Dan Murphy's": {
        "url": "https://www.danmurphys.com.au/whisky/all",
        "wordmark": "Dan Murphy's",
    },
    "BWS": {
        "url": "https://bws.com.au/spirits/whisky",
        "wordmark": "BWS",
    },
    "Liquorland": {
        "url": "https://www.liquorland.com.au/spirits/whisky",
        "wordmark": "Liquorland",
    },
    "First Choice": {
        "url": "https://www.firstchoiceliquor.com.au/spirits/whisky",
        "wordmark": "First Choice",
    },
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"], footer, #MainMenu, header {display:none !important;}
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(249,115,22,0.12), transparent 20%),
                radial-gradient(circle at top right, rgba(59,130,246,0.10), transparent 22%),
                linear-gradient(180deg, #060b16 0%, #091120 55%, #09101a 100%);
        }
        .block-container {max-width: 1420px; padding-top: 1rem; padding-bottom: 2.5rem;}
        h1,h2,h3 {letter-spacing: -0.03em;}
        .hero {
            background:
                radial-gradient(circle at 85% 15%, rgba(249,115,22,0.26), transparent 22%),
                linear-gradient(135deg, rgba(15,23,42,0.96) 0%, rgba(15,23,42,0.98) 48%, rgba(66,32,14,0.96) 100%);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 30px 90px rgba(0,0,0,.36);
            border-radius: 30px;
            padding: 2.1rem 2.1rem 1.9rem 2.1rem;
            color: white;
            overflow: hidden;
        }
        .eyebrow {font-size: .8rem; letter-spacing: .18em; text-transform: uppercase; color: #f59e0b; font-weight: 800; margin-bottom: .8rem;}
        .hero h1 {margin: 0; font-size: 3.1rem; line-height: 1.02;}
        .hero-copy {margin: .9rem 0 0 0; color: #d1d5db; font-size: 1.03rem; max-width: 820px;}
        .hero-badges {margin-top: 1rem; display:flex; gap:.6rem; flex-wrap:wrap;}
        .badge {padding:.38rem .72rem; border-radius:999px; font-size:.82rem; font-weight:700; background:rgba(255,255,255,.08); color:#f8fafc; border:1px solid rgba(255,255,255,.08);}
        .hero-kicker {margin-top: 1.25rem; display:flex; gap:1rem; flex-wrap:wrap; color:#cbd5e1; font-size:.92rem;}
        .hero-kicker b {color:white;}
        .panel {
            margin-top: 1rem;
            background: rgba(10,17,30,.78);
            border: 1px solid rgba(255,255,255,.08);
            backdrop-filter: blur(16px);
            box-shadow: 0 18px 40px rgba(0,0,0,.18);
            border-radius: 24px;
            padding: 1rem 1rem 1.1rem 1rem;
        }
        .panel-title {font-size: 1rem; font-weight: 800; color: #f8fafc; margin-bottom: .9rem;}
        .metric-card {
            background: linear-gradient(180deg, rgba(255,255,255,.065), rgba(255,255,255,.03));
            border: 1px solid rgba(255,255,255,.09);
            border-radius: 22px;
            padding: 1rem 1rem .9rem 1rem;
            min-height: 122px;
        }
        .metric-label {font-size:.88rem; color:#94a3b8;}
        .metric-value {font-size:2rem; color:#f8fafc; font-weight:800; margin-top:.25rem; line-height:1.05;}
        .metric-help {font-size:.9rem; color:#cbd5e1; margin-top:.35rem;}
        .best-deal-card {
            background: linear-gradient(135deg, rgba(249,115,22,.15), rgba(15,23,42,.75));
            border: 1px solid rgba(249,115,22,.35);
            border-radius: 22px;
            padding: 1.1rem 1.15rem;
            min-height: 162px;
        }
        .best-deal-label {font-size:.8rem; letter-spacing:.14em; text-transform:uppercase; color:#fbbf24; font-weight:800;}
        .best-deal-price {font-size:2.2rem; font-weight:900; color:#fff; line-height:1; margin:.5rem 0 .35rem 0;}
        .best-deal-name {font-size:1.03rem; font-weight:800; color:#fff;}
        .best-deal-copy {font-size:.94rem; color:#d1d5db; margin-top:.35rem;}
        .store-pill {
            display:inline-flex; align-items:center; justify-content:center; width:100%;
            padding:.68rem .95rem; border-radius:16px; font-weight:800; color:white;
            text-decoration:none; border:1px solid rgba(255,255,255,.08); box-shadow:0 10px 30px rgba(0,0,0,.14);
        }
        .store-pill:hover {filter: brightness(1.05);}
        .section-title {font-size:1.22rem; font-weight:800; margin: .2rem 0 .3rem 0; color:#f8fafc;}
        .section-subtitle {font-size:.92rem; color:#94a3b8; margin: 0 0 .95rem 0;}
        .offer-card {
            background: linear-gradient(180deg, rgba(15,23,42,.85), rgba(17,24,39,.96));
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 24px;
            padding: 1.05rem;
            min-height: 272px;
            box-shadow: 0 18px 44px rgba(0,0,0,.22);
        }
        .offer-card.best {border-color: rgba(249,115,22,.52); box-shadow: 0 18px 50px rgba(249,115,22,.14);}
        .offer-top {display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.8rem;}
        .store-name {font-size:1.05rem; font-weight:800; color:#fff;}
        .store-chip {font-size:.78rem; font-weight:800; border-radius:999px; padding:.28rem .58rem; color:white;}
        .price {font-size:2rem; font-weight:800; color:#ffffff; letter-spacing:-0.03em;}
        .subtle {color:#cbd5e1; font-size:.94rem;}
        .muted {color:#94a3b8; font-size:.85rem;}
        .pills {display:flex; gap:.45rem; flex-wrap:wrap; margin-top:.9rem;}
        .pill {display:inline-block; padding:.22rem .56rem; border-radius:999px; font-size:.78rem; font-weight:700; background:rgba(255,255,255,.08); color:#e5e7eb; border:1px solid rgba(255,255,255,.08);}
        .offer-link {display:inline-block; margin-top:1rem; color:#93c5fd; text-decoration:none; font-weight:700;}
        .offer-link:hover {text-decoration:underline;}
        .spacer {height: .55rem;}
        .data-note {font-size:.86rem; color:#94a3b8; margin-top:.55rem;}
        .compact-note {font-size:.83rem; color:#94a3b8; margin-top:.2rem;}
        div[data-testid="stDataFrame"] {border: 1px solid rgba(255,255,255,.08); border-radius: 18px; overflow: hidden;}
        div[data-testid="stLinkButton"] a, div.stButton > button, div[data-testid="stDownloadButton"] button {
            border-radius: 14px !important; font-weight: 700 !important;
        }
        .stTabs [data-baseweb="tab-list"] {gap: 0.5rem;}
        .stTabs [data-baseweb="tab"] {background: rgba(255,255,255,.03); border-radius: 999px; padding-inline: .9rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    pivot = (
        filtered.pivot_table(index=["rank_au", "whisky", "brand", "size_ml"], columns="store", values="price_aud", aggfunc="min")
        .reset_index()
    )
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
        "rank_au": None,
        "whisky": "",
        "expression": "",
        "brand": "",
        "style": "",
        "age": "",
        "abv": "",
        "size_ml": 700,
        "store": "",
        "state": "AU",
        "price_aud": 0.0,
        "in_stock": True,
        "product_url": "",
        "store_url": "",
        "last_seen": "",
        "source": "manual",
        "popularity_group": "",
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
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
    )
    return df.dropna(subset=["price_aud", "size_ml"])


def metric_card(title: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"""
        <div class='metric-card'>
            <div class='metric-label'>{title}</div>
            <div class='metric-value'>{value}</div>
            <div class='metric-help'>{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def store_pill(store_name: str) -> str:
    color = STORE_COLORS.get(store_name, "#475569")
    return f"<span class='store-pill' style='background:linear-gradient(135deg, {color}, {color}CC)'>{STORE_META.get(store_name, {}).get('wordmark', store_name)}</span>"


def store_offer_card(row: pd.Series, best_price: float) -> None:
    link = row.get("product_url") or STORE_META.get(row["store"], {}).get("url") or "#"
    chip_color = STORE_COLORS.get(row["store"], "#475569")
    best_class = " best" if abs(float(row["price_aud"]) - float(best_price)) < 0.001 else ""
    stock = "In stock" if bool(row["in_stock"]) else "Availability unknown"
    st.markdown(
        f"""
        <div class='offer-card{best_class}'>
            <div class='offer-top'>
                <div class='store-name'>{row['store']}</div>
                <span class='store-chip' style='background:{chip_color}'>{STORE_META.get(row['store'], {}).get('wordmark', row['store'])}</span>
            </div>
            <div class='price'>${row['price_aud']:,.2f}</div>
            <div class='subtle'>${row['price_per_100ml']:,.2f} per 100mL</div>
            <div class='pills'>
                <span class='pill'>{stock}</span>
                <span class='pill'>{int(row['size_ml'])}mL</span>
                <span class='pill'>Seen {row['last_seen']}</span>
            </div>
            <div style='margin-top:1rem;color:#e5e7eb;font-weight:700'>{row['whisky']}</div>
            <div class='muted'>{row['brand']} • {row['style']}</div>
            <a class='offer-link' href='{link}' target='_blank'>Open store listing ↗</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(best_row: pd.Series, tracked: int, avg_spread: float) -> None:
    st.markdown(
        f"""
        <div class='hero'>
            <div class='eyebrow'>Premium Whisky Price Tracker</div>
            <h1>BoozeDeals AU</h1>
            <div class='hero-copy'>Compare a curated watchlist of 50 high-demand whiskies across Australia's major chains, jump straight to store pages, and spot the best value bottle in seconds.</div>
            <div class='hero-badges'>
                <span class='badge'>Clickable store shortcuts</span>
                <span class='badge'>Best deal today</span>
                <span class='badge'>Top 50 watchlist</span>
                <span class='badge'>Price spread tracking</span>
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
            <div class='best-deal-name'>{best_row['whisky']}</div>
            <div class='best-deal-copy'>Currently cheapest at {best_row['store']} · ${best_row['price_per_100ml']:,.2f} per 100mL · {int(best_row['size_ml'])}mL bottle.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button("Open deal ↗", best_row.get("product_url") or STORE_META.get(best_row["store"], {}).get("url") or "#", use_container_width=True)


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

    hero_col, deal_col = st.columns([1.65, 1], gap="large")
    with hero_col:
        render_hero(baseline_best_row, baseline_board["whisky"].nunique(), baseline_spread)
    with deal_col:
        best_deal_card(baseline_best_row)

    st.markdown("<div class='section-title' style='margin-top:1rem'>Jump to a store</div>", unsafe_allow_html=True)
    logo_cols = st.columns(len(STORE_META))
    for col, (store_name, meta) in zip(logo_cols, STORE_META.items()):
        with col:
            st.markdown(store_pill(store_name), unsafe_allow_html=True)
            st.link_button(f"Open {store_name} ↗", meta["url"], use_container_width=True)

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

    f6, f7, f8 = st.columns([2.6, 1, 1])
    with f6:
        focus_whisky = st.selectbox("Focus whisky", whisky_opts, index=min(8, len(whisky_opts) - 1))
    with f7:
        in_stock_only = st.toggle("In stock only", value=True)
    with f8:
        sort_by = st.selectbox("Sort matrix", ["cheapest_price", "spread", "rank_au", "whisky"])
    st.markdown("<div class='data-note'>Prices in the bundled CSV are a starter dataset and can vary by postcode or promo. Replace them with scraped or manually corrected CSVs for live accuracy.</div></div>", unsafe_allow_html=True)

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

    st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Store comparison for your focus bottle</div><div class='section-subtitle'>Direct links, current visible prices, and the cheapest store highlighted.</div>", unsafe_allow_html=True)
    offer_cols = st.columns(min(4, max(1, len(focus_rows))))
    best_focus_price = float(focus_rows["price_aud"].min())
    for col, (_, row) in zip(offer_cols, focus_rows.iterrows()):
        with col:
            store_offer_card(row, best_focus_price)

    overview_tab, compare_tab, history_tab = st.tabs(["Overview", "Comparison matrix", "Price history"])

    with overview_tab:
        left, right = st.columns([1.1, 0.9])
        with left:
            st.markdown("<div class='section-title'>Top 50 leaderboard</div><div class='section-subtitle'>Best currently visible store price for each whisky in the watchlist.</div>", unsafe_allow_html=True)
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
            chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
                .encode(
                    x=alt.X("best_price:Q", title="Best price (AUD)"),
                    y=alt.Y("whisky:N", sort=alt.SortField(field="rank_au", order="ascending"), title=None),
                    color=alt.Color("best_store:N", scale=alt.Scale(domain=list(STORE_COLORS), range=list(STORE_COLORS.values())), legend=alt.Legend(title="Best store")),
                    tooltip=["rank_au", "whisky", "best_store", alt.Tooltip("best_price:Q", format=".2f")],
                )
                .properties(height=560)
            )
            st.altair_chart(chart, use_container_width=True)

    with compare_tab:
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

        export_df = filtered[[
            "rank_au", "whisky", "expression", "brand", "style", "store", "size_ml", "price_aud", "price_per_100ml", "in_stock", "product_url", "store_url", "last_seen"
        ]].sort_values(["rank_au", "price_aud"])
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "Download filtered rows as CSV",
                data=export_df.to_csv(index=False).encode("utf-8"),
                file_name="boozedeals_filtered.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "Download filtered rows as Excel",
                data=export_excel(export_df),
                file_name="boozedeals_filtered.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with history_tab:
        st.markdown("<div class='section-title'>Price history</div><div class='section-subtitle'>Historical trend for the filtered whiskies and selected stores.</div>", unsafe_allow_html=True)
        history_join = history_df.copy()
        if not history_join.empty:
            history_join = history_join[history_join["whisky"].isin(filtered["whisky"].unique())]
            history_join = history_join[history_join["store"].isin(filtered["store"].unique())]
            line = (
                alt.Chart(history_join)
                .mark_line(point=True)
                .encode(
                    x=alt.X("checked_at:T", title="Checked at"),
                    y=alt.Y("price_aud:Q", title="Price (AUD)"),
                    color=alt.Color("store:N", scale=alt.Scale(domain=list(STORE_COLORS), range=list(STORE_COLORS.values()))),
                    tooltip=["whisky", "store", alt.Tooltip("price_aud:Q", format=".2f"), "checked_at:T"],
                )
                .properties(height=430)
            )
            st.altair_chart(line, use_container_width=True)
            st.markdown("<div class='compact-note'>History is from the bundled sample dataset. Replace it with scheduled snapshots for a real price tracker.</div>", unsafe_allow_html=True)
        else:
            st.info("No history CSV loaded.")

    with st.expander("About the watchlist and accuracy"):
        st.markdown(
            """
            This app uses a curated watchlist of 50 whiskies commonly seen across major Australian retailer bestseller and popular-brand pages.
            It is a practical comparison set for the app, not an official audited national sales ranking.

            Prices in the bundled CSV are starter data. Retailer pricing can differ by postcode, member pricing, same-day delivery, or temporary promos.
            For example, the sample file has been corrected so Glenfiddich 12YO at BWS shows **A$106** instead of the older lower sample value you spotted.
            """
        )


if __name__ == "__main__":
    main()
