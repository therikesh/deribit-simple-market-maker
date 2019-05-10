import deribit_interface
import threading
import time

### CONSTANTS ###
AMOUNT_TO_TRADE = 10
INSTRUMENT_NAME = 'BTC-PERPETUAL'
CLIENT_ID = 'QGJ6REiriDa3'
CLIENT_SECRET = 'X7PJRHVNAAKHDDR5NHT5Y5JU4FWUC7B6'
### ### ###


### system value ###
deribit = deribit_interface.Deribit(test=True, 
	client_ID=CLIENT_ID,
 	client_secret=CLIENT_SECRET)
logwritter = deribit.logwritter

buy_order_id, sell_order_id, bid_last, ask_last, case_pose = None, None, None, None, None
first_trade = True
step_in_algo = 0
### ### ###

### functions ###

def First_setuper():
	global deribit, AMOUNT_TO_TRADE, INSTRUMENT_NAME, buy_order_id, sell_order_id, bid_last, ask_last
	ask_last = deribit.Orderbook['asks'][0][0]
	bid_last = deribit.Orderbook['bids'][0][0]
	logwritter('now: bid/ask %f/%f' % (bid_last, ask_last))

	buy_order_id = deribit.make_order(side='buy',
		instrument_name=INSTRUMENT_NAME,
		amount=AMOUNT_TO_TRADE,
		price=bid_last,
		post_only=True)['order']['order_id']
	sell_order_id = deribit.make_order(side='sell',
		instrument_name=INSTRUMENT_NAME,
		amount=AMOUNT_TO_TRADE,
		price=ask_last,
		post_only=True)['order']['order_id']
	logwritter('Setup first order OK')



def Order_manager(timeout=0.1):
	global deribit, AMOUNT_TO_TRADE, INSTRUMENT_NAME, buy_order_id, sell_order_id, step_in_algo, case_pose, ask_last, bid_last, first_trade
	while True:
		ask_now = deribit.Orderbook['asks'][0][0]
		bid_now = deribit.Orderbook['bids'][0][0]

		if not first_trade: # Change order to actual price
			if (not ask_now==ask_last) or (not bid_now==ask_last):
				logwritter('change order to actual price')
				deribit.edit_order(order_id=buy_order_id, amount=2*AMOUNT_TO_TRADE, price=bid_now)
				deribit.edit_order(order_id=sell_order_id, amount=2*AMOUNT_TO_TRADE, price=ask_now)
			ask_last = ask_now
			bid_last = bid_now

		if step_in_algo==0:
			logwritter('step 0')
			if case_pose=='buy_first_filled' or first_trade:
				status_buy = deribit.get_order_state(order_id=buy_order_id)['order_state']
				if status_buy=='filled':
					if first_trade:
						case_pose = 'buy_first_filled'
					price_editor_busy = False
					step_in_algo = 1
			if case_pose=='sell_first_filled' or first_trade:
				status_sell = deribit.get_order_state(order_id=sell_order_id)['order_state']
				if status_sell=='filled':
					if first_trade:
						case_pose = 'sell_first_filled'
					price_editor_busy = False
					step_in_algo = 1

		if step_in_algo==1:
			logwritter('step 1')
			if case_pose=='buy_first_filled' and not first_trade:
				sell_order_id = deribit.make_order(side='sell',
												instrument_name=INSTRUMENT_NAME,
												amount=2*AMOUNT_TO_TRADE,
												price=ask_now,
												post_only=True)['order']['order_id']
			if case_pose=='buy_first_filled' and first_trade:
				first_trade = False
				deribit.edit_order(order_id=sell_order_id, amount=2*AMOUNT_TO_TRADE, price=ask_now)
			if case_pose=='sell_first_filled' and not first_trade:
				buy_order_id = deribit.make_order(side='buy',
												instrument_name=INSTRUMENT_NAME,
												amount=2*AMOUNT_TO_TRADE,
												price=bid_now,
												post_only=True)['order']['order_id']
			if case_pose=='sell_first_filled' and first_trade:
				first_trade = False
				deribit.edit_order(order_id=buy_order_id, amount=2*AMOUNT_TO_TRADE, price=bid_now)
			step_in_algo = 2
			continue

		if step_in_algo==2:
			logwritter('step 2')
			status_order = None
			if case_pose=='buy_first_filled':
				status_order = deribit.get_order_state(order_id=sell_order_id)['order_state']
			if case_pose=='sell_first_filled':
				status_order = deribit.get_order_state(order_id=buy_order_id)['order_state']
			if status_order=='filled':
				if case_pose=='buy_first_filled':
					buy_order_id = deribit.make_order(side='buy',
								instrument_name=INSTRUMENT_NAME,
								amount=2*AMOUNT_TO_TRADE,
								price=bid_now,
								post_only=True)['order']['order_id']
				if case_pose=='sell_first_filled':
					sell_order_id = deribit.make_order(side='sell',
								instrument_name=INSTRUMENT_NAME,
								amount=2*AMOUNT_TO_TRADE,
								price=ask_now,
								post_only=True)['order']['order_id']
				step_in_algo = 0
		time.sleep(timeout)
### ### ###


if __name__=="__main__":
	#open('log.log', 'w')
	deribit.start_orderbook_update(instrument_name='BTC-PERPETUAL')
	time.sleep(3)
	First_setuper()
	Order_manager()
