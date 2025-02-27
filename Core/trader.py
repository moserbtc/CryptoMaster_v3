# Core do robô de trading
import ccxt.async_support as ccxt
import asyncio
import logging
from strategies.scalping import ScalpingStrategy
from strategies.swing import SwingStrategy
from data.fetcher import DataFetcher

class CryptoMaster:
    def __init__(self, config):
        """Inicializa o robô com configurações e conexão com a exchange."""
        self.config = config
        self.exchange = ccxt.binance({
            'apiKey': config['exchanges']['binance']['api_key'],
            'secret': config['exchanges']['binance']['api_secret'],
            'enableRateLimit': True,
        })
        self.capital = config['trading']['initial_capital']
        self.data_fetcher = DataFetcher(self.exchange)
        self.strategies = {
            'scalping': ScalpingStrategy(self.exchange, self.config),
            'swing': SwingStrategy(self.exchange, self.config)
        }
        logging.basicConfig(filename='cm3.log', level=logging.INFO)

    async def run(self):
        """Loop principal do robô."""
        await self.exchange.load_markets()
        while True:
            await self.execute_strategies()
            await asyncio.sleep(60)  # Executa a cada 1 minuto

    async def execute_strategies(self):
        """Executa todas as estratégias configuradas."""
        for name, strategy in self.strategies.items():
            await strategy.execute(self.capital)
            logging.info(f"Estratégia {name} executada. Capital: {self.capital}")

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    trader = CryptoMaster(config)
    asyncio.run(trader.run())