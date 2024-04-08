import logging
from decimal import Decimal as D
import gate_api
from gate_api.exceptions import ApiException
from gate_api import ApiClient, Configuration, Order, SpotApi
import json
import threading
import tzlocal
from datetime import datetime
import time

logger = logging.getLogger(__name__)

def convert_unix_to_readable(unix_timestamp):
    local_tz = tzlocal.get_localzone() 
    local_time = datetime.fromtimestamp(int(unix_timestamp), local_tz)
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

def spot_sell(spot_api, currency_pair, account_name, ignore_coins):
    try:
        base_currency = currency_pair.split("_")[0]
        available = D(spot_api.list_spot_accounts(currency=base_currency)[0].available)
        if available > D(spot_api.get_currency_pair(currency_pair).min_base_amount):
            order = Order(amount=str(available), currency_pair=currency_pair, side='sell', type='market', time_in_force='ioc')
            created_order = spot_api.create_order(order)
            print(f"Account {account_name} sold {base_currency}: Total {spot_api.get_order(created_order.id, currency_pair).filled_total} USDT at {convert_unix_to_readable(spot_api.get_order(created_order.id, currency_pair).update_time)}")
        else:
            print(f"{currency_pair} available lower than {spot_api.get_currency_pair(currency_pair).min_base_amount}")
    except ApiException as e:
        if "is too small" in str(e):
            ignore_coins.add(base_currency)
            print(f"Error in selling {currency_pair} for account {account_name}: {e}. Added to ignore list.")
        else:
            logger.error(f"Error in selling {currency_pair} for account {account_name}: {e}")

def check_and_sell(spot_api, account_name, ignore_coins):
    #print(f"Checking account: {account_name}")

    try:
        current_pairs = {pair.id for pair in spot_api.list_currency_pairs()}

        for balance in spot_api.list_spot_accounts():
            currency = balance.currency.upper()
            if currency not in ignore_coins and float(balance.available) > 0:
                pair_id = f"{currency}_USDT"
                if pair_id in current_pairs:
                    try:
                        pair_info = spot_api.get_currency_pair(pair_id)
                        if pair_info.trade_status == 'tradable' and float(balance.available) >= float(pair_info.min_base_amount):
                            spot_sell(spot_api, pair_id, account_name, ignore_coins)
                    except ApiException as e:
                        print(f"Error with {currency} for account {account_name}: {e}")

    except ApiException as e:
        print(f"API Exception for account {account_name}: {e}")

def account_monitor(account):
    configuration = Configuration(key=account['API_KEY'], secret=account['API_SECRET'])
    api_client = ApiClient(configuration)
    spot_api = SpotApi(api_client)
    account_name = account['ACCOUNT_NAME']
    ignore_coins = set(['GT', 'BTC', 'ETH', 'USDT'])

    while True:
        check_and_sell(spot_api, account_name, ignore_coins)
        time.sleep(5)

if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        accounts = json.load(config_file)

    threads = []
    for account in accounts:
        thread = threading.Thread(target=account_monitor, args=(account,), daemon=True)
        thread.start()
        threads.append(thread)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted, exiting...")