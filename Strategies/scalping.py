import ccxt.async_support as ccxt
import asyncio
import numpy as np
import pandas as pd
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from typing import Optional, Dict
import logging
from functools import lru_cache
from data.fetcher import DataFetcher

class ScalpingStrategy:
    """Estratégia de scalping para trading de criptomoedas com base em médias móveis e volume.
    
    Utiliza análise técnica para gerar sinais de compra/venda e gerencia posições com risco controlado.
    """
    def __init__(
        self,
        exchange: ccxt.Exchange,
        config: Dict[str, any],
        data_fetcher: DataFetcher,
        max_retries: int = 3
    ):
        """Inicializa a estratégia de scalping.
        
        Args:
            exchange (ccxt.Exchange): Conexão com a exchange via CCXT.
            config (Dict): Configurações do trading (timeframe, risco, etc.).
            data_fetcher (DataFetcher): Objeto para coletar dados de mercado.
            max_retries (int): Número máximo de retentativas para requisições.
        """
        self.exchange = exchange
        self.config = config
        self.timeframe = config['data']['timeframe_scalp']
        self.risk = config['trading']['risk_per_trade']
        self.data_fetcher = data_fetcher
        self.max_retries = max_retries
        self.logger = logging.getLogger("ScalpingStrategy")
        self.current_position: Optional[float] = None  # Tamanho da posição aberta

    async def execute(self, capital: float) -> None:
        """Executa a estratégia de scalping, gerenciando entradas e saídas com base em sinais técnicos.
        
        Args:
            capital (float): Capital disponível para trading.
        
        Raises:
            ccxt.NetworkError: Erro de conexão com a exchange.
            ccxt.ExchangeError: Erro específico da exchange.
        """
        try:
            df = await self._fetch_ohlcv_with_retry('BTC/USDT')
            if df.empty:
                self.logger.warning("Dados OHLCV vazios. Abortando execução.")
                return

            signal = self._generate_trading_signal(df)
            if signal == 'BUY' and not self.current_position:
                await self._enter_long_position(df, capital)
            elif signal == 'SELL' and self.current_position:
                await self._exit_position(capital)

        except ccxt.NetworkError as e:
            self.logger.error(f"Erro de rede: {str(e)}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Erro da exchange: {str(e)}")
        except Exception as e:
            self.logger.error(f"Erro inesperado: {str(e)}", exc_info=True)

    @lru_cache(maxsize=10)  # Cache para evitar recálculos frequentes
    async def _fetch_ohlcv_with_retry(self, symbol: str) -> pd.DataFrame:
        """Busca dados OHLCV com retentativas para lidar com falhas temporárias.
        
        Args:
            symbol (str): Par de trading (ex.: 'BTC/USDT').
        
        Returns:
            pd.DataFrame: Dados OHLCV ou DataFrame vazio em caso de falha.
        """
        for attempt in range(self.max_retries):
            try:
                df = await self.data_fetcher.get_ohlcv(symbol, self.timeframe)
                if not df.empty:
                    return df
                self.logger.warning(f"Tentativa {attempt + 1}/{self.max_retries} falhou. Aguardando 5s...")
                await asyncio.sleep(5 + np.random.uniform(0, 2))  # Adiciona aleatoriedade
        return pd.DataFrame()

    def _generate_trading_signal(self, df: pd.DataFrame) -> str:
        """Gera sinais de compra/venda com confirmação de volume e RSI.
        
        Args:
            df (pd.DataFrame): DataFrame com dados OHLCV.
        
        Returns:
            str: 'BUY', 'SELL' ou 'HOLD' com base em indicadores técnicos.
        """
        # Cálculo eficiente com numpy para médias móveis
        close = df['close'].values
        volume = df['volume'].values

        sma_short = np.convolve(close, np.ones(5)/5, mode='valid')[-1]
        sma_long = np.convolve(close, np.ones(20)/20, mode='valid')[-1]
        volume_ma = np.convolve(volume, np.ones(5)/5, mode='valid')[-1]
        last_volume = volume[-1]

        # RSI para evitar trades em sobrecompra/venda
        rsi = RSIIndicator(close=close, window=14).rsi()[-1] if len(close) >= 14 else 50

        if (
            sma_short > sma_long and
            (len(close) < 2 or np.convolve(close[-2:], np.ones(2)/2, mode='valid')[0] <= sma_long) and
            last_volume > volume_ma * 1.2 and  # Volume 20% acima da média
            rsi < 70  # Evita sobrecompra
        ):
            return 'BUY'
        elif (
            sma_short < sma_long and
            (len(close) < 2 or np.convolve(close[-2:], np.ones(2)/2, mode='valid')[0] >= sma_long)
        ):
            return 'SELL'
        return 'HOLD'

    async def _enter_long_position(self, df: pd.DataFrame, capital: float) -> None:
        """Abre uma posição long com gerenciamento de risco dinâmico.
        
        Args:
            df (pd.DataFrame): DataFrame com dados OHLCV.
            capital (float): Capital disponível para trading.
        """
        current_price = df['close'].iloc[-1]
        position_size = (capital * self.risk) / current_price

        try:
            order = await self.exchange.create_market_buy_order(
                symbol='BTC/USDT',
                amount=position_size
            )
            self.current_position = position_size
            self.logger.info(f"Ordem de COMPRA executada: {order}")
            await self._log_trade_to_db(order, 'BUY', current_price, capital)
        except Exception as e:
            self.logger.error(f"Falha ao executar ordem: {str(e)}")

    async def _exit_position(self, capital: float) -> None:
        """Fecha a posição atual com ordem de mercado.
        
        Args:
            capital (float): Capital atual para atualizar o log.
        """
        try:
            order = await self.exchange.create_market_sell_order(
                symbol='BTC/USDT',
                amount=abs(self.current_position)
            )
            self.logger.info(f"Ordem de VENDA executada: {order}")
            await self._log_trade_to_db(order, 'SELL', order['price'], capital)
            self.current_position = None
        except Exception as e:
            self.logger.error(f"Falha ao fechar posição: {str(e)}")

    async def _log_trade_to_db(self, order: Dict, action: str, price: float, capital: float) -> None:
        """Registra trade no banco de dados SQLite de forma assíncrona.
        
        Args:
            order (Dict): Dados da ordem executada.
            action (str): Ação realizada ('BUY' ou 'SELL').
            price (float): Preço da execução.
            capital (float): Capital atual após o trade.
        """
        from utils.database import log_trade  # Função auxiliar para SQLite
        trade_data = {
            'timestamp': pd.Timestamp.now(),
            'symbol': order['symbol'],
            'action': action,
            'size': order['amount'],
            'price': price,
            'capital': capital
        }
        await log_trade(trade_data)