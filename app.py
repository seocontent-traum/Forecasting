import streamlit as st
from google.cloud import bigquery
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Region-wise Inquiry Forecast")

@st.cache_data
def load_data(country, region):
    client = bigquery.Client()

    query = """
    SELECT
      forecast_date,
      yhat,
      yhat_lower,
      yhat_upper
    FROM `project.dataset.inquiry_prophet_forecast`
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

    return client.query(query, job_config=job_config).to_dataframe()

country = st.selectbox("Country", ["Germany"])
region = st.selectbox("Region", ["Bavaria", "Berlin", "Hamburg"])

df = load_data(country, region)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["forecast_date"], y=df["yhat"], name="Forecast"))
fig.add_trace(go.Scatter(
    x=df["forecast_date"], y=df["yhat_upper"],
    mode="lines", line=dict(width=0), showlegend=False
))
fig.add_trace(go.Scatter(
    x=df["forecast_date"], y=df["yhat_lower"],
    fill="tonexty", mode="lines",
    line=dict(width=0), name="Confidence Interval"
))

st.plotly_chart(fig, use_container_width=True)
