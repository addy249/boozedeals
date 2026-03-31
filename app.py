
from __future__ import annotations

from pathlib import Path
import io
import base64
import pandas as pd
import streamlit as st
import altair as alt

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets" / "stores"
DEFAULT_CSV = DATA_DIR / "sample_whisky_prices.csv"
HISTORY_CSV = DATA_DIR / "sample_price_history.csv"

st.set_page_config(page_title="BoozeDeals AU", page_icon="🥃", layout="wide")

STORE_COLORS = {
    "Dan Murphy's": "#0F8B8D",
    "BWS": "#F97316",
    "Liquorland": "#2563EB",
    "First Choice": "#7C3AED",
}


def local_logo_uri(path_str: str) -> str:
    path = APP_DIR / path_str
    if not path.exists():
        return ""
    return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


STORE_META = {
    "Dan Murphy's": {"url": "https://www.danmurphys.com.au/whisky/all", "logo": local_logo_uri("assets/stores/dan_murphys.svg")},
    "BWS": {"url": "https://bws.com.au/spirits/whisky", "logo": local_logo_uri("assets/stores/bws.svg")},
    "Liquorland": {"url": "https://www.liquorland.com.au/spirits/whisky", "logo": local_logo_uri("assets/stores/liquorland.svg")},
    "First Choice": {"url": "https://www.firstchoiceliquor.com.au/spirits/whisky", "logo": local_logo_uri("assets/stores/first_choice.svg")},
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        .hero {background: linear-gradient(135deg, #111827 0%, #1f2937 45%, #7c2d12 100%); padding: 1.4rem 1.6rem; border-radius: 24px; color: white; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 20px 40px rgba(0,0,0,.18);}
        .hero h1 {margin:0; font-size: 2.2rem;}
        .hero p {margin:.45rem 0 0 0; color:#e5e7eb; font-size:1rem;}
        .mini-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:20px; padding:1rem 1rem .85rem 1rem; box-shadow:0 10px 24px rgba(15,23,42,.06);}
        .store-card {background:#ffffff; border:1px solid #e5e7eb; border-radius:20px; padding:1rem; box-shadow:0 10px 24px rgba(15,23,42,.06); min-height: 235px;}
        .store-card img {height: 42px; max-width: 150px; object-fit: contain; margin-bottom:.75rem;}
        .pill {display:inline-block; padding:.18rem .55rem; border-radius:999px; font-size:.78rem; font-weight:600; background:#f3f4f6; color:#374151; margin-right:.35rem;}
        .section-title {font-size:1.15rem; font-weight:700; margin:.35rem 0 .75rem 0;}
        .subtle {color:#6b7280; font-size:.92rem;}
        .whisky-card {background:#fff; border:1px solid #e5e7eb; border-radius:20px; padding:1rem; box-shadow:0 10px 24px rgba(15,23,42,.06);}
        a.clean-link {text-decoration:none;}
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
    df["label"] = df["whisky"].fillna("") + " — " + df["store"].fillna("")
    df["search_text"] = (
        df[["whisky", "expression", "brand", "store", "state", "style"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
    )
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



def metric_card(title: str, value: str, help_text: str = "") -> None:
    st.markdown(f"<div class='mini-card'><div class='subtle'>{title}</div><div style='font-size:1.7rem;font-weight:800;margin-top:.2rem'>{value}</div><div class='subtle' style='margin-top:.25rem'>{help_text}</div></div>", unsafe_allow_html=True)



def store_offer_card(row: pd.Series) -> None:
    meta = STORE_META.get(row["store"], {})
    logo = meta.get("logo", "")
    price = f"${row['price_aud']:,.2f}"
    per = f"${row['price_per_100ml']:,.2f} / 100mL"
    stock = "In stock" if bool(row["in_stock"]) else "Low / unknown"
    link = row.get("product_url") or meta.get("url") or "#"
    st.markdown(
        f"""
        <div class='store-card'>
            <img src='{logo}' alt='{row['store']}' />
            <div style='font-size:1.28rem;font-weight:800'>{price}</div>
            <div class='subtle' style='margin-top:.15rem'>{per}</div>
            <div style='margin-top:.75rem'><span class='pill'>{stock}</span><span class='pill'>{int(row['size_ml'])}mL</span></div>
            <div style='margin-top:.8rem;font-weight:700'>{row['store']}</div>
            <div class='subtle'>Last seen {row['last_seen']}</div>
            <div style='margin-top:1rem'><a class='clean-link' href='{link}' target='_blank'>🔗 Open store listing</a></div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def main() -> None:
    inject_css()
    default_current, default_history = load_default_data()

    st.markdown(
        """
        <div class='hero'>
            <h1>BoozeDeals AU</h1>
            <p>Compare prices for a curated watchlist of 50 high-demand whiskies in Australia, with store links, price spread tracking, and a cleaner buying view.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Data")
        upload = st.file_uploader("Upload current prices CSV", type=["csv"])
        hist_upload = st.file_uploader("Upload price history CSV", type=["csv"])
        st.caption("Keep the bundled sample data, or replace it with your own scraped exports.")

    current_df = pd.read_csv(upload) if upload else default_current.copy()
    history_df = pd.read_csv(hist_upload) if hist_upload else default_history.copy()
    current_df = normalize_prices(current_df)
    history_df = prepare_history(history_df)

    if current_df.empty:
        st.error("No current price data found.")
        st.stop()

    with st.sidebar:
        st.header("Filters")
        styles = ["All"] + sorted(x for x in current_df["style"].dropna().astype(str).unique() if x)
        brands = ["All"] + sorted(x for x in current_df["brand"].dropna().astype(str).unique() if x)
        stores = sorted(x for x in current_df["store"].dropna().astype(str).unique() if x)
        whiskies = current_df[["rank_au", "whisky"]].drop_duplicates().sort_values("rank_au")
        whisky_opts = whiskies["whisky"].tolist()

        selected_style = st.selectbox("Style", styles)
        selected_brand = st.selectbox("Brand", brands)
        selected_whiskies = st.multiselect("Whiskies", whisky_opts, default=whisky_opts[:12])
        selected_stores = st.multiselect("Stores", stores, default=stores)
        max_rank = int(current_df["rank_au"].max()) if current_df["rank_au"].notna().any() else 50
        rank_limit = st.slider("Top-ranked whiskies", min_value=10, max_value=max_rank, value=max_rank, step=5)
        in_stock_only = st.checkbox("Only show in-stock", value=True)
        sort_by = st.selectbox("Sort comparison table", ["cheapest_price", "spread", "rank_au", "whisky"])
        search_term = st.text_input("Search")

    filtered = current_df.copy()
    filtered = filtered[filtered["rank_au"].fillna(999) <= rank_limit]
    if selected_style != "All":
        filtered = filtered[filtered["style"] == selected_style]
    if selected_brand != "All":
        filtered = filtered[filtered["brand"] == selected_brand]
    if selected_whiskies:
        filtered = filtered[filtered["whisky"].isin(selected_whiskies)]
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
        metric_card("Average shelf price", f"${avg_price:,.2f}", "Filtered results only")
    with c4:
        metric_card("Average store spread", f"${avg_spread:,.2f}", "Gap between cheapest and priciest store")

    st.markdown("<div class='section-title'>Best current offers</div>", unsafe_allow_html=True)
    focus_whisky = st.selectbox("Focus whisky", board["whisky"].tolist(), index=0)
    focus_rows = filtered[filtered["whisky"] == focus_whisky].sort_values("price_aud")

    cols = st.columns(min(4, max(1, len(focus_rows))))
    for col, (_, row) in zip(cols, focus_rows.iterrows()):
        with col:
            store_offer_card(row)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("<div class='section-title'>Top 50 leaderboard</div>", unsafe_allow_html=True)
        show_board = board.copy()
        show_board["best_price"] = show_board["best_price"].map(lambda x: f"${x:,.2f}")
        show_board["best_per_100ml"] = show_board["best_per_100ml"].map(lambda x: f"${x:,.2f}")
        st.dataframe(show_board, use_container_width=True, hide_index=True, column_config={
            "product_url": st.column_config.LinkColumn("Store link", display_text="Open"),
            "rank_au": st.column_config.NumberColumn("AU rank", format="%d"),
            "best_price": "Best price",
            "best_per_100ml": "Best / 100mL",
            "best_store": "Cheapest store",
        })

    with right:
        st.markdown("<div class='section-title'>Price spread chart</div>", unsafe_allow_html=True)
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
            .properties(height=540)
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("<div class='section-title'>Store-by-store comparison matrix</div>", unsafe_allow_html=True)
    compare_show = compare.copy()
    numeric_cols = [c for c in compare_show.columns if c in STORE_META or c in ["cheapest_price", "spread"]]
    for col in numeric_cols:
        compare_show[col] = compare_show[col].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
    st.dataframe(compare_show.sort_values(sort_by), use_container_width=True, hide_index=True)

    st.markdown("<div class='section-title'>Price history</div>", unsafe_allow_html=True)
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
            .properties(height=380)
        )
        st.altair_chart(line, use_container_width=True)
    else:
        st.info("Upload history data to see price movements.")

    export_df = filtered[[
        "rank_au", "whisky", "expression", "brand", "style", "store", "size_ml", "price_aud", "price_per_100ml", "in_stock", "product_url", "store_url", "last_seen"
    ]].sort_values(["rank_au", "price_aud"])
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button("Download filtered rows as CSV", data=export_df.to_csv(index=False).encode("utf-8"), file_name="boozedeals_filtered.csv", mime="text/csv")
    with dl2:
        st.download_button("Download filtered rows as Excel", data=export_excel(export_df), file_name="boozedeals_filtered.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with st.expander("About this sample dataset"):
        st.markdown(
            """
            This seeded watchlist contains 50 whiskies commonly featured across major Australian retailer bestseller, top-seller, premium whisky, and popular-brand pages.
            Treat the ranking as a **curated watchlist**, not an official nationwide sales ranking. Replace the sample CSV with your own scraper output whenever you have fresher live data.
            """
        )


if __name__ == "__main__":
    main()
