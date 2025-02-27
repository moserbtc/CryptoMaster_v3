# Geração de relatórios diários
import pandas as pd
from datetime import datetime

def generate_daily_report():
    """Gera um relatório diário com base nos trades registrados."""
    df = pd.read_sql("SELECT * FROM trades", "sqlite:///cm3.db")
    profit = df['profit'].sum()
    with open(f"reports/report_{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
        f.write(f"Lucro Total: ${profit:.2f}\n")
        f.write(f"Trades Executados: {len(df)}\n")