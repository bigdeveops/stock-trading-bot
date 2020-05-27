import time
from datetime import datetime

import yfinance as yf

import portfolio_manager
import trading_constants
import yf_extender


def run_stock_pipelines(stock_database: [str]):
    for ticker_symbol in stock_database:
        if ticker_symbol not in trading_constants.blacklist:
            try:
                trend_following_confidence = trend_following(ticker_symbol)
                ema_crossover_confidence = ema_crossover(ticker_symbol)
                print("{0} price: {1} at {2}".format(ticker_symbol,
                                                     yf_extender.get_stock_info(yf.Ticker(ticker_symbol))['Close'],
                                                     datetime.now().strftime("%H:%M:%S")))
                if trend_following_confidence and ema_crossover_confidence is not None and trend_following_confidence + ema_crossover_confidence >= 0.5:
                    portfolio_manager.buy_stock(yf.Ticker(ticker_symbol))

            except IndexError:
                print("No data")


def trend_following(ticker_symbol: str):
    try:
        ticker = yf.Ticker(ticker_symbol)
        stock_info = yf_extender.get_stock_info(ticker)
        previous_2mo_high = yf_extender.previous_high(ticker, "2mo")
        if previous_2mo_high < stock_info['Close'] and (stock_info['High'] - stock_info['Close']) < 0.1:
            return 0.3
        return 0
    except IndexError:
        print("No Data")
        return None


def ema_crossover(ticker_symbol: str):
    try:
        ticker = yf.Ticker(ticker_symbol)
        stock_info = yf_extender.get_stock_info(ticker)
        stock_history = ticker.history("5d")
        ticker_ema = yf_extender.calculate_ema(ticker)
        ticker_yesterday_ema = yf_extender.calculate_yesterday_ema(ticker)

        if stock_info['Close'] - ticker_ema > trading_constants.ema_cross_threshold and \
                stock_history.iloc[len(stock_history) - 2].to_dict()['Close'] < ticker_yesterday_ema and stock_info[
            'Close'] > ticker_ema:
            return 0.5
        return 0
    except IndexError:
        return None


def evaluate_purchased_stocks():
    while True:
        for ticker_symbol in portfolio_manager.purchased:
            ticker = yf.Ticker(ticker_symbol)
            stock_info = yf_extender.get_stock_info(ticker)
            if stock_info['Close'] <= yf_extender.calculate_ema(
                    ticker):
                print("Because stock price dropped below EMA line, ")
                time.sleep(0.2)
                portfolio_manager.sell_stock(ticker)
                break
            elif yf_extender.get_high2current_price_change_percent(ticker) < -0.0025:
                print("Because high 2 current price change is large ")
                time.sleep(0.2)
                portfolio_manager.sell_stock(ticker)
                break
            time.sleep(0.2)
