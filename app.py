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

st.set_page_config(page_title="Whisky Price Dashboard AU", page_icon="🥃", layout="wide")


def load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_default_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    current = load_csv(DEFAULT_CSV)
    history = load_csv(HISTORY_CSV)
    return current, history


def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    expected = {
        "whisky": "",
        "expression": "",
        "brand": "",
        "age": "",
        "abv": "",
        "size_ml": 700,
        "store": "",
        "state": "AU",
        "price_aud": 0.0,
        "in_stock": True,
        "product_url": "",
        "last_seen": "",
        "source": "manual",
    }
    for col, default in expected.items():
        if col not in df.columns:
            df[col] = default

    df["price_aud"] = pd.to_numeric(df["price_aud"], errors="coerce")
    df["size_ml"] = pd.to_numeric(df["size_ml"], errors="coerce")
    if "in_stock" in df.columns:
        df["in_stock"] = df["in_stock"].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    df["price_per_100ml"] = (df["price_aud"] / df["size_ml"]) * 100
    df["label"] = df["whisky"].fillna("") + " — " + df["store"].fillna("")
    df["search_text"] = (
        df[["whisky", "expression", "brand", "store", "state"]]
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


def metric_delta_text(df: pd.DataFrame) -> str:
    if len(df) < 2:
        return "Need 2+ stores"
    prices = df["price_aud"].sort_values().tolist()
    return f"Spread: ${prices[-1] - prices[0]:,.2f}"


def styled_download(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="whisky_prices")
    return output.getvalue()


def main() -> None:
    st.title("🥃 Whisky Price Dashboard AU")
    st.caption("Compare whisky prices across Australian stores, spot the cheapest offer, and track price movements over time.")

    default_current, default_history = load_default_data()

    with st.sidebar:
        st.header("Data")
        upload = st.file_uploader("Upload current prices CSV", type=["csv"])
        hist_upload = st.file_uploader("Upload price history CSV", type=["csv"])
        st.markdown("Use the sample files first, then replace with your own exports or scraped data.")

        st.header("Filters")

    current_df = pd.read_csv(upload) if upload else default_current.copy()
    history_df = pd.read_csv(hist_upload) if hist_upload else default_history.copy()

    current_df = normalize_prices(current_df)
    history_df = prepare_history(history_df)

    if current_df.empty:
        st.error("No current price data found. Upload a CSV or use the included sample data.")
        st.stop()

    with st.sidebar:
        brands = ["All"] + sorted(x for x in current_df["brand"].dropna().astype(str).unique() if x)
        stores = sorted(x for x in current_df["store"].dropna().astype(str).unique() if x)
        whiskies = sorted(x for x in current_df["whisky"].dropna().astype(str).unique() if x)
        sizes = sorted(x for x in current_df["size_ml"].dropna().astype(int).unique())

        selected_brand = st.selectbox("Brand", brands)
        selected_whiskies = st.multiselect("Whiskies", whiskies, default=whiskies[:5])
        selected_stores = st.multiselect("Stores", stores, default=stores)
        selected_sizes = st.multiselect("Bottle sizes (mL)", sizes, default=sizes)
        in_stock_only = st.checkbox("Only show in-stock items", value=True)
        sort_by = st.selectbox("Sort table by", ["price_aud", "price_per_100ml", "store", "whisky"])
        search_term = st.text_input("Search")

    filtered = current_df.copy()
    if selected_brand != "All":
        filtered = filtered[filtered["brand"] == selected_brand]
    if selected_whiskies:
        filtered = filtered[filtered["whisky"].isin(selected_whiskies)]
    if selected_stores:
        filtered = filtered[filtered["store"].isin(selected_stores)]
    if selected_sizes:
        filtered = filtered[filtered["size_ml"].isin(selected_sizes)]
    if in_stock_only:
        filtered = filtered[filtered["in_stock"]]
    if search_term:
        filtered = filtered[filtered["search_text"].str.contains(search_term.lower(), na=False)]

    if filtered.empty:
        st.warning("No rows matched the current filters.")
        st.stop()

    cheapest_row = filtered.sort_values("price_aud").iloc[0]
    avg_price = filtered["price_aud"].mean()
    avg_100ml = filtered["price_per_100ml"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cheapest bottle", f"${cheapest_row['price_aud']:,.2f}", f"{cheapest_row['whisky']} @ {cheapest_row['store']}")
    c2.metric("Average price", f"${avg_price:,.2f}", metric_delta_text(filtered))
    c3.metric("Average per 100mL", f"${avg_100ml:,.2f}")
    c4.metric("Rows shown", f"{len(filtered):,}")

    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("Current price comparison")
        bar = (
            alt.Chart(filtered.sort_values("price_aud"))
            .mark_bar()
            .encode(
                x=alt.X("price_aud:Q", title="Price (AUD)"),
                y=alt.Y("label:N", sort="-x", title="Whisky / Store"),
                tooltip=["whisky", "expression", "store", "price_aud", "size_ml", "price_per_100ml", "state", "last_seen"],
            )
            .properties(height=max(300, min(900, len(filtered) * 28)))
        )
        st.altair_chart(bar, use_container_width=True)

    with right:
        st.subheader("Cheapest store by whisky")
        best = (
            filtered.sort_values(["whisky", "price_aud"])
            .groupby("whisky", as_index=False)
            .first()[["whisky", "store", "price_aud", "price_per_100ml", "product_url"]]
            .rename(columns={"store": "cheapest_store"})
        )
        st.dataframe(best, use_container_width=True, hide_index=True)

    st.subheader("Store comparison table")
    display_cols = [
        "whisky",
        "expression",
        "store",
        "state",
        "size_ml",
        "price_aud",
        "price_per_100ml",
        "in_stock",
        "last_seen",
        "source",
        "product_url",
    ]
    table = filtered[display_cols].sort_values(sort_by, ascending=True)
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered rows as CSV",
        data=table.to_csv(index=False).encode("utf-8"),
        file_name="filtered_whisky_prices.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download filtered rows as Excel",
        data=styled_download(table),
        file_name="filtered_whisky_prices.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.subheader("Price history")
    if not history_df.empty:
        history_join = history_df.copy()
        if selected_whiskies:
            history_join = history_join[history_join["whisky"].isin(selected_whiskies)]
        if selected_stores:
            history_join = history_join[history_join["store"].isin(selected_stores)]
        if search_term:
            text = history_join[["whisky", "store"]].fillna("").agg(" ".join, axis=1).str.lower()
            history_join = history_join[text.str.contains(search_term.lower(), na=False)]

        if not history_join.empty:
            line = (
                alt.Chart(history_join)
                .mark_line(point=True)
                .encode(
                    x=alt.X("checked_at:T", title="Checked at"),
                    y=alt.Y("price_aud:Q", title="Price (AUD)"),
                    color="store:N",
                    tooltip=["whisky", "store", "price_aud", "checked_at"],
                )
                .properties(height=380)
            )
            st.altair_chart(line, use_container_width=True)
        else:
            st.info("No history rows matched the current filters.")
    else:
        st.info("Upload a history CSV to see price trends.")

    with st.expander("CSV format"):
        st.markdown(
            """
**Current prices CSV columns**
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

**Price history CSV columns**
- `whisky`
- `store`
- `price_aud`
- `checked_at`
            """
        )


if __name__ == "__main__":
    main()
