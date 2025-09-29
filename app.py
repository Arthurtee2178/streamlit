import io
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px


@st.cache_data
def load_csv_auto(path: Path):
    """Load the CSV while handling the metadata rows at the top of the provided file.

    The CSV in this workspace has a couple of metadata lines before the actual header
    "Date,Value". This function finds the header line and loads the table that follows.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("date,"):
            header_idx = i
            break
    if header_idx is None:
        df = pd.read_csv(path, parse_dates=[0])
        df.columns = [c.strip() for c in df.columns]
        return df
    data = "\n".join(lines[header_idx:])
    df = pd.read_csv(io.StringIO(data), parse_dates=[0])
    df.columns = [c.strip() for c in df.columns]
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        df = df.sort_values("Date")
        df = df.set_index("Date")
    return df


def sidebar_controls(df: pd.DataFrame):
    st.sidebar.header("View & plot options")
    min_date = pd.to_datetime(df.index.min())
    max_date = pd.to_datetime(df.index.max())
    date_range = st.sidebar.date_input("Date range", [min_date, max_date])
    show_table = st.sidebar.checkbox("Show raw table", value=True)
    chart_type = st.sidebar.selectbox("Chart type", ["Line", "Area", "Bar"])
    smoothing = st.sidebar.checkbox("Show rolling mean", value=False)
    rolling_window = None
    if smoothing:
        rolling_window = st.sidebar.slider("Rolling window (days)", 2, 60, 7)
    resample_freq = st.sidebar.selectbox("Resample / Aggregate", ["None", "W", "M", "Q"])
    show_hist = st.sidebar.checkbox("Show histogram", value=False)
    show_box = st.sidebar.checkbox("Show boxplot by month", value=False)
    return {
        "date_range": date_range,
        "show_table": show_table,
        "chart_type": chart_type,
        "smoothing": smoothing,
        "rolling_window": rolling_window,
        "resample_freq": resample_freq,
        "show_hist": show_hist,
        "show_box": show_box,
    }


def main():
    st.set_page_config(page_title="Historical Rate Explorer", layout="wide")
    st.title("Historical Rate Explorer")

    st.markdown(
        "This app loads `HistoricalRateDetail.csv` (provided) or you can upload your own CSV with `Date` and `Value` columns. It provides interactive charts, aggregation and basic stats."
    )

    uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"])
    default_path = Path(__file__).parent / "HistoricalRateDetail.csv"

    if uploaded is not None:
        try:
            content = uploaded.getvalue().decode("utf-8")
            lines = content.splitlines()
            header_idx = None
            for i, line in enumerate(lines):
                if line.strip().lower().startswith("date,"):
                    header_idx = i
                    break
            if header_idx is None:
                df = pd.read_csv(io.StringIO(content), parse_dates=[0])
                df.columns = [c.strip() for c in df.columns]
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"]).dt.date
                    df = df.set_index("Date").sort_index()
            else:
                data = "\n".join(lines[header_idx:])
                df = pd.read_csv(io.StringIO(data), parse_dates=[0])
                df.columns = [c.strip() for c in df.columns]
                df["Date"] = pd.to_datetime(df["Date"]).dt.date
                df = df.set_index("Date").sort_index()
        except Exception as e:
            st.error(f"Failed to parse uploaded CSV: {e}")
            return
    else:
        if not default_path.exists():
            st.error(f"Default CSV not found at {default_path}. Please upload a CSV with Date,Value columns.")
            return
        df = load_csv_auto(default_path)

    if "Value" not in df.columns:
        numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric:
            df = df.rename(columns={numeric[0]: "Value"})
        else:
            st.error("No numeric 'Value' column found in data.")
            return

    opts = sidebar_controls(df)

    start, end = opts["date_range"]
    if isinstance(start, (list, tuple)):
        start, end = start
    mask = (pd.to_datetime(df.index) >= pd.to_datetime(start)) & (pd.to_datetime(df.index) <= pd.to_datetime(end))
    df_view = df.loc[mask]

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Time series")
        plot_df = df_view.copy()
        if opts["resample_freq"] != "None":
            plot_df = plot_df.resample(opts["resample_freq"]).mean()

        fig = None
        if opts["chart_type"] == "Line":
            fig = px.line(plot_df, y="Value", labels={"index": "Date", "Value": "Value"}, title="Value over time")
        elif opts["chart_type"] == "Area":
            fig = px.area(plot_df, y="Value", labels={"index": "Date", "Value": "Value"}, title="Value over time")
        else:
            fig = px.bar(plot_df, y="Value", labels={"index": "Date", "Value": "Value"}, title="Value over time")

        if opts["smoothing"] and opts["rolling_window"]:
            rolling = df_view["Value"].rolling(window=opts["rolling_window"], min_periods=1).mean()
            fig.add_scatter(x=rolling.index, y=rolling.values, mode="lines", name=f"Rolling {opts['rolling_window']}d")

        st.plotly_chart(fig, use_container_width=True)

        if opts["show_hist"]:
            st.subheader("Distribution")
            fig2 = px.histogram(df_view, x="Value", nbins=30, title="Value distribution")
            st.plotly_chart(fig2, use_container_width=True)

        if opts["show_box"]:
            st.subheader("Boxplot by month")
            tmp = df_view.copy()
            tmp = tmp.reset_index()
            tmp["Month"] = pd.to_datetime(tmp["Date"]).dt.to_period("M").astype(str)
            fig3 = px.box(tmp, x="Month", y="Value", title="Monthly boxplot")
            st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.subheader("Quick stats")
        last = df_view["Value"].iloc[-1]
        change = df_view["Value"].pct_change().iloc[-1] * 100
        st.metric("Last value", f"{last:.4f}", delta=f"{change:.2f}%")
        st.write(df_view["Value"].describe().to_frame().T)

        st.markdown("---")
        st.subheader("Aggregation & transforms")
        st.write("Number of rows:", len(df_view))
        monthly = df_view.resample("M").mean()
        st.write("Monthly mean (last 12):")
        st.dataframe(monthly.tail(12))

    if opts["show_table"]:
        st.subheader("Data")
        st.dataframe(df_view)

    st.download_button("Download filtered CSV", df_view.to_csv().encode("utf-8"), file_name="filtered_rates.csv")


if __name__ == "__main__":
    main()
