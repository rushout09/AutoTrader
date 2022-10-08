import os
import time
import sys
from dotenv import load_dotenv
import requests
import hashlib
import logging
import json

load_dotenv()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    """To set up as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def get_quote(var_instrument: str):
    quote_response = requests.get(url=KITE_QUOTE_ENDPOINT + var_instrument, headers=HEADERS)
    quote_response_dict = quote_response.json()
    return quote_response_dict["data"][var_instrument]["last_price"]


main_log = setup_logger(name="main_log", log_file="logs/main.log", level=logging.INFO)
db_log = setup_logger(name="db_log", log_file="logs/db.log", level=logging.CRITICAL)

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
ACCESS_TOKEN = None

EXCHANGE = os.getenv('EXCHANGE')
TRADING_SYMBOL = os.getenv('TRADING_SYMBOL')
INSTRUMENT = f"{EXCHANGE}:{TRADING_SYMBOL}"

BUYING_MARGIN: float = float(os.getenv('BUYING_MARGIN'))
SELLING_MARGIN: float = float(os.getenv('SELLING_MARGIN'))
UNITS: int = int(os.getenv('UNITS'))

KITE_BASE_URL = "https://api.kite.trade"
KITE_LOGIN_ENDPOINT = f"https://kite.zerodha.com/connect/login?v=3&api_key={API_KEY}"
KITE_SESSION_ENDPOINT = f"{KITE_BASE_URL}/session/token"
KITE_USER_PROFILE_ENDPOINT = f"{KITE_BASE_URL}/user/profile"
KITE_MARGIN_ENDPOINT = f"{KITE_BASE_URL}/user/margins"
KITE_QUOTE_ENDPOINT = f"{KITE_BASE_URL}/quote?i="
KITE_ORDER_ENDPOINT = f"{KITE_BASE_URL}/orders"
KITE_GTT_ENDPOINT = f"{KITE_BASE_URL}/gtt/triggers"

HEADERS = {
    "X-Kite-Version": "3",
}

# "Authorization": f"token {API_KEY}:{ACCESS_TOKEN}"
if len(sys.argv) > 1 and sys.argv[1] != "":
    REQUEST_TOKEN = sys.argv[1]
else:
    REQUEST_TOKEN = os.getenv('REQUEST_TOKEN')

CHECKSUM = API_KEY + REQUEST_TOKEN + API_SECRET
SHA_CHECKSUM = hashlib.sha256(CHECKSUM.encode())

# data = f"api_key={API_KEY}&request_token={REQUEST_TOKEN}&checksum={SHA_CHECKSUM}"

data = {
    'api_key': API_KEY,
    'request_token': REQUEST_TOKEN,
    'checksum': SHA_CHECKSUM.hexdigest()
}

session_response = requests.post(url=KITE_SESSION_ENDPOINT, headers=HEADERS, data=data)
session_response_dict = session_response.json()
if session_response.status_code == 200:
    ACCESS_TOKEN = session_response_dict['data']['access_token']
    main_log.info("Session created successfully.")
else:
    main_log.debug(session_response_dict)
    main_log.error("Error in creating a session.")
    exit(code=1)

HEADERS['Authorization'] = f"token {API_KEY}:{ACCESS_TOKEN}"

instrument_LTP = get_quote(INSTRUMENT)

while True:
    instrument_CTP = get_quote(INSTRUMENT)
    main_log.info(f"{INSTRUMENT} LTP={instrument_LTP}")
    main_log.info(f"{INSTRUMENT} CTP={instrument_CTP}")
    if instrument_CTP <= (instrument_LTP * BUYING_MARGIN):
        main_log.info(f"Trying to place an order as CTP ({instrument_CTP}) < LTP {instrument_LTP}")
        margin_response = requests.get(KITE_MARGIN_ENDPOINT, headers=HEADERS)
        margin_response_dict = margin_response.json()
        equity_margin = None
        if margin_response.status_code == 200:
            equity_margin = margin_response_dict["data"]["equity"]["available"]["live_balance"]
            main_log.info(f"Got margin as {equity_margin}")
        else:
            main_log.debug(margin_response_dict)
            main_log.error("Error in getting the margin.")
        if equity_margin is not None and UNITS * instrument_CTP <= equity_margin:
            data = {
                "tradingsymbol": TRADING_SYMBOL,
                "exchange": EXCHANGE,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "quantity": UNITS,
                "product": "CNC",
                "validity": "TTL",
                "validity_ttl": 1,
                "price": instrument_CTP
            }
            order_response = requests.post(url=KITE_ORDER_ENDPOINT + "/regular", headers=HEADERS, data=data)
            order_response_dict = order_response.json()

            if order_response.status_code == 200:
                order_id = order_response_dict["data"]["order_id"]
                main_log.info(f"Order placed successfully with order_id - {order_id}")
                order_status = "OPEN"
                while order_status not in ["COMPLETE", "CANCELLED", "REJECTED"]:
                    time.sleep(2)
                    order_status_response = requests.get(url=KITE_ORDER_ENDPOINT + f"/{order_id}",
                                                         headers=HEADERS)
                    order_status_response_dict = order_status_response.json()
                    if order_status_response.status_code == 200:
                        order_status = order_status_response_dict["data"][-1]["status"]
                        if order_status == "COMPLETE":
                            instrument_CTP = order_status_response_dict["data"][-1]["average_price"]
                            quantity = order_status_response_dict["data"][-1]["filled_quantity"]
                            data = {
                                "type": "single",
                                "condition": json.dumps({
                                    "exchange": EXCHANGE,
                                    "tradingsymbol": TRADING_SYMBOL,
                                    "trigger_values": [round(instrument_CTP * SELLING_MARGIN, 2)],
                                    "last_price": instrument_CTP
                                }),
                                "orders": json.dumps([
                                    {
                                        "exchange": EXCHANGE,
                                        "tradingsymbol": TRADING_SYMBOL,
                                        "transaction_type": "SELL",
                                        "quantity": quantity,
                                        "order_type": "LIMIT",
                                        "product": "CNC",
                                        "price": round(instrument_CTP * SELLING_MARGIN, 2)
                                    }
                                ])
                            }
                            main_log.info(f"Trying to place GTT for order_id - {order_id}")
                            trigger_response = requests.post(url=KITE_GTT_ENDPOINT, headers=HEADERS, data=data)
                            trigger_response_dict = trigger_response.json()
                            if trigger_response.status_code == 200:
                                trigger_id = trigger_response_dict["data"]["trigger_id"]
                                main_log.info(f"GTT created with trigger_id - {trigger_id} for order_id - {order_id}")
                                db_log.info(f"order_id={order_id}|trigger_id={trigger_id}")
                            else:
                                main_log.debug(trigger_response_dict)
                                main_log.error(f"Error in creating Trigger for order_id - {order_id}")
                                db_log.info(f"order_id={order_id}|trigger_id=None")
                        else:
                            main_log.info(f"Order status set to {order_status} for order_id - {order_id}")
                    else:
                        main_log.debug(order_status_response_dict)
                        main_log.error(f"Error in getting status for order_id - {order_id}")
            else:
                main_log.debug(order_response_dict)
                main_log.error(f"Error in placing order for price {instrument_CTP * BUYING_MARGIN}")
        else:
            main_log.error(f"Margin available: {equity_margin} is less than amount needed {UNITS * instrument_CTP}.")

    instrument_LTP = instrument_CTP
    # run every 3 hours. (9:20am, 12:20pm, 3:20pm, 6:20pm, 9:20pm, 12:20am, 3:20am, 6:20am)
    time.sleep(10800)
