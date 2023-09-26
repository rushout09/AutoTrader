import math
from csv import writer
import pandas as pd

file_names = ["JUNIORBEES"]

for file_name in file_names:
    output_dir_day_wise = f'simulator/output2/{file_name}_day_wise_only.csv'
    output_dir_order_wise = f'simulator/output2/{file_name}_order_wise_only.csv'

    with open(output_dir_day_wise, 'w') as file_object:
        writer_object = writer(file_object)
        writer_object.writerow(['Date', 'Cash Available', 'Cash Invested', 'Open', 'High', 'Low', 'Close'])

    with open(output_dir_order_wise, 'w') as file_object:
        writer_object = writer(file_object)
        writer_object.writerow(['OrderID', 'Buy Date', 'Buy Price', 'Sell Date', 'Sell Price'])

    # CSV to DataFrame
    df = pd.read_csv(f'simulator/Input/{file_name}.csv', header=None)
    date_price_list: list = df.values.tolist()

    # date_price_list.reverse()

    BUYING_MARGIN = 0.99
    SELLING_MARGIN = 1.05
    equity_margin = 100000
    NIFTY_BEES_LTP = date_price_list[0][1]
    NIFTY_BEES_CTP = date_price_list[0][1]

    orders = {}
    order_id = 0
    prev_date = None
    for date_prices in date_price_list:
        UNITS = round(equity_margin / NIFTY_BEES_CTP)
        date = date_prices[0]
        prices = [date_prices[1], date_prices[4]]
        if math.isnan(prices[0]):
            continue
        for price in prices:
            NIFTY_BEES_CTP = price
            if NIFTY_BEES_CTP <= (NIFTY_BEES_LTP * BUYING_MARGIN):
                if UNITS > 0 and UNITS * NIFTY_BEES_CTP <= equity_margin:
                    equity_margin = equity_margin - (UNITS * NIFTY_BEES_CTP)

                    order_id = order_id + 1
                    orders[order_id] = {
                        "buy_date": date,
                        "buy_price": NIFTY_BEES_CTP,
                        "sell_price": NIFTY_BEES_CTP * SELLING_MARGIN,
                        "units": UNITS,
                        "profit": 0,
                        "sold": False
                    }

            for o_id, order in orders.items():
                if order["sold"] is False and NIFTY_BEES_CTP >= order["sell_price"]:
                    TURNOVER = (order["sell_price"] * order["units"]) + (order["buy_price"] * order["units"])
                    STT = int(TURNOVER * 0.001)
                    ETC = int(TURNOVER * 0.000035)
                    DPC = 16
                    SEBI = int(TURNOVER * 0.00001)
                    STAMP = int(TURNOVER * 0.00015)
                    GST = 0.18 * (SEBI + ETC)
                    TOTAL = STT + ETC + DPC + SEBI + STAMP + GST
                    equity_margin = equity_margin + (order["sell_price"] * order["units"]) - TOTAL
                    order["sold"] = True
                    order["sell_date"] = date
                    order["profit"] = (order["units"] * (order["sell_price"] - order["buy_price"])) - TOTAL
                    orders[o_id] = order

            # Update LTP on Open or Close.
            # if price == date_prices[4]:
            NIFTY_BEES_LTP = price

        invested = 0
        for oid, order in orders.items():
            if order["sold"] is False:
                invested = invested + NIFTY_BEES_CTP * order["units"]

        with open(output_dir_day_wise, 'a') as file_object:
            writer_object = writer(file_object)
            # if not prev_date or prev_date != date[:4]:
            writer_object.writerow([date, equity_margin, invested, *date_prices[1:5]])
            prev_date = date[:4]

    for oid, order in orders.items():
        with open(output_dir_order_wise, 'a') as file_object:
            writer_object = writer(file_object)
            if order['sold']:
                writer_object.writerow(
                    [oid, order['buy_date'], order['buy_price'], order['sell_date'], order['sell_price'],
                     order["units"], order["profit"]])
            else:
                writer_object.writerow(
                    [oid, order['buy_date'], order['buy_price'], "na", order['sell_price'], order["units"]])


# Volatility matters. Best return comes in juniorbees, followed by niftybees, followed by goldbees.
# invest with 2% profit. Profit is significantly more.
# Do not Update LTP on Buy. Update LTP on open or close.
