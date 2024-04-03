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

def check_and_sell(spot_api, account_name):
    global non_tradeable_initially

    if account_name not in non_tradeable_initially:
        non_tradeable_initially[account_name] = {'not_tradable': set(), 'tradable': set()}

    print(f"Checking account: {account_name}")

    try:
        current_pairs = {pair.id for pair in spot_api.list_currency_pairs()}

        # 初始搜寻
        if not non_tradeable_initially[account_name]['not_tradable']:
            for balance in spot_api.list_spot_accounts():
                currency = balance.currency.upper()
                if currency != 'USDT':
                    pair_id = f"{currency}_USDT"
                    if pair_id not in non_tradeable_initially[account_name]['tradable']:
                        if not is_currency_pair_tradable(spot_api, pair_id):
                            non_tradeable_initially[account_name]['not_tradable'].add(pair_id)
                            print(f"{currency} not tradable now, added to the watchlist for account {account_name}.")
                        else:
                            non_tradeable_initially[account_name]['tradable'].add(pair_id)
        else:  # 后续检查
            tradable_now = set()
            for pair_id in non_tradeable_initially[account_name]['not_tradable']:
                if is_currency_pair_tradable(spot_api, pair_id):
                    print(f"{pair_id.split('_')[0]} is now tradable, initiating sale.")
                    spot_sell(spot_api, pair_id)
                    tradable_now.add(pair_id)
                else:
                    print(f"{pair_id} not tradable now.")

            # 更新 non_tradeable_initially 列表
            non_tradeable_initially[account_name]['not_tradable'].difference_update(tradable_now)
            non_tradeable_initially[account_name]['tradable'].update(tradable_now)

    except ApiException as e:
        print(f"API Exception: {e}")

non_tradeable_initially = {}

def account_monitor(account):
    configuration = Configuration(key=account['API_KEY'], secret=account['API_SECRET'])
    api_client = ApiClient(configuration)
    spot_api = SpotApi(api_client)
    account_name = account['ACCOUNT_NAME']

    while True:
        check_and_sell(spot_api, account_name)
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
        while True:  # 保持主线程运行，直到收到中断信号
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted, exiting...")