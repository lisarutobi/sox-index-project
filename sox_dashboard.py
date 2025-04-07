#!/usr/bin/env python3

import pandas as pd
import numpy as np
import dash
from dash import dcc, html
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
import os
import datetime
import logging

# Set up basic logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
CSV_FILE = '/home/ubuntu/sox-index-project/sox_index_data.csv'
REFRESH_INTERVAL = 5 * 60 * 1000  # Refresh every 5 minutes (in milliseconds)
PORT = 8050
THEME_COLORS = {
    'primary': '#2c3e50',
    'secondary': '#34495e',
    'light': '#ecf0f1',
    'positive': '#2ecc71',
    'negative': '#e74c3c',
    'accent1': '#3498db',
    'accent2': '#e67e22',
    'accent3': '#9b59b6',
    'text_muted': '#7f8c8d'
}

# Create the Dash app with custom CSS
app = dash.Dash(
    __name__,
    external_stylesheets=['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
server = app.server
app.title = "SOX Index Dashboard"

# Custom CSS for additional styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f7fa;
            }
            .metric-card {
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 15px rgba(0,0,0,0.1);
            }
            .chart-container {
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            .chart-container:hover {
                box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            }
            @media (max-width: 768px) {
                .mobile-full-width {
                    width: 100% !important;
                    margin-bottom: 15px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Cache for data
data_cache = {'df': None, 'last_load_time': None}

# Function to load data and calculate metrics with caching
def load_data(force_reload=False):
    current_time = datetime.datetime.now()

    # Use cached data if available and less than 5 minutes old
    if not force_reload and data_cache['df'] is not None and data_cache['last_load_time'] is not None:
        time_diff = (current_time - data_cache['last_load_time']).total_seconds()
        if time_diff < 300:  # Less than 5 minutes
            return data_cache['df']

    try:
        if os.path.exists(CSV_FILE):
            logging.info(f"Loading data from {CSV_FILE}")
            df = pd.read_csv(CSV_FILE)
            df = df.dropna(subset=['date', 'current_value'])

            # Convert date and time to datetime
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')

            # Filter for market hours
            df = df[df['datetime'].dt.time.between(datetime.time(9, 30), datetime.time(16, 0))]

            # Add new derived metrics
            df['ma20'] = df['current_value'].rolling(window=20).mean()
            df['ma50'] = df['current_value'].rolling(window=50).mean()
            df['ma200'] = df['current_value'].rolling(window=200).mean()

            # Calculate Bollinger Bands (20-period, 2 standard deviations)
            df['rolling_std'] = df['current_value'].rolling(window=20).std()
            df['upper_band'] = df['ma20'] + (df['rolling_std'] * 2)
            df['lower_band'] = df['ma20'] - (df['rolling_std'] * 2)

            # Calculate RSI (14-period)
            delta = df['current_value'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # Calculate MACD
            df['ema12'] = df['current_value'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['current_value'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema12'] - df['ema26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']

            # Group by date for daily metrics
            df['day_open'] = df.groupby(df['datetime'].dt.date)['current_value'].transform('first')

            # Calculate daily returns
            df['daily_return'] = df.groupby(df['datetime'].dt.date)['current_value'].pct_change()

            # Update cache
            data_cache['df'] = df
            data_cache['last_load_time'] = current_time

            logging.info(f"Data loaded successfully with {len(df)} records")
            return df
        else:
            logging.error(f"CSV file not found: {CSV_FILE}")
            return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Define the layout with responsive design
app.layout = html.Div([
    html.Div([
        html.Div([
            html.Img(src="/assets/chip_icon.png", style={"height": "40px", "marginRight": "15px"}, className="d-none d-md-block"),
            html.H1("Philadelphia SE Semiconductor Index (.SOX)", style={"color": THEME_COLORS['primary']})
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "10px"}),

        html.Div([
            html.Span(id="last-update-time", style={"color": THEME_COLORS['text_muted']}),
            html.Button(
                html.I(className="fas fa-sync-alt"),
                id="refresh-button",
                style={
                    "marginLeft": "15px",
                    "border": "none",
                    "borderRadius": "50%",
                    "width": "30px",
                    "height": "30px",
                    "backgroundColor": THEME_COLORS['accent1'],
                    "color": "white",
                    "cursor": "pointer"
                }
            )
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "25px"}),

        # First row - Key metrics
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Current Value", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="current-value", style={"textAlign": "center", "fontSize": "28px", "fontWeight": "bold", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "20px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("Change", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.Div([
                        html.H2(id="change-value", style={"textAlign": "center", "fontSize": "28px", "fontWeight": "bold", "margin": "0"}),
                        html.Div(id="change-icon", style={"marginLeft": "10px", "fontSize": "24px"})
                    ], style={"display": "flex", "justifyContent": "center", "alignItems": "center"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "20px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("VWAP", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="vwap-value", style={"textAlign": "center", "fontSize": "28px", "fontWeight": "bold", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "20px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("RSI (14)", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="rsi-value", style={"textAlign": "center", "fontSize": "28px", "fontWeight": "bold", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "20px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width")
        ], className="row", style={"marginBottom": "20px"}),

        # Second row - Additional metrics
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Today's Range", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="day-range", style={"textAlign": "center", "fontSize": "20px", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "15px", "borderRadius": "10px", "height": "100%"})
            ], className="four columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("Range Since Feb 6", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="total-range", style={"textAlign": "center", "fontSize": "20px", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "15px", "borderRadius": "10px", "height": "100%"})
            ], className="four columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("Previous Close", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="previous-close", style={"textAlign": "center", "fontSize": "20px", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "15px", "borderRadius": "10px", "height": "100%"})
            ], className="four columns mobile-full-width")
        ], className="row", style={"marginBottom": "20px"}),

        # Third row - Technical metrics
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Volatility (Daily)", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="volatility-value", style={"textAlign": "center", "fontSize": "20px", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "15px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("MA Crossover", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="ma-signal", style={"textAlign": "center", "fontSize": "20px", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "15px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("MACD Signal", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="macd-signal", style={"textAlign": "center", "fontSize": "20px", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "15px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width"),

            html.Div([
                html.Div([
                    html.H3("Bollinger Position", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "10px"}),
                    html.H2(id="bollinger-position", style={"textAlign": "center", "fontSize": "20px", "margin": "0"})
                ], className="metric-card", style={"backgroundColor": THEME_COLORS['light'], "padding": "15px", "borderRadius": "10px", "height": "100%"})
            ], className="three columns mobile-full-width")
        ], className="row", style={"marginBottom": "20px"}),

        # Chart navigation tabs
        html.Div([
            dcc.Tabs(id="chart-tabs", value="trend-tab", children=[
                dcc.Tab(label="Price Trend with Indicators", value="trend-tab"),
                dcc.Tab(label="OHLC Candlestick", value="candle-tab"),
                dcc.Tab(label="Technical Analysis", value="technical-tab"),
                dcc.Tab(label="Performance", value="performance-tab")
            ], style={"fontFamily": "'Segoe UI', sans-serif"})
        ], style={"marginBottom": "20px"}),

        # Chart period selector
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id="chart-period",
                    options=[
                        {"label": "Today", "value": "Today"},
                        {"label": "Last Day", "value": "1D"},
                        {"label": "Last Week", "value": "1W"},
                        {"label": "Last Month", "value": "1M"},
                        {"label": "Last 3 Months", "value": "3M"},
                        {"label": "All Data", "value": "All"}
                    ],
                    value="1D",
                    clearable=False
                )
            ], className="six columns", style={"width": "300px", "marginRight": "20px"}),

            html.Div([
                dcc.RadioItems(
                    id="chart-interval",
                    options=[
                        {"label": "5 min", "value": "5min"},
                        {"label": "15 min", "value": "15min"},
                        {"label": "30 min", "value": "30min"},
                        {"label": "1 hour", "value": "1hour"},
                        {"label": "EOD", "value": "1day"}
                    ],
                    value="5min",
                    labelStyle={"display": "inline-block", "marginRight": "15px"}
                )
            ], className="six columns")
        ], className="row", style={"marginBottom": "15px"}),

        # Chart container
        html.Div([
            html.Div(id="chart-container", className="chart-container", style={
                "backgroundColor": THEME_COLORS['light'],
                "padding": "20px",
                "borderRadius": "10px",
                "marginBottom": "20px"
            })
        ], className="row"),

        # Hidden divs for storing data
        html.Div(id="chart-data-store", style={"display": "none"}),

        # Interval component for auto-refresh
        dcc.Interval(
            id='interval-component',
            interval=REFRESH_INTERVAL,
            n_intervals=0
        )
    ], style={"maxWidth": "1400px", "margin": "0 auto", "padding": "20px"})
])

# Callback to handle chart tab rendering
@app.callback(
    Output("chart-container", "children"),
    [Input("chart-tabs", "value"),
     Input("chart-period", "value"),
     Input("chart-interval", "value"),
     Input("chart-data-store", "children")]
)
def update_chart_content(tab_value, period_value, interval_value, _):
    df = load_data()
    if df.empty:
        return html.Div("No data available", style={"textAlign": "center", "padding": "40px"})

    # Filter data based on selected period
    filtered_df = filter_data_by_period(df, period_value)

    # Resample data based on selected interval
    if interval_value != "5min" and not filtered_df.empty:
        filtered_df = resample_data(filtered_df, interval_value)

    if tab_value == "trend-tab":
        return [
            html.H3("Price Trend with Technical Indicators", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "20px"}),
            dcc.Graph(figure=create_trend_chart(filtered_df, period_value), style={"height": "650px"})
        ]

    elif tab_value == "candle-tab":
        return [
            html.H3("SOX Index Candlestick Chart", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "20px"}),
            dcc.Graph(figure=create_candlestick_chart(filtered_df, period_value), style={"height": "650px"})
        ]

    elif tab_value == "technical-tab":
        return [
            html.H3("Technical Analysis Dashboard", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "20px"}),
            dcc.Graph(figure=create_technical_chart(filtered_df, period_value), style={"height": "800px"})
        ]

    elif tab_value == "performance-tab":
        return [
            html.H3("SOX Index Performance", style={"textAlign": "center", "color": THEME_COLORS['secondary'], "marginBottom": "20px"}),
            dcc.Graph(figure=create_performance_chart(filtered_df, period_value), style={"height": "650px"})
        ]

# Callback to update metrics
@app.callback(
    [Output("current-value", "children"),
     Output("change-value", "children"),
     Output("change-icon", "children"),
     Output("vwap-value", "children"),
     Output("rsi-value", "children"),
     Output("day-range", "children"),
     Output("total-range", "children"),
     Output("previous-close", "children"),
     Output("volatility-value", "children"),
     Output("ma-signal", "children"),
     Output("macd-signal", "children"),
     Output("bollinger-position", "children"),
     Output("last-update-time", "children")],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_metrics(_, __):
    df = load_data()
    if df.empty:
        return ["N/A"] * 11 + ["Last update: N/A"]

    # Get the latest data point
    latest = df.iloc[-1]

    # Calculate metrics
    current_value = f"{latest['current_value']:.2f}"
    previous_close = f"{df.iloc[-2]['current_value']:.2f}" if len(df) > 1 else "N/A"
    change_value = f"{(latest['current_value'] - df.iloc[-2]['current_value']):.2f}" if len(df) > 1 else "N/A"
    change_icon = "▲" if latest['current_value'] > df.iloc[-2]['current_value'] else "▼" if len(df) > 1 else ""
    vwap_value = f"{latest['current_value']:.2f}"  # Assuming VWAP is the current value for simplicity
    rsi_value = f"{latest['rsi']:.2f}"
    day_range = f"{df['current_value'].min():.2f} - {df['current_value'].max():.2f}"
    total_range = f"{df['current_value'].min():.2f} - {df['current_value'].max():.2f}"
    volatility_value = f"{latest['rolling_std']:.2f}"
    ma_signal = "Bullish" if latest['ma20'] > latest['ma50'] else "Bearish"
    macd_signal = "Bullish" if latest['macd'] > latest['macd_signal'] else "Bearish"
    bollinger_position = "Overbought" if latest['current_value'] > latest['upper_band'] else "Oversold" if latest['current_value'] < latest['lower_band'] else "Neutral"

    last_update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [current_value, change_value, change_icon, vwap_value, rsi_value, day_range, total_range, previous_close, volatility_value, ma_signal, macd_signal, bollinger_position, f"Last update: {last_update_time}"]

# Function to filter data by selected period
def filter_data_by_period(df, period):
    if df.empty:
        return df

    now = pd.Timestamp.now()

    if period == "Today":
        today = pd.Timestamp.now().date()
        return df[df['datetime'].dt.date == today]
    elif period == "1D":
        delta = pd.Timedelta(days=1)
    elif period == "1W":
        delta = pd.Timedelta(weeks=1)
    elif period == "1M":
        delta = pd.Timedelta(days=30)
    elif period == "3M":
        delta = pd.Timedelta(days=90)
    elif period == "All":
        return df
    else:
        delta = pd.Timedelta(days=1)

    start_time = now - delta
    filtered_df = df[df['datetime'] >= start_time]

    if filtered_df.empty:
        filtered_df = df.tail(100)

    return filtered_df

# Function to resample data by interval
def resample_data(df, interval):
    if df.empty:
        return df

    # Set datetime as index for resampling
    df_copy = df.copy()
    df_copy.set_index('datetime', inplace=True)

    # Determine resample rule
    if interval == "15min":
        rule = '15min'
    elif interval == "30min":
        rule = '30min'
    elif interval == "1hour":
        rule = '1H'
    elif interval == "1day":
        rule = '1D'
    else:
        # Return original data for 5min
        df_copy.reset_index(inplace=True)
        return df_copy

    # Perform resampling
    resampled = df_copy['current_value'].resample(rule).ohlc()

    # Calculate additional metrics for resampled data
    if 'ma20' in df_copy.columns:
        resampled['ma20'] = df_copy['ma20'].resample(rule).last()
    if 'ma50' in df_copy.columns:
        resampled['ma50'] = df_copy['ma50'].resample(rule).last()
    if 'ma200' in df_copy.columns:
        resampled['ma200'] = df_copy['ma200'].resample(rule).last()
    if 'upper_band' in df_copy.columns:
        resampled['upper_band'] = df_copy['upper_band'].resample(rule).last()
    if 'lower_band' in df_copy.columns:
        resampled['lower_band'] = df_copy['lower_band'].resample(rule).last()
    if 'rsi' in df_copy.columns:
        resampled['rsi'] = df_copy['rsi'].resample(rule).last()
    if 'macd' in df_copy.columns:
        resampled['macd'] = df_copy['macd'].resample(rule).last()
    if 'macd_signal' in df_copy.columns:
        resampled['macd_signal'] = df_copy['macd_signal'].resample(rule).last()
    if 'macd_hist' in df_copy.columns:
        resampled['macd_hist'] = df_copy['macd_hist'].resample(rule).last()

    # Reset index to get datetime back as a column
    resampled.reset_index(inplace=True)

    # Rename columns to match original format
    resampled.rename(columns={
        'open': 'open_value',
        'high': 'day_high',
        'low': 'day_low',
        'close': 'current_value'
    }, inplace=True)

    return resampled

# Create trend chart
def create_trend_chart(df, period):
    if df.empty:
        return go.Figure()

    fig = go.Figure()

    # Add main price line
    fig.add_trace(go.Scatter(
        x=df['datetime'] if 'datetime' in df.columns else df.index,
        y=df['current_value'],
        mode='lines',
        name='Price',
        line=dict(color=THEME_COLORS['accent1'], width=2)
    ))

    # Add moving averages if available
    if 'ma20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['ma20'],
            mode='lines',
            name='MA20',
            line=dict(color=THEME_COLORS['accent2'], width=1.5, dash='dash')
        ))

    if 'ma50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['ma50'],
            mode='lines',
            name='MA50',
            line=dict(color=THEME_COLORS['positive'], width=1.5, dash='dash')
        ))

    if 'ma200' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['ma200'],
            mode='lines',
            name='MA200',
            line=dict(color=THEME_COLORS['accent3'], width=1.5, dash='dash')
        ))

    # Add Bollinger Bands if available
    if 'upper_band' in df.columns and 'lower_band' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['upper_band'],
            mode='lines',
            name='Upper Band',
            line=dict(color='rgba(0, 0, 255, 0.3)', width=1),
            showlegend=True
        ))

        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['lower_band'],
            mode='lines',
            name='Lower Band',
            line=dict(color='rgba(0, 0, 255, 0.3)', width=1),
            fill='tonexty',
            fillcolor='rgba(0, 0, 255, 0.05)',
            showlegend=True
        ))

    fig.update_layout(
        title=f"SOX Index Trend - {period}",
        xaxis_title="Date/Time",
        yaxis_title="Value (USD)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig

# Create candlestick chart
def create_candlestick_chart(df, period):
    if df.empty:
        return go.Figure()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.7, 0.3],
                        specs=[[{"type": "candlestick"}], [{"type": "bar"}]])

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df['datetime'] if 'datetime' in df.columns else df.index,
        open=df['open_value'] if 'open_value' in df.columns else df['current_value'],
        high=df['day_high'] if 'day_high' in df.columns else df['current_value'],
        low=df['day_low'] if 'day_low' in df.columns else df['current_value'],
        close=df['current_value'],
        name='OHLC',
        increasing_line_color=THEME_COLORS['positive'],
        decreasing_line_color=THEME_COLORS['negative']
    ), row=1, col=1)

    # Create dummy volume data (for visualization purposes)
    if 'datetime' in df.columns:
        df['dummy_volume'] = np.random.randint(10000, 50000, size=len(df))
        df['dummy_volume'] = df['dummy_volume'] * (1 + abs(df['current_value'].pct_change()))

        fig.add_trace(go.Bar(
            x=df['datetime'],
            y=df['dummy_volume'],
            name='Volume',
            marker_color='rgba(52, 152, 219, 0.5)'
        ), row=2, col=1)

    fig.update_layout(
        title=f"SOX Index Candlestick - {period}",
        xaxis_title="Date/Time",
        yaxis_title="Value (USD)",
        xaxis2_title="Date/Time",
        yaxis2_title="Volume",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # Update y-axis properties
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig

# Create technical analysis chart
def create_technical_chart(df, period):
    if df.empty:
        return go.Figure()

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                       vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2],
                       specs=[[{"type": "candlestick"}], [{"type": "scatter"}], [{"type": "bar"}]])

    # Add candlestick chart with Bollinger Bands
    fig.add_trace(go.Candlestick(
        x=df['datetime'] if 'datetime' in df.columns else df.index,
        open=df['open_value'] if 'open_value' in df.columns else df['current_value'],
        high=df['day_high'] if 'day_high' in df.columns else df['current_value'],
        low=df['day_low'] if 'day_low' in df.columns else df['current_value'],
        close=df['current_value'],
        name='OHLC',
        increasing_line_color=THEME_COLORS['positive'],
        decreasing_line_color=THEME_COLORS['negative']
    ), row=1, col=1)

    # Add Bollinger Bands if available
    if 'upper_band' in df.columns and 'lower_band' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['upper_band'],
            mode='lines',
            name='Upper Band',
            line=dict(color='rgba(0, 0, 255, 0.3)', width=1),
            showlegend=True
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['lower_band'],
            mode='lines',
            name='Lower Band',
            line=dict(color='rgba(0, 0, 255, 0.3)', width=1),
            fill='tonexty',
            fillcolor='rgba(0, 0, 255, 0.05)',
            showlegend=True
        ), row=1, col=1)

    # Add RSI if available
    if 'rsi' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['rsi'],
            mode='lines',
            name='RSI',
            line=dict(color=THEME_COLORS['accent2'], width=2)
        ), row=2, col=1)

        # Add RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red",
                     annotation_text="Overbought", annotation_position="right", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                     annotation_text="Oversold", annotation_position="right", row=2, col=1)

    # Add MACD if available
    if 'macd' in df.columns and 'macd_signal' in df.columns and 'macd_hist' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['macd'],
            mode='lines',
            name='MACD',
            line=dict(color=THEME_COLORS['accent1'], width=2)
        ), row=3, col=1)

        fig.add_trace(go.Scatter(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['macd_signal'],
            mode='lines',
            name='Signal',
            line=dict(color=THEME_COLORS['accent3'], width=2)
        ), row=3, col=1)

        fig.add_trace(go.Bar(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['macd_hist'],
            name='Histogram',
            marker_color=np.where(df['macd_hist'] >= 0, THEME_COLORS['positive'], THEME_COLORS['negative'])
        ), row=3, col=1)

    # Update layout
    fig.update_layout(
        title=f"SOX Index Technical Analysis - {period}",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=800
    )

    # Update axes
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_xaxes(title_text="Date/Time", row=3, col=1)

    return fig

if __name__ == "__main__":
    print(f"Starting dashboard server on port {PORT}...")
    app.run(debug=False, host='0.0.0.0', port=PORT)
