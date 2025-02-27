# Coleta de dados do mercado e redes sociais
import ccxt.async_support as ccxt
import tweepy
import pandas as pd

class DataFetcher:
    def __init__(self, exchange):
        """Inicializa o coletor de dados."""
        self.exchange = exchange
        self.twitter_client = tweepy.Client(bearer_token="SEU_TOKEN_AQUI")  # Substitua pelo seu token

    async def get_ohlcv(self, symbol, timeframe):
        """Busca dados OHLCV da exchange."""
        ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df

    def get_sentiment(self, keyword):
        """Analisa o sentimento no Twitter."""
        tweets = self.twitter_client.search_recent_tweets(query=keyword, max_results=100)
        sentiment = sum(1 if "bull" in t.text.lower() else -1 if "bear" in t.text.lower() else 0 for t in tweets.data)
        return sentiment