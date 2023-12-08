import argparse
import time
import json
from web3 import Web3
from datetime import datetime
import threading
import os
import sys
from pyuniswap.pyuniswap import Token

f = open('config.json')
data = json.load(f)
provider_http = data["provider_http"]
wallet_address = data["wallet_address"]
private_key = data["private_key"]
new_token = sys.argv[1]
buy_type = sys.argv[2]
# for buy_type 1
buy_amount = int(data["buy_amount"] * pow(10, 18)) 
# for buy_type 2
buy_token_amount = int(data["buy_token_amount"])
max_eth_amount = int(data["max_eth_amount"] * pow(10, 18))

sliipage = int(data["slippage"]) / 100
speed = int(data["speed"])
gas_limit = int(data["gas_limit"])
gas_price = int(data["gas_price"])
current_token = Token(
        address=new_token,
        provider=provider_http,
    )
current_token.connect_wallet(wallet_address, private_key)  # craete token
current_token.set_gas_limit(gas_limit)

buy_price = 0
sell_price = 0
token_found = False
sell_flag = False
token_decimal = current_token.decimals()


token_balance = current_token.balance()
liquidity_add_methods = ['0xe8e33700', '0x384e03db', '0x4515cef3', '0x267dd102', '0xe8078d94', '0xc9567bf9', '0x8a8c523c', '0xd543dbeb', '0xf305d719', '0x83791758', '0x01339c21', '0x8f70ccf7', '0x293230b8', '0x31532eb8', '0xa6334231']
liquidity_remove_methods = ['0xbaa2abde', '0x02751cec', '0xaf2979eb', '0xded9382a', '0x5b0d5984', '0x2195995c']
liquidity_rug_methods = ['0xec28438a', '0x1bbae6eo', '0x74010ece', '0xbc337182', '0xea1644d5', '0xd543dbeb', '0xe8b94e5a', '0xc6d69a30', '0x45596e2e', '0x5880b873', '0xc4081a4c', '0x4bf2c7c9', '0x379e2919', '0x061c82d0', '0xfbeb37be', '0x357bf15c', '0x8ee88c53', '0xd54994db', '0xa08f6760']
set_bots_methods = ['0xb515566a', '0x4303443d', '0xf2cc0c18', '0x41959586', '0xff897570', '0xf375b253', '0x00b8cf2a', '0x966924f9', '0x089d566c', '0xffecf516']

def mempool():
    print('Waiting liquidity to be added')
    event_filter = current_token.web3.eth.filter("pending")
    while not sell_flag:
        try:
            new_entries = event_filter.get_new_entries()
            threading.Thread(target=get_event, args=(new_entries,)).start()
        except Exception as err:
            print(err)
            pass

def get_event( new_entries):
    global sell_flag
    for event in new_entries[::-1]:
        try:
            threading.Thread(target=handle_event, args=(event,)).start()
            if sell_flag:
                return
        except Exception as e:
            print(e)
            pass

def handle_event(event):
    try:
        transaction = current_token.web3.eth.getTransaction(event)
        # print("Transaction Added : {}".format(event.hex()))
        if not token_found and (transaction.input[:10].lower() in liquidity_add_methods) and (new_token[2:].lower() in transaction.input.lower() or new_token.lower() in transaction.to.lower()):
            print('Start Buy')
            
            threading.Thread(target=buy, args=(int(transaction.gasPrice), int(transaction.gas), int(transaction.maxFeePerGas), int(transaction.maxPriorityFeePerGas), )).start()
            
            print("Liquidity Added : {}".format(event.hex()))
        if token_found and (new_token[2:].lower() in transaction.input.lower() or new_token.lower() in transaction.to.lower()):
            if (transaction.input[:10].lower() in liquidity_remove_methods) or (transaction.input[:10].lower() in liquidity_rug_methods) or (transaction.input[:10].lower() in set_bots_methods):
                print('Start Sell')
                threading.Thread(target=start_sell).start()
    except Exception as e:
        pass

def buy(gas_price, gas_limit, maxFeePerGas, maxPriorityFeePerGas):
    global token_found
    # current_token.set_gas_limit(gas_limit)
    if buy_type == 1:
        sign_tx = current_token.buy_type1(int(buy_amount), slippage=sliipage,
                                gas_price=int(gas_price*speed), timeout=2100, maxFeePerGas=maxFeePerGas, maxPriorityFeePerGas=maxPriorityFeePerGas)
    else:
        sign_tx = current_token.buy_type2(int(buy_token_amount), int(max_eth_amount), slippage=sliipage,
                                gas_price=int(gas_price*speed), timeout=2100, maxFeePerGas=maxFeePerGas, maxPriorityFeePerGas=maxPriorityFeePerGas)
    try:
        result = current_token.send_buy_transaction(sign_tx)
        print('Wait until transaction completed...')
        print(f'Buy transaction: {result.hex()}')
        retry = 1
        while retry < 300:
            current_balance = current_token.balance()
            if current_balance > token_balance:
                print("Buy transaction confirmed")
                token_found = True
                break
                # start_sell()

            retry += 1
            time.sleep(1)
        if retry >= 300:
            print("Buy transaction failed")

    except Exception as e:
        print(f'Buy error: {e}')
        print(f'Retry ...')
        print(f'Buy error: {e}')

def start_sell():
    print("Buy price", buy_price)
    while True:
        current_price = current_token.price()
        print("current_price: ", current_price)
        threading.Thread(target=sell).start()

def sell():
    global current_token
    global sell_flag
    balance = current_token.balance()
    print(balance)
    while not sell_flag:
        try:
            transaction_address = current_token.sell(balance, slippage=sliipage, timeout=2100, gas_price=gas_price * 10 ** 9)  # sell token as amount
            print("Sell transaction address", transaction_address)
            sell_flag = True
        except Exception as e:
            print(e)

def main():
    
    print("start")
    # threading.Thread(target=mempool).start()

if __name__ == '__main__':
    main()
