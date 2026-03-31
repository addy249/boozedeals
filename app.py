
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
    "Dan Murphy's": "#0EA5A4",
    "BWS": "#F97316",
    "Liquorland": "#2563EB",
    "First Choice": "#7C3AED",
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
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"], footer, #MainMenu, header {display:none !important;}
        .block-container {max-width: 1380px; padding-top: 1.2rem; padding-bottom: 2rem;}
        .app-shell {background: radial-gradient(circle at top left, rgba(249,115,22,0.10), transparent 22%), radial-gradient(circle at top right, rgba(37,99,235,0.12), transparent 20%);}
        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #111827 45%, #4a1d12 100%);
            border: 1px solid rgba(255,255,255,0.09);
            box-shadow: 0 26px 70px rgba(0,0,0,.35);
            border-radius: 28px;
            padding: 1.9rem 2rem;
            color: white;
        }
        .hero h1 {margin: 0; font-size: 2.7rem; line-height: 1.1; letter-spacing: -0.03em;}
        .hero p {margin: .7rem 0 0 0; color: #d1d5db; font-size: 1.05rem; max-width: 900px;}
        .hero-badges {margin-top: 1rem; display:flex; gap:.6rem; flex-wrap:wrap;}
        .badge {padding:.36rem .68rem; border-radius:999px; font-size:.83rem; font-weight:700; background:rgba(255,255,255,.09); color:#f8fafc; border:1px solid rgba(255,255,255,.09);}
        .panel {
            background: rgba(17,24,39,.78);
            border: 1px solid rgba(255,255,255,.07);
            backdrop-filter: blur(16px);
            box-shadow: 0 18px 40px rgba(0,0,0,.22);
            border-radius: 24px;
            padding: 1rem 1rem 1.1rem 1rem;
        }
        .panel-title {font-size: 1rem; font-weight: 800; color: #f8fafc; margin-bottom: .8rem;}
        .metric-card {
            background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
            border: 1px solid rgba(255,255,255,.09);
            border-radius: 22px;
            padding: 1rem 1rem .9rem 1rem;
            min-height: 122px;
        }
        .metric-label {font-size:.88rem; color:#94a3b8;}
        .metric-value {font-size:2rem; color:#f8fafc; font-weight:800; margin-top:.25rem; line-height:1.05;}
        .metric-help {font-size:.9rem; color:#cbd5e1; margin-top:.35rem;}
        .section-title {font-size:1.18rem; font-weight:800; margin: .2rem 0 .85rem 0; color:#f8fafc;}
        .section-subtitle {font-size:.92rem; color:#94a3b8; margin: -.35rem 0 .85rem 0;}
        .offer-card {
            background: linear-gradient(180deg, rgba(15,23,42,.78), rgba(17,24,39,.92));
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 24px;
            padding: 1.05rem;
            min-height: 255px;
            box-shadow: 0 18px 44px rgba(0,0,0,.24);
        }
        .offer-card.best {border-color: rgba(249,115,22,.55); box-shadow: 0 18px 50px rgba(249,115,22,.15);}
        .offer-top {display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.8rem;}
        .store-chip {font-size:.78rem; font-weight:800; border-radius:999px; padding:.28rem .58rem; color:white;}
        .price {font-size:2rem; font-weight:800; color:#ffffff; letter-spacing:-0.03em;}
        .subtle {color:#cbd5e1; font-size:.94rem;}
        .muted {color:#94a3b8; font-size:.85rem;}
        .pills {display:flex; gap:.45rem; flex-wrap:wrap; margin-top:.9rem;}
        .pill {display:inline-block; padding:.22rem .56rem; border-radius:999px; font-size:.78rem; font-weight:700; background:rgba(255,255,255,.08); color:#e5e7eb; border:1px solid rgba(255,255,255,.08);}
        .offer-link {display:inline-block; margin-top:1rem; color:#93c5fd; text-decoration:none; font-weight:700;}
        .offer-link:hover {text-decoration:underline;}
        .toolbar-spacer {height: .3rem;}
        .store-logo-wrap {height: 42px; display:flex; align-items:center;}
        .store-logo-svg {max-height: 36px; width: auto; max-width: 150px;}
        div[data-testid="stDataFrame"] {border: 1px solid rgba(255,255,255,.08); border-radius: 18px; overflow: hidden;}
        div[data-testid="stDownloadButton"] button, div[data-testid="stLinkButton"] a, div.stButton > button {
            border-radius: 12px !important;
            font-weight: 700 !important;
        }
        .tiny-note {font-size:.82rem; color:#94a3b8; margin-top:.35rem;}
        </style>
        <div class='app-shell'></div>
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
    pivot = filtered.pivot_table(index=["rank_au", "whisky", "brand", "size_ml"], columns="store", values="price_aud", aggfunc="min").reset_index()
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
        "store_logo": "",
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


def render_logo(store_name: str) -> str:
    html = STORE_META.get(store_name, {}).get("logo_html", "")
    if html:
        return f"<div class='store-logo-wrap'>{html}</div>"
    return f"<div style='font-weight:800;color:#f8fafc'>{store_name}</div>"


def store_offer_card(row: pd.Series, best_price: float) -> None:
    link = row.get("product_url") or STORE_META.get(row["store"], {}).get("url") or "#"
    chip_color = STORE_COLORS.get(row["store"], "#475569")
    best_class = " best" if float(row["price_aud"]) == float(best_price) else ""
    stock = "In stock" if bool(row["in_stock"]) else "Availability unknown"
    st.markdown(
        f"""
        <div class='offer-card{best_class}'>
            <div class='offer-top'>
                {render_logo(row['store'])}
                <span class='store-chip' style='background:{chip_color}'>{row['store']}</span>
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


def main() -> None:
    inject_css()
    default_current, default_history = load_default_data()

    current_df = normalize_prices(default_current.copy())
    history_df = prepare_history(default_history.copy())

    if current_df.empty:
        st.error("No current price data found.")
        st.stop()

    st.markdown(
        """
        <div class='hero'>
            <h1>BoozeDeals AU</h1>
            <p>A cleaner whisky price comparison dashboard for Australia. Compare the curated top-50 watchlist across major stores, jump straight to listings, and spot the best live bottle faster.</p>
            <div class='hero-badges'>
                <span class='badge'>Store links</span>
                <span class='badge'>Top 50 watchlist</span>
                <span class='badge'>Price spread tracking</span>
                <span class='badge'>Professional buying view</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='toolbar-spacer'></div>", unsafe_allow_html=True)

    with st.container(border=False):
        st.markdown("<div class='panel'><div class='panel-title'>Filters</div></div>", unsafe_allow_html=True)
        f1, f2, f3, f4, f5 = st.columns([1, 1, 1.2, 1.1, 1.1])
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

        f6, f7, f8 = st.columns([2.5, 1, 1])
        with f6:
            focus_whisky = st.selectbox("Focus whisky", whisky_opts, index=min(8, len(whisky_opts)-1))
        with f7:
            in_stock_only = st.toggle("In stock only", value=True)
        with f8:
            sort_by = st.selectbox("Sort matrix", ["cheapest_price", "spread", "rank_au", "whisky"])
        st.markdown("<div class='tiny-note'>The left sidebar has been removed. To change datasets later, you can add upload controls back or replace the CSV files directly in the repo.</div>", unsafe_allow_html=True)

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
        metric_card("Average store spread", f"${avg_spread:,.2f}", "Difference between highest and lowest store price")

    st.markdown("<div class='section-title'>Best current offers</div><div class='section-subtitle'>Direct comparison for your selected bottle, with logos and quick links.</div>", unsafe_allow_html=True)
    offer_cols = st.columns(min(4, max(1, len(focus_rows))))
    best_focus_price = float(focus_rows['price_aud'].min())
    for col, (_, row) in zip(offer_cols, focus_rows.iterrows()):
        with col:
            store_offer_card(row, best_focus_price)

    overview_tab, compare_tab, history_tab = st.tabs(["Overview", "Comparison matrix", "Price history"])

    with overview_tab:
        left, right = st.columns([1.12, 0.88])
        with left:
            st.markdown("<div class='section-title'>Top 50 leaderboard</div><div class='section-subtitle'>Best currently visible store price for each whisky.</div>", unsafe_allow_html=True)
            show_board = board.copy()
            show_board["best_price"] = show_board["best_price"].map(lambda x: f"${x:,.2f}")
            show_board["best_per_100ml"] = show_board["best_per_100ml"].map(lambda x: f"${x:,.2f}")
            st.dataframe(
                show_board,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "product_url": st.column_config.LinkColumn("Store link", display_text="Open"),
                    "rank_au": st.column_config.NumberColumn("AU rank", format="%d"),
                    "best_store": "Cheapest store",
                    "best_price": "Best price",
                    "best_per_100ml": "Best / 100mL",
                },
            )
        with right:
            st.markdown("<div class='section-title'>Best-price chart</div><div class='section-subtitle'>Top 20 whiskies by rank with the cheapest currently shown store.</div>", unsafe_allow_html=True)
            chart_df = board.head(20).copy()
            chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
                .encode(
                    x=alt.X("best_price:Q", title="Best price (AUD)"),
                    y=alt.Y("whisky:N", sort="-x", title=None),
                    color=alt.Color("best_store:N", scale=alt.Scale(domain=list(STORE_COLORS), range=list(STORE_COLORS.values()))),
                    tooltip=["rank_au", "whisky", "best_store", alt.Tooltip("best_price:Q", format=".2f")],
                )
                .properties(height=560)
            )
            st.altair_chart(chart, use_container_width=True)

    with compare_tab:
        st.markdown("<div class='section-title'>Store-by-store comparison matrix</div><div class='section-subtitle'>Use this to spot where the same bottle is cheapest and how wide the spread is.</div>", unsafe_allow_html=True)
        compare_show = compare.copy().sort_values(sort_by)
        numeric_cols = [c for c in compare_show.columns if c in STORE_META or c in ["cheapest_price", "spread"]]
        for col in numeric_cols:
            compare_show[col] = compare_show[col].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
        st.dataframe(compare_show, use_container_width=True, hide_index=True)

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
        else:
            st.info("No history CSV loaded.")

    with st.expander("About the watchlist"):
        st.markdown(
            """
            This uses a curated watchlist of 50 whiskies commonly seen across major Australian retailer bestseller and popular-brand pages.
            It is a practical comparison set for the app, not an official national audited sales ranking.
            """
        )


if __name__ == "__main__":
    main()
