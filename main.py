import os
import time
from datetime import datetime
from dotenv import load_dotenv
import requests
import hashlib
import logging
import json

logging.basicConfig(filename="log.txt", level=logging.INFO)
logging.info("logging test...")
load_dotenv()


def get_quote(var_instrument: str):
    quote_response = requests.get(url=KITE_QUOTE_ENDPOINT + var_instrument, headers=HEADERS)
    quote_response_dict = quote_response.json()
    return quote_response_dict["data"][var_instrument]["last_price"]


API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

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

REQUEST_TOKEN = input(KITE_LOGIN_ENDPOINT)

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
logging.debug(session_response)
ACCESS_TOKEN = None

if session_response_dict['status'] == "success":
    ACCESS_TOKEN = session_response_dict['data']['access_token']
else:
    logging.error("Unable to create a session.")

HEADERS['Authorization'] = f"token {API_KEY}:{ACCESS_TOKEN}"

instrument_LTP = get_quote(INSTRUMENT)

while True:
    instrument_CTP = get_quote(INSTRUMENT)
    logging.info(f"Instrument LTP: {instrument_LTP}")
    logging.info(f"Instrument CTP: {instrument_CTP}")
    if instrument_CTP <= (instrument_LTP * BUYING_MARGIN):
        margin_response = requests.get(KITE_MARGIN_ENDPOINT, headers=HEADERS)
        margin_response_dict = margin_response.json()
        equity_margin = margin_response_dict["data"]["equity"]["available"]["live_balance"]
        if UNITS * instrument_CTP <= equity_margin:
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
            if order_response_dict["status"] == "success":
                order_id = order_response_dict["data"]["order_id"]
                logging.info(f"{datetime.now()}: Order placed successfully with order_id - {order_id}")
                order_status = "OPEN"
                while order_status not in ["COMPLETE", "CANCELLED", "REJECTED"]:
                    time.sleep(2)
                    order_status_response = requests.get(url=KITE_ORDER_ENDPOINT + f"/{order_id}",
                                                         headers=HEADERS)
                    order_status_response_dict = order_status_response.json()
                    order_status = order_status_response_dict["data"][-1]["status"]
                    if order_status == "COMPLETE":
                        instrument_CTP = order_status_response_dict["data"][-1]["average_price"]
                        quantity = order_status_response_dict["data"][-1]["filled_quantity"]
                        logging.info(f"{datetime.now()}: Order status set to {order_status} for order_id - {order_id} "
                                     f"at price {instrument_CTP}")
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
                        trigger_response = requests.post(url=KITE_GTT_ENDPOINT, headers=HEADERS, data=data)
                        trigger_response_dict = trigger_response.json()
                        if trigger_response_dict["status"] == "success":
                            trigger_id = trigger_response_dict["data"]["trigger_id"]
                            logging.info(f"{datetime.now()}: GTT created with trigger_id - {trigger_id} "
                                         f"for order_id - {order_id} at price {instrument_CTP * SELLING_MARGIN}")
                        else:
                            logging.error(f"{datetime.now()}: Failed to create GTT for order_id - {order_id}")
                    else:
                        logging.error(f"{datetime.now()}: Order status set to {order_status} for order_id - {order_id}")
                        if order_status in ["CANCELLED", "REJECTED"]:
                            break
            else:
                logging.error(f"{datetime.now()}: Order placement failed for price {instrument_CTP * BUYING_MARGIN}")
                logging.error(order_response_dict['message'])
        else:
            logging.error(f"{datetime.now()}: Margin available: {equity_margin} is less than "
                          f"amount needed {UNITS * instrument_CTP}.")

    instrument_LTP = instrument_CTP
    time.sleep(100)
