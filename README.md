# Deribit-simple-market-maker
##Использование api:
###Авторизация:
```python
deribit = deribit_interface.Deribit(test=True, 
	client_ID=<client_ID>,
 	client_secret=<client_secret>)
```
###Создание ордера:
```python
deribit.make_order(side='sell',
  instrument_name=<instrument_name>,
  amount=<amount>,
  price=<price>,
  post_only=True)
```
Больше примеров в файле market-maker.py 
                        
##Простой маркет-мейкер бот для биржи Deribit (API over WebSocket)

###Что делает бот:
1. Выставляет ордера с двух сторон по лучшим ценам bid/ask(пустоты не заполняет).
2. Ждет выполнение одного из ордеров.
3. Если один из ордеров исполняется, то ставится противоположный ордер с объемом x2 от изначального (чтобы покрыть текущую позицию и войти в новую).
3.1. Если цена уходит от цены ордера, ордер обновляется до актуальных цен.

Стратегию и ее параметры можно изменить в файле market-market-maker.py.
ОСТОРОЖНО! Бот в изначальном виде стабильно приносит убыток, без изменения стратегии вы будете терять деньги.

