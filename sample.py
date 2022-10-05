import time
from datetime import datetime
import pandas as pd

# CSV to DataFrame
df = pd.read_csv('NIFTYBEES2.csv', header=None)
date_price_list: list = df.values.tolist()

# date_price_list.reverse()

BUYING_MARGIN = 0.992
SELLING_MARGIN = 1.008
UNITS = 200
equity_margin = 10000
NIFTY_BEES_LTP = 30

orders = {}
order_id = 0

for date_prices in date_price_list:
    date = date_prices[0]

    prices = [date_prices[1], date_prices[4]]
    for price in prices:
        NIFTY_BEES_CTP = price
        if NIFTY_BEES_CTP <= (NIFTY_BEES_LTP * BUYING_MARGIN):
            if UNITS * NIFTY_BEES_CTP <= equity_margin:
                equity_margin = equity_margin - (UNITS * NIFTY_BEES_CTP)

                order_id = order_id + 1
                orders[order_id] = {
                    "buy_date": date,
                    "buy_price": NIFTY_BEES_CTP,
                    "sell_price": NIFTY_BEES_CTP * SELLING_MARGIN,
                    "sold": False
                }

        for id, order in orders.items():
            if order["sold"] is False and NIFTY_BEES_CTP >= order["sell_price"]:
                equity_margin = equity_margin + (NIFTY_BEES_CTP * UNITS)

                order["sold"] = True
                order["sell_date"] = date
                orders[id] = order

        NIFTY_BEES_LTP = NIFTY_BEES_CTP

    invested = 0
    for oid, order in orders.items():
        if order["sold"] is False:
            invested = invested + NIFTY_BEES_CTP * UNITS
        if order['buy_date'] == date:
            print(order)
        if 'sell_date' in order and order['sell_date'] == date and order['sell_date'] != order['buy_date']:
            print(order)
    print(f"date: {date}, equity_margin: {equity_margin}, invested: {invested}, ctp: {NIFTY_BEES_CTP}")


print(orders)
print(equity_margin)
print(invested)


