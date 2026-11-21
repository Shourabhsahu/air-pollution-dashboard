
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Air Quality Analysis", layout="wide")
st.title("🌍 Air Quality Analysis Dashboard")

# Load data
file = st.file_uploader("Upload CSV", type="csv")

if file:
    df = pd.read_csv(file)
elif os.path.exists("air_quality.csv"):
    df = pd.read_csv("air_quality.csv")
else:
    st.info("Upload an air_quality.csv file.")
    st.stop()

# Clean data
df.columns = df.columns.str.strip()
pollutants = ["PM2.5", "PM10", "NO2"]

required = ["date", "zone"] + pollutants
if any(c not in df.columns for c in required):
    st.error("CSV must contain date, zone, PM2.5, PM10 and NO2.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")

for p in pollutants:
    df[p] = pd.to_numeric(df[p], errors="coerce")

df["zone"] = df["zone"].astype("string").str.strip()
df = df.drop_duplicates().dropna(subset=["date", "zone"])
df = df[df["zone"] != ""]

# Filters
st.sidebar.header("Filters")

pollutant = st.sidebar.selectbox("Select Pollutant", pollutants)

zones = sorted(df["zone"].unique())
selected_zones = st.sidebar.multiselect(
    "Select Zones", zones, default=zones
)

start = st.sidebar.date_input("Start Date", df["date"].min().date())
end = st.sidebar.date_input("End Date", df["date"].max().date())

if start > end:
    st.error("Start date must be before end date.")
    st.stop()

data = df[
    df["zone"].isin(selected_zones) &
    df["date"].dt.date.between(start, end)
].dropna(subset=[pollutant]).copy()

if data.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# Calculate metrics
average = data[pollutant].mean()
maximum = data[pollutant].max()
minimum = data[pollutant].min()

zone_avg = data.groupby("zone")[pollutant].mean()
highest_zone = zone_avg.idxmax()

# Display metrics
st.header(f"{pollutant} Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Average Level", round(average, 2))
c2.metric("Maximum Level", round(maximum, 2))
c3.metric("Minimum Level", round(minimum, 2))
c4.metric("Highest Pollution Zone", highest_zone)

st.divider()

# Pollution trend
st.subheader("1. Pollution Trend Over Time")

daily = data.groupby("date")[pollutant].mean().reset_index()

fig = px.line(
    daily,
    x="date",
    y=pollutant,
    title=f"Daily Average {pollutant}",
    markers=True
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Pollution Level",
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Zone comparison
st.subheader("2. Pollution Comparison Across Zones")

zone_data = zone_avg.reset_index()

fig = px.bar(
    zone_data,
    x="zone",
    y=pollutant,
    color=pollutant,
    title=f"Average {pollutant} by Zone",
    text_auto=".2f"
)

st.plotly_chart(fig, use_container_width=True)

# Monthly analysis
st.subheader("3. Monthly Pollution Analysis")

data["Month"] = data["date"].dt.month
monthly = data.groupby("Month")[pollutant].mean().reset_index()

monthly["Month Name"] = pd.to_datetime(
    monthly["Month"], format="%m"
).dt.month_name()

fig = px.bar(
    monthly,
    x="Month Name",
    y=pollutant,
    title=f"Monthly Average {pollutant}",
    text_auto=".2f"
)

st.plotly_chart(fig, use_container_width=True)

# Generate insights
st.header("4. Automatic Insights")

st.write(f"**Selected Pollutant:** {pollutant}")

st.write(
    f"1. The average pollution level is {average:.2f}."
)

st.write(
    f"2. The highest recorded pollution level is {maximum:.2f}."
)

st.write(
    f"3. The lowest recorded pollution level is {minimum:.2f}."
)

st.write(
    f"4. {highest_zone} has the highest average pollution "
    f"level at {zone_avg.max():.2f}."
)

highest_month = monthly.loc[monthly[pollutant].idxmax(), "Month Name"]
lowest_month = monthly.loc[monthly[pollutant].idxmin(), "Month Name"]

st.write(
    f"5. {highest_month} has the highest monthly average pollution."
)

st.write(
    f"6. {lowest_month} has the lowest monthly average pollution."
)

# Compare beginning and ending trends
if len(daily) >= 2:
    first = daily[pollutant].iloc[0]
    last = daily[pollutant].iloc[-1]

    change = last - first

    if change > 0:
        st.warning(
            f"Pollution increased by {change:.2f} "
            "between the first and last recorded dates."
        )
    elif change < 0:
        st.success(
            f"Pollution decreased by {abs(change):.2f} "
            "between the first and last recorded dates."
        )
    else:
        st.info("Pollution remained unchanged between the endpoints.")

# Dataset
st.header("5. Dataset")

st.dataframe(data, use_container_width=True)

st.download_button(
    "Download Filtered Data",
    data.to_csv(index=False),
    "air_quality_filtered.csv",
    "text/csv"
)
