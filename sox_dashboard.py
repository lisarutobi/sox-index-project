#!/usr/bin/env python3

import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import os
import flask
import datetime

# Configuration
CSV_FILE = '/home/ubuntu/sox-index-project/sox_index_data.csv'  # Full path for Supervisor
REFRESH_INTERVAL = 60 * 60 * 1000  # Refresh every hour (in milliseconds)
PORT = 8050  # The port to serve your dashboard on

# Create the Dash app
app = dash.Dash(__name__,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server = app.server

# Function to load data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Handle missing or malformed data
        df = df.dropna(subset=['date', 'current_value'])  # Drop rows missing key data
        # Convert date and time columns to datetime, handle errors gracefully
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
        return df
    else:
        return pd.DataFrame()

# Define the layout of the dashboard
app.layout = html.Div([
    html.Div([
        html.H1("Philadelphia SE Semiconductor Index (.SOX) Dashboard",
                style={"textAlign": "center", "color": "#2c3e50", "marginBottom": "20px"}),

        html.Div(id="last-update-time", style={"textAlign": "center", "marginBottom": "20px", "color": "#7f8c8d"}),

        html.Div([
            html.Div([
                html.H3("Current Value", style={"textAlign": "center", "color": "#34495e"}),
                html.H2(id="current-value", style={"textAlign": "center", "fontSize": "32px"})
            ], className="four columns", style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px"}),

            html.Div([
                html.H3("Change", style={"textAlign": "center", "color": "#34495e"}),
                html.H2(id="change-value", style={"textAlign": "center", "fontSize": "32px"})
            ], className="four columns", style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px"}),

            html.Div([
                html.H3("Previous Close", style={"textAlign": "center", "color": "#34495e"}),
                html.H2(id="previous-close", style={"textAlign": "center", "fontSize": "32px"})
            ], className="four columns", style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px"})
        ], className="row", style={"marginBottom": "20px"}),

        html.Div([
            html.Div([
                html.H3("Today's Range", style={"textAlign": "center", "color": "#34495e"}),
                html.H2(id="day-range", style={"textAlign": "center"})
            ], className="six columns", style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px"}),

            html.Div([
                html.H3("52 Week Range", style={"textAlign": "center", "color": "#34495e"}),
                html.H2(id="week52-range", style={"textAlign": "center"})
            ], className="six columns", style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px"})
        ], className="row", style={"marginBottom": "20px"}),

        html.Div([
            html.H3("Historical Price Chart", style={"textAlign": "center", "color": "#34495e", "marginBottom": "20px"}),
            dcc.Graph(id="historical-chart", style={"height": "800px"}),  # Increased graph height
            dcc.Dropdown(
                id="chart-period",
                options=[
                    {"label": "Last Day", "value": "1D"},
                    {"label": "Last Week", "value": "1W"},
                    {"label": "Last Month", "value": "1M"},
                    {"label": "Last 3 Months", "value": "3M"},
                    {"label": "Last Year", "value": "1Y"},
                    {"label": "All Data", "value": "ALL"}
                ],
                value="1M",
                style={"width": "50%", "margin": "0 auto 20px auto"}
            )
        ], style={"backgroundColor": "#ecf0f1", "padding": "20px", "borderRadius": "5px", "marginBottom": "20px"}),

        # Interval component for refreshing the data
        dcc.Interval(
            id='interval-component',
            interval=REFRESH_INTERVAL,
            n_intervals=0
        )
    ], style={"maxWidth": "1400px", "margin": "0 auto", "padding": "20px"})  # Increased maxWidth for larger graph
])

# Define callback to update the dashboard components
@app.callback(
    [Output("current-value", "children"),
     Output("current-value", "style"),
     Output("change-value", "children"),
     Output("change-value", "style"),
     Output("previous-close", "children"),
     Output("day-range", "children"),
     Output("week52-range", "children"),
     Output("historical-chart", "figure"),
     Output("last-update-time", "children")],
    [Input("interval-component", "n_intervals"),
     Input("chart-period", "value")]
)
def update_dashboard(n_intervals, chart_period):
    df = load_data()

    if df.empty:
        return ("No data", {}, "No data", {}, "No data", "No data", "No data",
                go.Figure(), "No data available")

    # Get the latest row
    latest_row = df.iloc[-1]

    # Format the current value
    current_value = f"${latest_row['current_value']:,.2f}"
    current_style = {"textAlign": "center", "fontSize": "32px"}

    # Format the change value and color
    change_amount = latest_row['change_amount'] if pd.notna(latest_row['change_amount']) else 0
    change_percent = latest_row['change_percent'] if pd.notna(latest_row['change_percent']) else 0
    change_text = f"${change_amount:+,.2f} ({change_percent:+.2f}%)"
    if change_amount < 0:
        change_style = {"textAlign": "center", "fontSize": "32px", "color": "#e74c3c"}  # Red
    else:
        change_style = {"textAlign": "center", "fontSize": "32px", "color": "#2ecc71"}  # Green

    # Format previous close
    previous_close = f"${latest_row['previous_close']:,.2f}" if pd.notna(latest_row['previous_close']) else "N/A"

    # Format ranges
    day_range = f"${latest_row['day_low']:,.2f} - ${latest_row['day_high']:,.2f}"
    week52_range = f"${latest_row['week52_low']:,.2f} - ${latest_row['week52_high']:,.2f}"

    # Filter data for the chart based on the selected period
    now = pd.Timestamp.now()
    if chart_period == "1D":
        delta = pd.Timedelta(days=1)
    elif chart_period == "1W":
        delta = pd.Timedelta(weeks=1)
    elif chart_period == "1M":
        delta = pd.Timedelta(days=30)
    elif chart_period == "3M":
        delta = pd.Timedelta(days=90)
    elif chart_period == "1Y":
        delta = pd.Timedelta(days=365)
    else:  # ALL
        delta = None  # Show all data

    if delta:
        start_time = now - delta
        filtered_df = df[df['datetime'] >= start_time]
    else:
        filtered_df = df

    if filtered_df.empty:
        filtered_df = df  # Fallback to all data

    # Create the historical chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered_df['datetime'],
        y=filtered_df['current_value'],
        mode='lines+markers',
        name='SOX Index',
        line=dict(color='#3498db', width=2),
        marker=dict(size=4)
    ))

    fig.update_layout(
        title=f"SOX Index - {chart_period}",
        xaxis_title="Date",
        yaxis_title="Value (USD)",
        template="plotly_white",
        hovermode="x unified",
        height=800,  # Increased height for the figure
        margin=dict(l=50, r=50, t=50, b=50)
    )

    # Format the last update time
    last_update = f"Last updated: {latest_row['date']} {latest_row['time']}"

    return (current_value, current_style, change_text, change_style, previous_close,
            day_range, week52_range, fig, last_update)

# Run the server
if __name__ == "__main__":
    print(f"Starting dashboard server on port {PORT}...")
    app.run(debug=False, host='0.0.0.0', port=PORT)  # Debug=False to remove toolbar
