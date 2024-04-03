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

def is_currency_pair_tradable(spot_api,currency_pair):
    try:
        return spot_api.get_currency_pair(currency_pair).trade_status == 'tradable'
    except ApiException as e:
        logger.error(f"Error fetching info for {currency_pair}: {e}")
        return False

def spot_sell(spot_api,currency_pair):
    try:
        base_currency = currency_pair.split("_")[0]
        available = D(spot_api.list_spot_accounts(currency=base_currency)[0].available)
        if available > D(spot_api.get_currency_pair(currency_pair).min_base_amount):
            order = Order(amount=str(available), currency_pair=currency_pair, side='sell', type='market', time_in_force='ioc')
            created_order = spot_api.create_order(order)
            print(f"Sold {base_currency}: Total {spot_api.get_order(created_order.id, currency_pair).filled_total} USDT at {convert_unix_to_readable(spot_api.get_order(created_order.id, currency_pair).update_time)}")
        else:
            print(f"{currency_pair} available low than {spot_api.get_currency_pair(currency_pair).min_base_amount}")
    except ApiException as e:
        logger.error(f"Error in selling {currency_pair}: {e}")

def check_and_sell(spot_api):
    non_tradeable_initially = set()
    try:
        current_pairs = {pair.id for pair in spot_api.list_currency_pairs()}
        print("Searching for tradable pairs...")

        if not non_tradeable_initially:  # 初始搜寻
            for balance in spot_api.list_spot_accounts():
                currency = balance.currency.upper()
                if currency != 'USDT':
                    pair_id = f"{currency}_USDT"
                    if not is_currency_pair_tradable(spot_api,pair_id):
                        non_tradeable_initially.add(pair_id)
                        print(f"{currency} not tradable now, added to the watchlist.")
        else:  # 后续检查
            tradable_now = set()
            for pair_id in non_tradeable_initially:
                if is_currency_pair_tradable(spot_api,pair_id):
                    print(f"{pair_id.split('_')[0]} is now tradable, initiating sale.")
                    spot_sell(spot_api,pair_id)
                    tradable_now.add(pair_id)
                else:
                    print(f"{pair_id} not tradable now.")
            
            # 更新 non_tradeable_initially 列表
            non_tradeable_initially.difference_update(tradable_now)

    except ApiException as e:
        print(f"API Exception: {e}")

def main(spot_api, account_name):
    print(f"Checking account: {account_name}")
    check_and_sell(spot_api)

if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        accounts = json.load(config_file)

    spot_apis = {}
    for account in accounts:
        configuration = Configuration(key=account['API_KEY'], secret=account['API_SECRET'])
        api_client = ApiClient(configuration)
        spot_apis[account['ACCOUNT_NAME']] = SpotApi(api_client)

    while True:
        for account_name, spot_api_instance in spot_apis.items():
            main(spot_api_instance, account_name)

        time.sleep(5)