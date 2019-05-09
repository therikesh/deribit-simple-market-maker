import deribit_interface
import threading

AMOUNT_TO_TRADE = 10
INSTRUMENT_NAME = 'BTC-PERPETUAL'


deribit = deribit_interface.Deribit(test=True, 
	client_ID='QGJ6REiriDa3',
 	client_secret='X7PJRHVNAAKHDDR5NHT5Y5JU4FWUC7B6')
logwritter = deribit.logwritter

buy_filled, sell_filled = False, False
buy_order_id, sell_order_id, bid_last, ask_last = None, None, None, None
case_pose = 'first_trade'
checker_is_busy = False
price_editor_busy = True


def thread_decor(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper


def First_setuper():
	global deribit, AMOUNT_TO_TRADE, INSTRUMENT_NAME, buy_order_id, sell_order_id, bid_last, ask_last
	orderbook = deribit.get_order_book(instrument_name=INSTRUMENT_NAME, depth=1)
	bid_last = orderbook['best_bid_price']
	ask_last = orderbook['best_ask_price']
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


@thread_decor
def Checker_filling_orders():
	global deribit, AMOUNT_TO_TRADE, INSTRUMENT_NAME, buy_order_id, sell_order_id, buy_filled, sell_filled, case_pose, checker_is_busy
	if not checker_is_busy:
		checker_is_busy = True
		ask_now = deribit.Quote['best_ask_price']
		bid_now = deribit.Quote['best_bid_price']

		if case_pose=='first_trade' or case_pose=='buy_first_filled':
			status_order = deribit.get_order_state(order_id=buy_order_id)['order_state']
			if status_order=='filled' or case_pose=='buy_first_filled':
				price_editor_busy = False
				if not case_pose=='first_trade':
					sell_order_id = deribit.make_order(side='sell',
						instrument_name=INSTRUMENT_NAME,
						amount=2*AMOUNT_TO_TRADE,
						price=ask_now,
						post_only=True)['order']['order_id']
				if buy_filled:
					deribit.edit_order(order_id=sell_order_id, price=ask_now, amount=2*AMOUNT_TO_TRADE)
				case_pose = 'buy_first_filled'
				buy_filled, sell_filled = True, False
				status_order = deribit.get_order_state(order_id=sell_order_id)['order_state']
				if status_order=='filled':
					buy_order_id = deribit.make_order(side='buy',
						instrument_name=INSTRUMENT_NAME,
						amount=2*AMOUNT_TO_TRADE,
						price=bid_now,
						post_only=True)['order']['order_id']
					buy_filled, sell_filled = False, True

		if case_pose=='first_trade' or case_pose=='sell_first_filled':
			status_order = deribit.get_order_state(order_id=sell_order_id)['order_state']
			if status_order=='filled' or case_pose=='sell_first_filled':
				price_editor_busy = False
				if not case_pose=='first_trade':
					buy_order_id = deribit.make_order(side='buy',
						instrument_name=INSTRUMENT_NAME,
						amount=2*AMOUNT_TO_TRADE,
						price=bid_now,
						post_only=True)['order']['order_id']
				case_pose = 'sell_first_filled'
				if sell_filled:
					deribit.edit_order(order_id=buy_order_id, price=bid_now, amount=2*AMOUNT_TO_TRADE)
				sell_filled, buy_filled = True, False
				status_order = deribit.get_order_state(order_id=buy_order_id)['order_state']
				if status_order=='filled':
					sell_order_id = deribit.make_order(side='sell',
						instrument_name=INSTRUMENT_NAME,
						amount=2*AMOUNT_TO_TRADE,
						price=ask_now,
						post_only=True)['order']['order_id']
					sell_filled, buy_filled = False, True
		checker_is_busy = False


@thread_decor
def Price_orders_editor():
	return
	global deribit, AMOUNT_TO_TRADE, INSTRUMENT_NAME, buy_order_id, sell_order_id, ask_last, bid_last, price_editor_busy
	if not price_editor_busy:
		price_editor_busy = True
		ask_now = deribit.Quote['best_ask_price']
		bid_now = deribit.Quote['best_bid_price']
		if (not ask_now==ask_last) or (not bid_now==ask_last):
			deribit.edit_order(order_id=buy_order_id, amount=2*AMOUNT_TO_TRADE, price=bid_now)
			deribit.edit_order(order_id=sell_order_id, amount=2*AMOUNT_TO_TRADE, price=ask_now)
		ask_last = ask_now
		bid_last = bid_now
		price_editor_busy = False


def combiner_for_two_func():
	Checker_filling_orders()
	Price_orders_editor()

if __name__=="__main__":
	First_setuper()
	deribit.start_quote_update(instrument_name='BTC-PERPETUAL', func_for_quoting=combiner_for_two_func)