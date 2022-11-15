from csv import writer
import pandas as pd

file_name = input("Input File Name")

with open(f'simulator/output/{file_name}_day_wise.csv', 'w') as file_object:
    writer_object = writer(file_object)
    writer_object.writerow(['Date', 'Cash Available', 'Cash Invested', 'Open', 'High', 'Low', 'Close'])

with open(f'simulator/output/{file_name}_order_wise.csv', 'w') as file_object:
    writer_object = writer(file_object)
    writer_object.writerow(['OrderID', 'Buy Date', 'Buy Price', 'Sell Date', 'Sell Price'])

# CSV to DataFrame
df = pd.read_csv(f'simulator/Input/{file_name}.csv', header=None)
date_price_list: list = df.values.tolist()

# date_price_list.reverse()

BUYING_MARGIN = 0.99
SELLING_MARGIN = 1.01
equity_margin = 100000
NIFTY_BEES_LTP = date_price_list[0][1]
NIFTY_BEES_CTP = date_price_list[0][1]
UNITS = round(equity_margin/(NIFTY_BEES_CTP * 2))

orders = {}
order_id = 0

for date_prices in date_price_list:
    date = date_prices[0]
    prices = date_prices[1:5]
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
                # Update LTP on Buy
                NIFTY_BEES_LTP = NIFTY_BEES_CTP

        for o_id, order in orders.items():
            if order["sold"] is False and NIFTY_BEES_CTP >= order["sell_price"]:
                equity_margin = equity_margin + (order["sell_price"] * UNITS)

                order["sold"] = True
                order["sell_date"] = date
                orders[o_id] = order

        # Update LTP on Open or Close.
        if price == date_prices[1] or price == date_prices[4]:
            NIFTY_BEES_LTP = price

    invested = 0
    for oid, order in orders.items():
        if order["sold"] is False:
            invested = invested + NIFTY_BEES_CTP * UNITS
        # if order['buy_date'] == date:
        #     print(f"OrderId: {oid} Order Details: {order}")
        # if 'sell_date' in order and order['sell_date'] == date and order['sell_date'] != order['buy_date']:
        #     print(f"OrderId: {oid} Order Details: {order}")

    with open(f'simulator/output/{file_name}_day_wise.csv', 'a') as file_object:
        writer_object = writer(file_object)
        writer_object.writerow([date, equity_margin, invested, *date_prices[1:5]])


for oid, order in orders.items():
    with open(f'simulator/output/{file_name}_order_wise.csv', 'a') as file_object:
        writer_object = writer(file_object)
        if order['sold']:
            writer_object.writerow(
                [oid, order['buy_date'], order['buy_price'], order['sell_date'], order['sell_price']])
        else:
            writer_object.writerow(
                [oid, order['buy_date'], order['buy_price'], "na", order['sell_price']])


