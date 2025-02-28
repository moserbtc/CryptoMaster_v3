# Estratégia de scalping
from ta.trend import SMAIndicator
import numpy as np

class ScalpingStrategy:
    def __init__(self, exchange, config):
        """Inicializa a estratégia de scalping."""
        self.exchange = exchange
        self.timeframe = config['data']['timeframe_scalp']
        self.risk = config['trading']['risk_per_trade']

    async def execute(self, capital):
        """Executa trades de scalping com base em médias móveis."""
        from data.fetcher import DataFetcher
        df = await DataFetcher(self.exchange).get_ohlcv('BTC/USDT', self.timeframe)
        sma_short = SMAIndicator(df['close'], window=5).sma_indicator()
        sma_long = SMAIndicator(df['close'], window=20).sma_indicator()

        if sma_short.iloc[-1] > sma_long.iloc[-1] and sma_short.iloc[-2] <= sma_long.iloc[-2]:
            size = (capital * self.risk) / df['close'].iloc[-1]
            await self.exchange.create_market_buy_order('BTC/USDT', size)
            print(f"Compra de {size} BTC/USDT executada!")