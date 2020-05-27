import trading_strategies
import yf_web_scraper
from utils import multithreading, json_simplifier as json_simp

while True:
    json_simp.read_json()
    most_active_stocks = yf_web_scraper.get_active_tickers()
    print(most_active_stocks)
    multithreading.run_thread(trading_strategies.evaluate_purchased_stocks)
    multithreading.run_chunked_threads(most_active_stocks, trading_strategies.run_stock_pipelines, 30)
