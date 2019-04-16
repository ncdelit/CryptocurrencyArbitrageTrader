import hashlib
import hmac
import urllib, json
import pandas as pd
import numpy as np
from collections import OrderedDict
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+
from urllib import urlretrieve
import time
import requests
from math import floor, ceil
import traceback

"Core Trading Functions"

def GetBidPriceOnBinance(Coin):
    Price = 0
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol='+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        Price = data4['price']
    except Exception,e:
        traceback.print_exc()
        GetBidPriceOnBinance(Coin)

    return Price

def GetAskPriceOnBinance(Coin):
    Price = 0
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol='+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        Price = data4['price']
    except Exception,e:
        traceback.print_exc()
        GetAskPriceOnBinance(Coin)

    return Price

def GetSellOrderBookOnBinance(Coin):
    df = pd.DataFrame()
    try:
        url = "https://api.binance.com/api/v1/depth?symbol="+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['bids'], orient='columns')
        df.rename(columns={0: 'Price',1:'Qty'}, inplace=True)
        df = df.apply(pd.to_numeric, errors='coerce', axis=1)
        #cols = ['col1', 'col2', 'col3'] for converting select columns to numbers
        #data[cols] = data[cols].apply(pd.to_numeric, errors='coerce', axis=1)
        df['Total'] = df['Price']*df['Qty']
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetSellOrderBookOnBinance(Coin)

    return df

def GetBuyOrderBookOnBinance(Coin):
    df = pd.DataFrame()
    try:
        url = "https://api.binance.com/api/v1/depth?symbol="+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['asks'], orient='columns')
        df.rename(columns={0: 'Price',1:'Qty'}, inplace=True)
        df = df.apply(pd.to_numeric, errors='coerce', axis=1)
        df['Total'] = df['Price']*df['Qty']
    except Exception,e:
        traceback.print_exc()
        GetBuyOrderBookOnBinance(Coin)

    return df

def GetSellOrderBookVolumeOnBinance(Coin,SellingPrice):
    OrderBookVolume2 = 0
    OB = pd.DataFrame()
    try:
        OB = GetSellOrderBookOnBinance(Coin)
        OB = OB[(OB['Price']>=SellingPrice)]
        OrderBookVolume2 = OB["Total"].sum()
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetSellOrderBookVolumeOnBinance(Coin,SellingPrice)
    return OrderBookVolume2

def roundDown(n, d):
    d = int('1' + ('0' * d))
    return floor(n * d) / d

def roundUp(n, d):
    d = int('1' + ('0' * d))
    return ceil(n * d) / d

def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

def PopulateBinancePriceList():
    global control
    try:
        url = 'https://api.binance.com/api/v1/ticker/24hr'
        response = urllib.urlopen(url)
        data = json.loads(response.read())
    except Exception,e:
        traceback.print_exc()
        control = True

    markets2 = []
    asks2 = []
    bids2 = []

    try:
        coin,status = GetBinanceCoinStatus()
        for i in range(len(data)):
            cont = False
            try:
                for j in range(len(coin)):
                    if (coin[j] in data[i]['symbol']):
                        if (status[j] == False):

                            cont == True
                            break
                if cont == True:
                    continue
                sym = str(data[i]['symbol'])
                Coin1 = sym[:len(sym)-3]
                Coin2 = sym[len(sym)-3:len(sym)]
                markets2.append(Coin1 + "-"+Coin2)
                asks2.append(float(data[i]['askPrice']))
                bids2.append(float(data[i]['bidPrice']))
            except Exception,e:
                markets2.append(str(data[i]['symbol']))
                asks2.append(0)
                bids2.append(0)
    except Exception,e:
        traceback.print_exc()
        control = True


    BinancePriceList = pd.DataFrame(columns=['A'])
    BinancePriceList = BinancePriceList.drop(['A'], axis=1)

    BinancePriceList['symbol'] =markets2
    BinancePriceList['symbol2'] =markets2
    BinancePriceList['BinanceAskPrice'] = asks2
    BinancePriceList['BinanceBidPrice'] = bids2

    return BinancePriceList

def GetBinanceAddress(CoinBought):
    print("GetBinanceAddress...")
    api_key = ''
    api_secret = ''

    request_url = 'https://api.binance.com/wapi/v3/depositAddress.html?'

    timestamp = int(time.time() * 1000)

    querystring = {'asset': str(CoinBought), 'timestamp' : timestamp, "recvWindow": str(10000000)}
    querystring = urllib.urlencode(querystring)

    signature = hmac.new(api_secret.encode('utf-8'), querystring.encode('utf-8'), hashlib.sha256).hexdigest()

    request_url += querystring + '&signature=' + signature

    r = requests.get(request_url, headers={"X-MBX-APIKEY": api_key})
    data = r.json()
    #print("GetBinanceAddress: "+str(data))
    if data['success'] == False:
        GetBinanceAddress(CoinBought)
    print("GetBinanceAddress: "+str(data))
    return str(data['address'])

def SellOnBinance(pair):
    print("SellOnBinance...")
    Coin2 = pair.split("-",1)[1]
    Coin1 = pair.split("-",1)[0]

    wait = GetBalanceOnBinance(Coin1)
    while wait < 0.05:
        wait = GetBalanceOnBinance(Coin1)
        print(wait)
        time.sleep(60*1)

    api_key = ''
    api_secret = ''

    request_url = 'https://api.binance.com/api/v3/order?'

    timestamp = int(time.time() * 1000)

    A = str(GetStepSize(Coin1+Coin2))
    bal = GetBalanceOnBinance(Coin1)
    qty = ''
    #print(int((A.replace('.', '')).find('1')))
    if (int((A.replace('.', '')).find('1')) == 0):
        qty = str(int(bal))
    else:
        qty =str(roundDown(bal, d=int((A.replace('.', '')).find('1'))))

    querystring = {'symbol': str(Coin1 + Coin2),'side':'SELL','type': 'MARKET','quantity':qty}

    querystring = urllib.urlencode(OrderedDict(querystring))

    querystring = "&symbol=" +str(Coin1 + Coin2) +  "&side=SELL" + "&type=MARKET" + "&quantity=" +qty + "&recvWindow="+str(10000000)+ "&timestamp=" + str(timestamp)

    signature = hmac.new(api_secret.encode('utf-8'), querystring.encode('utf-8'), hashlib.sha256).hexdigest()

    request_url += querystring + '&signature=' + signature
    #print(request_url)

    r = requests.post(request_url, headers={"X-MBX-APIKEY": api_key})
    data = r.json()
    print("SellOnBinance: " + str(data))

def GetBalanceOnBinance(coin):
    print("GetBalanceOnBinance...")
    api_key = ''
    api_secret = ''

    #Coin1 = pair.split("-",1)[0]
    request_url = 'https://api.binance.com/api/v3/account?'

    timestamp = int(time.time() * 1000)

    querystring = {'timestamp' : timestamp}
    querystring = urllib.urlencode(querystring)

    signature = hmac.new(api_secret.encode('utf-8'), querystring.encode('utf-8'), hashlib.sha256).hexdigest()

    request_url += querystring + '&signature=' + signature

    r = requests.get(request_url, headers={"X-MBX-APIKEY": api_key})
    data = r.json()
    #print("GetBalanceOnBinance: " + str(data))
    #print(data)

    if "error" in data:
        GetBalanceOnBinance(coin)
    Balance = 0.00
    for i in range(len(data['balances'])):
        if data['balances'][i]['asset'] == coin:
            Balance = float(data['balances'][i]['free'])

    return Balance

def DownloadStepSizes():
    api_key = ''
    api_secret = ''

    #Coin1 = pair.split("-",1)[0]
    request_url = 'https://www.binance.com/api/v1/exchangeInfo'

    r = requests.get(request_url)
    data = r.json()
    print(data)


    Symbols = []
    Stepsizes = []
    for i in range(len(data['symbols'])):
        Symbols.append(data['symbols'][i]['symbol'])
        Stepsizes.append(float(data['symbols'][i]['filters'][1]['stepSize']))

    StepSizes = pd.DataFrame(columns=['A'])
    StepSizes = StepSizes.drop(['A'], axis=1)

    StepSizes['symbol'] = Symbols
    StepSizes['step'] = Stepsizes

    print(StepSizes)
    import pickle

    StepSizes.to_pickle('StepSizes.db')

def GetStepSize(Coin):
    df = pd.read_pickle('StepSizes.db')

    df = df[(df['symbol'] == Coin)]

    return float(df.head(1)['step'].values[0])

def BuyOnBinance(pair,Price):
    print("BuyOnBinance...")
    Coin2 = pair.split("-",1)[1]
    Coin1 = pair.split("-",1)[0]

    api_key = ''
    api_secret = ''

    request_url = 'https://api.binance.com/api/v3/order?'

    timestamp = int(time.time() * 1000)

    A = str(GetStepSize(Coin1+Coin2))
    bal = (GetBalanceOnBinance(Coin2)*0.95)/Price


    qty = ''
    #print(int((A.replace('.', '')).find('1')))
    if (int((A.replace('.', '')).find('1')) == 0):
        qty = str(int(bal))
    else:
        qty =str(roundDown(bal, d=int((A.replace('.', '')).find('1'))))


    # querystring = {'symbol': str(Coin1 + Coin2),'side':'BUY','type': 'LIMIT','quantity':qty,'price':Price}

    #querystring = urllib.urlencode(OrderedDict(querystring))

    querystring = "&symbol=" +str(Coin1 + Coin2) +  "&side=BUY" + "&type=MARKET" + "&quantity=" +str(qty) + "&recvWindow="+str(10000000)+ "&timestamp=" + str(timestamp)

    signature = hmac.new(api_secret.encode('utf-8'), querystring.encode('utf-8'), hashlib.sha256).hexdigest()

    request_url += querystring + '&signature=' + signature
    #print(request_url)


    r = requests.post(request_url, headers={"X-MBX-APIKEY": api_key})
    data = r.json()
    print("BuyOnBinance: "+ str(data))

def GetPriceOfRecentTradeOnBinance(pair):
    Coin2 = pair.split("-",1)[1]
    Coin1 = pair.split("-",1)[0]

    # wait = GetBalanceOnBinance(Coin1)
    # while wait != 0:
    #     wait = GetBalanceOnBinance(Coin1)
    #     print(wait)
    #     time.sleep(60*1)

    api_key = ''
    api_secret = ''

    request_url = 'https://api.binance.com/api/v3/myTrades?'

    timestamp = int(time.time() * 1000)

    # bal = str(GetBalanceOnBinance(Coin1))
    # A = GetStepSize(Coin1)
    # querystring = {'symbol': str(Coin1 + Coin2),'timestamp':timestamp,'limit': 1}
    #
    # querystring = urllib.urlencode(OrderedDict(querystring))

    querystring = "&symbol=" +str(Coin1)+str(Coin2)+"&limit="+str(1)+"&timestamp=" + str(timestamp) + "&recvWindow="+str(10000000)

    signature = hmac.new(api_secret.encode('utf-8'), querystring.encode('utf-8'), hashlib.sha256).hexdigest()

    request_url += querystring + '&signature=' + signature
    #print(request_url)

    r = requests.get(request_url, headers={"X-MBX-APIKEY": api_key})
    #print(r.text)
    #print(request_url)
    data = r.json()
    print("GetPriceOfRecentTradeOnBinance: " +str(data))
    if (float(data[0]['qty']) == 0):
        GetPriceOfRecentTradeOnBinance(pair)
    else:
        return float(data[0]['price'])

def GetBinanceTradingStatus():
    url2 = 'https://api.binance.com/api/v1/exchangeInfo'
    response2 = urllib.urlopen(url2)
    data2 = json.loads(response2.read())

    #Coin1 = pair.split("-",1)[0]
    coin = []
    status = []
    for i in range(len(data2['symbols'])):
        coin.append(data2['symbols'][i]['symbol'])
        status.append(data2['symbols'][i]['status'])

    return coin,status

def GetBinanceCoinStatus():
    url2 = 'https://www.binance.com/assetWithdraw/getAllAsset.html'
    response2 = urllib.urlopen(url2)
    data2 = json.loads(response2.read())

    #Coin1 = pair.split("-",1)[0]
    coin = []
    status = []
    for i in range(len(data2)):
        coin.append(data2[i]['assetCode'])
        status.append(data2[i]['enableWithdraw'])


    return coin,status

def WithdrawFromBinance(Coin,SaleOrPurchase,address, qty):
    print("WithdrawFromBinance...")
    time.sleep(2*1)
    wait = GetBalanceOnBinance(Coin)
    while wait == 0:
        time.sleep(2*1)
        wait = GetBalanceOnBinance(Coin)
        print(wait)
        time.sleep(30*1)

    api_key = ''
    api_secret = ''

    request_url = 'https://api.binance.com/wapi/v3/withdraw.html?'

    timestamp = int(time.time() * 1000)

    # A = str(GetStepSize(Coin1+Coin2))
    # bal = GetBalanceOnBinance(Coin1)
    # qty = ''
    # print(int((A.replace('.', '')).find('1')))
    # if (int((A.replace('.', '')).find('1')) == 0):
    #     qty = str(int(bal))
    # else:
    #     qty =str(round(bal,int((A.replace('.', '')).find('1'))))

    # querystring = {'symbol': str(Coin1 + Coin2),'side':'SELL','type': 'MARKET','quantity':qty}

    # querystring = urllib.urlencode(OrderedDict(querystring))

    if (SaleOrPurchase == 'Purchase'):
        querystring = "&asset=" +Coin +  "&address=" +str(address)+ "&amount=" + str(GetBalanceOnBinance(Coin)) +"&name=Binance"+"&timestamp=" + str(timestamp)
    else:
        querystring = "&asset=" +Coin +  "&address=" + str(address)+ "&amount=" + str(qty) +"&name=Binance"+"&timestamp=" + str(timestamp)

    signature = hmac.new(api_secret.encode('utf-8'), querystring.encode('utf-8'), hashlib.sha256).hexdigest()

    request_url += querystring + '&signature=' + signature
    print(request_url)

    r = requests.post(request_url, headers={"X-MBX-APIKEY": api_key})
    data = r.json()
    print("WithdrawFromBinance: " + str(data))
    if ("false" in data):
        WithdrawFromBinance(Coin,SaleOrPurchase,Pair)

"Trading Mechanisms"

def InitiateOnBinance(Pair,Price,address):
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]

    BuyOnBinance(Pair,Price)
    WithdrawFromBinance(Coin1,"Purchase",address,"")

def CloseOnBinance(Pair,Price,address):
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]

    A = GetBalanceOnBinance(Coin2)
    SellOnBinance(Pair)
    time.sleep(15)
    B = GetBalanceOnBinance(Coin2)
    WithdrawFromBinance(Coin2,"Sale",address,B-A)
