import re
import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import threading
import sys
from collections import deque
import logging
from flask import Flask

# Suppress Dash web logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

MAX_POINTS = 500
data = {
    'timestamp':         deque(maxlen=MAX_POINTS),
    'prev':              deque(maxlen=MAX_POINTS),
    'updated':           deque(maxlen=MAX_POINTS),
    'diff_div_by_eight': deque(maxlen=MAX_POINTS),
}

# Read from stdin thread
def stream_reader():
    cur_time          = None
    prev_idle         = None
    diff_div_by_eight = None
    updated_idle      = None

    for line in sys.stdin:
        line = line.strip()
        # print(line)

        m = re.search(r'(\d+\.\d+):', line)
        if m:
            cur_time = float(m.group(1))

        if 'previous avg_idle' in line:
            prev_idle = int(line.split()[-3])
        elif 'diff' in line:
            diff_div_by_eight = int(line.split()[-2])
        elif 'updated avg_idle' in line:
            updated_idle = int(line.split()[-3])

        # Once all parts are captured, process them
        if all(x is not None for x in (cur_time, prev_idle, diff_div_by_eight, updated_idle)):
            data['timestamp'].append(cur_time)
            data['prev'].append(prev_idle)
            data['diff_div_by_eight'].append(diff_div_by_eight)
            data['updated'].append(updated_idle)
            # print(f"[{cur_time:.6f}] prev_idle: {prev_idle}, diff: {diff}, updated_idle: {updated_idle}")
            # Reset for next group
            cur_time = prev_idle = diff = updated_idle = None

# Dash app
server = Flask(__name__)
app = Dash(__name__, server=server)
app.layout = html.Div([
    html.H4("Live avg_idle plot"),
    dcc.Graph(id='live-graph'),
    dcc.Interval(id='interval', interval=1000, n_intervals=0)
])

@app.callback(Output('live-graph', 'figure'), Input('interval', 'n_intervals'))
def update_graph(n):
    df = pd.DataFrame(data)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("diff/8", "avg_idle")
    )

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['diff_div_by_eight'],
        mode='lines+markers',
        name='diff/8'),
        row=1,
        col=1
    )

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['updated'],
        mode='lines+markers',
        name='avg_idle'),
        row=2,
        col=1
    )

    # Layout
    fig.update_layout(height=900)
    fig.update_xaxes(title_text="Timestamp", row=1, col=1)
    fig.update_yaxes(title_text="diff/8", row=1, col=1)
    fig.update_xaxes(title_text="Timestamp", row=2, col=1)
    fig.update_yaxes(title_text="avg_idle", row=2, col=1)

    return fig

if __name__ == '__main__':
    threading.Thread(target=stream_reader, daemon=True).start()
    app.run(host='0.0.0.0', port=8050)
