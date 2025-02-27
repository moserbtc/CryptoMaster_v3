# Estratégia de swing trading
class SwingStrategy:
    def __init__(self, exchange, config):
        """Inicializa a estratégia de swing."""
        self.exchange = exchange
        self.timeframe = config['data']['timeframe_swing']
        self.risk = config['trading']['risk_per_trade']

    async def execute(self, capital):
        """Executa trades de swing com base em análise técnica e sentimento."""
        from data.fetcher import DataFetcher
        df = await DataFetcher(self.exchange).get_ohlcv('ETH/USDT', self.timeframe)
        sentiment = DataFetcher(self.exchange).get_sentiment('ETH')

        if df['close'].iloc[-1] > df['close'].rolling(50).mean().iloc[-1] and sentiment > 10:
            size = (capital * self.risk) / df['close'].iloc[-1]
            await self.exchange.create_market_buy_order('ETH/USDT', size)
            print(f"Compra de {size} ETH/USDT executada!")