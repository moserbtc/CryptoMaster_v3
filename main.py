# Arquivo principal para executar o robô
from core.trader import CryptoMaster
import yaml
import schedule
from reports.report import generate_daily_report

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

trader = CryptoMaster(config)
schedule.every().day.at("22:30").do(generate_daily_report)

import asyncio
asyncio.run(trader.run())