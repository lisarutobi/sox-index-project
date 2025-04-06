import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

# Dashboard configuration
app = dash.Dash(__name__)

def load_historical_data():
    data_dir = "/home/ubuntu/sox-index-project/data/historical"
    if not os.path.exists(data_dir):
        print("Data directory not found!")
        return pd.DataFrame(columns=['timestamp', 'last_price', 'net_change', 'day_high'])

    all_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not all_files:
        print("No CSV files found!")
        return pd.DataFrame(columns=['timestamp', 'last_price', 'net_change', 'day_high'])

    dataframes = []
    for file in all_files:
        df = pd.read_csv(file, header=None, names=['timestamp', 'last_price', 'net_change', 'day_high'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame(columns=['timestamp', 'last_price', 'net_change', 'day_high'])
    combined_df = combined_df.sort_values('timestamp')
    combined_df = combined_df.sort_values('timestamp').drop_duplicates('timestamp', keep='last')
    
    print(f"Loaded {len(combined_df)} rows of data. Latest timestamp: {combined_df['timestamp'].max() if not combined_df.empty else 'N/A'}")
    return combined_df

def generate_daily_report():
    """Generate comprehensive daily report"""
    df = load_historical_data()
    if df.empty:
        return {
            'Open Price': 'N/A',
            'Close Price': 'N/A',
            'Daily Volatility': 'N/A',
            'Max Price': 'N/A',
            'Min Price': 'N/A',
            'Total Net Change': 'N/A'
        }

    today = datetime.now().date()
    # Filter today's data
    daily_data = df[df['timestamp'].dt.date == today]
    if daily_data.empty:
        return {
            'Open Price': 'N/A',
            'Close Price': 'N/A',
            'Daily Volatility': 'N/A',
            'Max Price': 'N/A',
            'Min Price': 'N/A',
            'Total Net Change': 'N/A'
        }

    report = {
        'Open Price': daily_data['last_price'].iloc[0],
        'Close Price': daily_data['last_price'].iloc[-1],
        'Daily Volatility': daily_data['last_price'].std(),
        'Max Price': daily_data['last_price'].max(),
        'Min Price': daily_data['last_price'].min(),
        'Total Net Change': daily_data['net_change'].sum()
    }

    return report

# Dashboard layout
app.layout = html.Div([
    html.H1('SOX Index Dashboard'),

    # Notification banner for updates
    html.Div(
        id='update-notification',
        style={
            'backgroundColor': '#e6f3ff',
            'padding': '10px',
            'margin': '10px 0',
            'borderRadius': '5px',
            'textAlign': 'center'
        }
    ),

    # Real-time metrics
    html.Div(id='real-time-metrics'),

    # Price Chart
    dcc.Graph(id='price-chart'),

    # Daily Report
    html.Div(id='daily-report'),

    # Interval for updates
    dcc.Interval(
        id='interval-component',
        interval=5*60*1000,  # 5 minutes
        n_intervals=0
    )
])

@app.callback(
    [Output('real-time-metrics', 'children'),
     Output('price-chart', 'figure'),
     Output('daily-report', 'children'),
     Output('update-notification', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    # Load data
    df = load_historical_data()

    # Real-time metrics
    if df.empty:
        metrics = html.Div([
            html.H3('Current Metrics'),
            html.P("Last Price: N/A"),
            html.P("Net Change: N/A")
        ])
    else:
        latest_data = df.iloc[-1]
        metrics = html.Div([
            html.H3('Current Metrics'),
            html.P(f"Last Price: {float(latest_data['last_price']):.2f}"),
            html.P(f"Net Change: {float(latest_data['net_change']):.2f}")
        ])

    # Price Chart
    price_chart = px.line(df, x='timestamp', y='last_price', title='SOX Index Price Over Time')

    # Daily Report
    daily_report_data = generate_daily_report()
    daily_report = html.Div([
        html.H3('Daily Report'),
        html.Ul([
            html.Li(f"{key}: {float(value):.2f}" if isinstance(value, (float, int)) else f"{key}: {value}")
            for key, value in daily_report_data.items()
        ])
    ])

    # Update notification
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notification = html.P(f"Dashboard last updated at {update_time}")

    return metrics, price_chart, daily_report, notification

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
