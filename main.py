import hashlib
from deta import App, Deta
from fastapi import FastAPI
import requests
import os
import json
import time
import logging

deta = Deta(os.getenv('DETA_PROJECT_KEY'))
app = App(FastAPI())
logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')

# Creating an object
logger = logging.getLogger()
# Setting the threshold of logger to INFO
logger.setLevel(logging.INFO)


API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
EXCHANGE = os.getenv('EXCHANGE')
TRADING_SYMBOL = os.getenv('TRADING_SYMBOL')
INSTRUMENT = f"{EXCHANGE}:{TRADING_SYMBOL}"
BUYING_MARGIN = float(os.getenv('BUYING_MARGIN'))
SELLING_MARGIN = float(os.getenv('SELLING_MARGIN'))
UNITS = int(os.getenv('UNITS'))
KITE_BASE_URL = "https://api.kite.trade"
KITE_LOGIN_ENDPOINT = f"https://kite.zerodha.com/connect/login?v=3&api_key={API_KEY}"
KITE_SESSION_ENDPOINT = f"{KITE_BASE_URL}/session/token"
KITE_USER_PROFILE_ENDPOINT = f"{KITE_BASE_URL}/user/profile"
KITE_MARGIN_ENDPOINT = f"{KITE_BASE_URL}/user/margins"
KITE_QUOTE_ENDPOINT = f"{KITE_BASE_URL}/quote?i="
KITE_ORDER_ENDPOINT = f"{KITE_BASE_URL}/orders"
KITE_GTT_ENDPOINT = f"{KITE_BASE_URL}/gtt/triggers"


tokens_db = deta.Base("tokens")
ltp_db = deta.Base("ltp")
orders_db = deta.Base("orders")
# "Authorization": f"token {API_KEY}:{ACCESS_TOKEN}"


@app.get("/")
def create_session(request_token: str):

    checksum = API_KEY + request_token + API_SECRET
    sha_checksum = hashlib.sha256(checksum.encode())
    # data = f"api_key={API_KEY}&request_token={REQUEST_TOKEN}&checksum={SHA_CHECKSUM}"
    session_data = {
        'api_key': API_KEY,
        'request_token': request_token,
        'checksum': sha_checksum.hexdigest()
    }
    headers = {
        "X-Kite-Version": "3"
    }
    session_response = requests.post(url=KITE_SESSION_ENDPOINT, headers=headers, data=session_data)
    session_response_dict = session_response.json()
    if session_response.status_code == 200:
        access_token = session_response_dict['data']['access_token']
        token_item = {"key": "ACCESS_TOKEN", "value": access_token}
        tokens_db.put(token_item)
        logger.info("Session created successfully.")
        instrument_ltp = get_quote(INSTRUMENT)
        return {
            "status": "success",
            "ltp": f"{instrument_ltp}"
        }

    else:
        logger.info(session_response_dict)
        logger.info("Error in creating a session.")


def get_quote(var_instrument: str):
    access_token = tokens_db.get("ACCESS_TOKEN")['value']
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {API_KEY}:{access_token}"
    }
    quote_response = requests.get(url=KITE_QUOTE_ENDPOINT + var_instrument, headers=headers)
    logger.info(headers)
    try:
        quote_response_dict = quote_response.json()
        instrument_ltp = quote_response_dict["data"][var_instrument]["last_price"]
        ltp_item = {"key": f"{INSTRUMENT}", "value": instrument_ltp}
        ltp_db.put(ltp_item)
        return instrument_ltp
    except Exception as e:
        logger.info(headers)
        logger.error("Error occurred", exc_info=e)


@app.lib.run()
@app.lib.cron()
def cron_job(event):
    access_token = tokens_db.get("ACCESS_TOKEN")['value']
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {API_KEY}:{access_token}"
    }
    instrument_ltp = ltp_db.get(INSTRUMENT)['value']
    instrument_ctp = get_quote(INSTRUMENT)
    logger.info(f"{INSTRUMENT} LTP={instrument_ltp}")
    logger.info(f"{INSTRUMENT} CTP={instrument_ctp}")
    if instrument_ctp <= (instrument_ltp * BUYING_MARGIN):
        logger.info(f"Trying to place an order as CTP ({instrument_ctp}) < LTP {instrument_ltp}")
        margin_response = requests.get(KITE_MARGIN_ENDPOINT, headers=headers)
        margin_response_dict = margin_response.json()
        equity_margin = None
        if margin_response.status_code == 200:
            equity_margin = margin_response_dict["data"]["equity"]["available"]["live_balance"]
            logger.info(f"Got margin as {equity_margin}")
        else:
            logger.info(margin_response_dict)
            logger.info("Error in getting the margin.")
        if equity_margin is not None and UNITS * instrument_ctp <= equity_margin:
            data = {
                "tradingsymbol": TRADING_SYMBOL,
                "exchange": EXCHANGE,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "quantity": UNITS,
                "product": "CNC",
                "validity": "TTL",
                "validity_ttl": 1,
                "price": instrument_ctp
            }
            order_response = requests.post(url=KITE_ORDER_ENDPOINT + "/regular", headers=headers, data=data)
            order_response_dict = order_response.json()

            if order_response.status_code == 200:
                order_id = order_response_dict["data"]["order_id"]
                logger.info(f"Order placed successfully with order_id - {order_id}")
                order_status = "OPEN"
                while order_status not in ["COMPLETE", "CANCELLED", "REJECTED"]:
                    time.sleep(2)
                    order_status_response = requests.get(url=KITE_ORDER_ENDPOINT + f"/{order_id}",
                                                         headers=headers)
                    order_status_response_dict = order_status_response.json()
                    if order_status_response.status_code == 200:
                        order_status = order_status_response_dict["data"][-1]["status"]
                        if order_status == "COMPLETE":
                            instrument_ctp = order_status_response_dict["data"][-1]["average_price"]
                            quantity = order_status_response_dict["data"][-1]["filled_quantity"]
                            data = {
                                "type": "single",
                                "condition": json.dumps({
                                    "exchange": EXCHANGE,
                                    "tradingsymbol": TRADING_SYMBOL,
                                    "trigger_values": [round(instrument_ctp * SELLING_MARGIN, 2)],
                                    "last_price": instrument_ctp
                                }),
                                "orders": json.dumps([
                                    {
                                        "exchange": EXCHANGE,
                                        "tradingsymbol": TRADING_SYMBOL,
                                        "transaction_type": "SELL",
                                        "quantity": quantity,
                                        "order_type": "LIMIT",
                                        "product": "CNC",
                                        "price": round(instrument_ctp * SELLING_MARGIN, 2)
                                    }
                                ])
                            }
                            logger.info(f"Trying to place GTT for order_id - {order_id}")
                            trigger_response = requests.post(url=KITE_GTT_ENDPOINT, headers=headers, data=data)
                            trigger_response_dict = trigger_response.json()
                            if trigger_response.status_code == 200:
                                trigger_id = trigger_response_dict["data"]["trigger_id"]
                                logger.info(f"GTT created with trigger_id - {trigger_id} for order_id - {order_id}")
                                order_item = {"key": f"{order_id}", "value": f"{trigger_id}"}
                                orders_db.put(order_item)
                            else:
                                logger.info(trigger_response_dict)
                                logger.info(f"Error in creating Trigger for order_id - {order_id}")
                                logger.info(f"order_id={order_id}|trigger_id=None")
                        else:
                            logger.info(f"Order status set to {order_status} for order_id - {order_id}")
                    else:
                        logger.info(order_status_response_dict)
                        logger.info(f"Error in getting status for order_id - {order_id}")
            else:
                logger.info(order_response_dict)
                logger.info(f"Error in placing order for price {instrument_ctp * BUYING_MARGIN}")
        else:
            logger.info(f"Margin available: {equity_margin} is less than amount needed {UNITS * instrument_ctp}.")
    return {
        "status": "success",
        "ltp": f"{instrument_ltp}"
    }
