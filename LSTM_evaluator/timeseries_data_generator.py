import yfinance as yf
import pandas as pd
import time
import pandas as pd
from datetime import datetime, date, timedelta
import os
from training_input import TrainingInput
import random
import numpy as np
import contextlib

# https://towardsdatascience.com/lstm-for-time-series-prediction-de8aeb26f2ca
# TODO: I don't think it is generating all possible combs
stocks = []
with open("stocks_to_download.txt", "r") as f:
    stocks = [i.replace("\n", "") for i in f.readlines()]

download_path = "raw_timeseries_data/"
for file in os.listdir(download_path): os.remove(os.path.join(download_path, file))




final_model_input = []
start_date = date.today()-timedelta(days=29) # starts downloading data starting from this date
end_date = date.today()

print("Downloading from %s to %s" % (start_date, end_date))

for stock in stocks:
    download_interval = pd.date_range(start=start_date, end=end_date)[::7]  # only allows download for 7 day intervals

    for i in range(0, len(download_interval) - 1):
        with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
            data = yf.download(
                tickers=stock,
                # use "period" instead of start/end
                # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
                # (optional, default is '1mo')
                period="7d",

                # fetch data by interval (including intraday if period < 60 days)
                # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                # (optional, default is '1d')
                interval="1m",

                start=download_interval[i],
                end=download_interval[i + 1],

                # download pre/post regular market hours data
                # (optional, default is False)
                prepost=False,


                # use threads for mass downloading? (True/False/Integer)
                # (optional, default is True)
                threads=True,
            )


        data_file_path = "timeseries_data/%s.csv"
        with open(data_file_path, 'a') as f:

            data.to_csv(data_file_path % stock, header=f.tell() == 0)

        timeseries_length = 30
        close_prices_7_day = data['Close'].to_numpy()
        volume_7_day = data['Volume'].to_numpy()

        # if len(close_prices_7_day) == 0:
        #     print("Found no data", stock)
        #     print(data.head())
        #     exit(0)

        max_price_7_day = max(close_prices_7_day)
        min_price_7_day = min(close_prices_7_day)

        max_volume_7_day = max(volume_7_day)
        min_volume_7_day = min(volume_7_day)

        # print("\n%s\nMax: %s Min: %s\n\n" % (stock, str(max_price_7_day), str(min_price_7_day)))
        for i in range(0, len(close_prices_7_day) - timeseries_length):
            final_model_input.append(TrainingInput(max_price_7_day, min_price_7_day, close_prices_7_day[i:i+30].tolist(), max_volume_7_day, min_volume_7_day, volume_7_day[i:i+30].tolist()))


        # print("2 Week Dataset Size:", len(model_input))
        print("Cumulative Dataset Size:", len(final_model_input), end='\r')


# shuffle input

random.shuffle(final_model_input)

print("Cumulative Dataset Size before balancing", len(final_model_input))

# balance input

input_buy = []
input_neutral = []
input_sell = []

for inputl in final_model_input:
    input_buysellneutral = TrainingInput.map(inputl.get_serialized_output())
    if input_buysellneutral == "buy":
        input_buy.append(inputl)
    elif input_buysellneutral == "neutral":
        input_neutral.append(inputl)
    else:
        input_sell.append(inputl)

class_max = min(len(input_buy), len(input_neutral), len(input_sell)) # most number of buy sell and neutral classifications in training set allowed
while len(input_buy) > class_max:
    input_buy.pop()
while len(input_sell) > class_max:
    input_sell.pop()
while len(input_neutral) > class_max:
    input_neutral.pop()

assert len(input_buy) == len(input_sell) == len(input_neutral) # asserts balanced

final_model_input = input_buy + input_sell + input_neutral

# shuffle input after balance

random.shuffle(final_model_input)



print("Training Dataset Size", len(final_model_input))


# unpack into x and y training data

train_x, train_y, val_x, val_y = [], [], [], []

val_split = 0.2

for i in range(0, len(final_model_input)):
    if i < (1 - val_split) * len(final_model_input):
        train_x.append(final_model_input[i].get_serialized_input())
        train_y.append(final_model_input[i].get_serialized_output())
    else:
        val_x.append(final_model_input[i].get_serialized_input())
        val_y.append(final_model_input[i].get_serialized_output())


save_status = input("Would you like to save? yes or no: ")
if save_status == "yes":
    np.savez("train", np.array(train_x), np.array(train_y))
    np.savez("val", np.array(val_x), np.array(val_y))


np.array(val_x), np.array(val_y)



