# Dashboard em tempo real com Dash
from dash import Dash, dcc, html, Output, Input
import plotly.express as px
import pandas as pd

app = Dash(__name__)

def update_dashboard():
    """Atualiza o gráfico com dados do banco de dados."""
    df = pd.read_sql("SELECT * FROM trades", "sqlite:///cm3.db")
    fig = px.line(df, x="timestamp", y="capital", title="Capital ao Longo do Tempo")
    return fig

app.layout = html.Div([
    dcc.Graph(id='live-graph'),
    dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0)  # Atualiza a cada 1s
])

@app.callback(Output('live-graph', 'figure'), Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    return update_dashboard()

if __name__ == '__main__':
    app.run_server(debug=True)