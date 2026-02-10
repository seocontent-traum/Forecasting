import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go

# -------------------------
# Page configuration
# -------------------------
st.set_page_config(
    page_title="Region-wise Inquiry Forecast",
    layout="wide"
)

st.title("Region-wise Inquiry Forecast")

# -------------------------
# BigQuery Authentication (Streamlit Secrets)
# -------------------------
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

client = bigquery.Client(
    credentials=credentials,
    project=credentials.project_id
)

# -------------------------
# Config (change only table name if needed)
# -------------------------
FORECAST_TABLE = "tfw-zentrum-daten.MLmodel_training.inquiry_prophet_forecast"

# -------------------------
# Helper functions
# -------------------------
@st.cache_data
def load_countries():
    query = f"""
    SELECT DISTINCT country
    FROM `{FORECAST_TABLE}`
    ORDER BY country
    """
    return client.query(query).to_dataframe()["country"].tolist()


@st.cache_data
def load_regions(country):
    query = f"""
    SELECT DISTINCT region
    FROM `{FORECAST_TABLE}`
    WHERE country = @country
    ORDER BY region
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("country", "STRING", country)
        ]
    )
    return client.query(query, job_config=job_config).to_dataframe()["region"].tolist()


@st.cache_data
def load_forecast(country, region):
    query = f"""
    SELECT
      forecast_date,
      yhat,
      yhat_lower,
      yhat_upper
    FROM `{FORECAST_TABLE}`
    WHERE country = @country
      AND region = @region
    ORDER BY forecast_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("country", "STRING", country),
            bigquery.ScalarQueryParameter("region", "STRING", region),
        ]
    )
    df = client.query(query, job_config=job_config).to_dataframe()
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

# -------------------------
# Sidebar controls
# -------------------------
st.sidebar.header("Filters")

countries = load_countries()
country = st.sidebar.selectbox("Country", countries)

regions = load_regions(country)
region = st.sidebar.selectbox("Region", regions)

# -------------------------
# Load forecast data
# -------------------------
df = load_forecast(country, region)

if df.empty:
    st.warning("No forecast data available for this selection.")
    st.stop()

# -------------------------
# Plot
# -------------------------
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["forecast_date"],
        y=df["yhat"],
        mode="lines",
        name="Forecast"
    )
)

fig.add_trace(
    go.Scatter(
        x=df["forecast_date"],
        y=df["yhat_upper"],
        mode="lines",
        line=dict(width=0),
        showlegend=False
    )
)

fig.add_trace(
    go.Scatter(
        x=df["forecast_date"],
        y=df["yhat_lower"],
        mode="lines",
        fill="tonexty",
        name="Confidence Interval",
        line=dict(width=0)
    )
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Inquiries",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Data preview & download
# -------------------------
with st.expander("View forecast data"):
    st.dataframe(df)

st.download_button(
    label="Download forecast as CSV",
    data=df.to_csv(index=False),
    file_name=f"inquiry_forecast_{country}_{region}.csv",
    mime="text/csv"
)
