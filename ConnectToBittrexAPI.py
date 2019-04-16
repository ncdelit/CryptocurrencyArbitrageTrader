import hashlib
import hmac
import urllib, json
import pandas as pd
import numpy as np
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+
from urllib import urlretrieve
import time
import requests
import decimal
import sys, os
import traceback


# create a new context for this task
ctx = decimal.Context()

# 20 digits should be enough for everyone :D
ctx.prec = 20

"Core Trading Functions"

def GetBidPriceOnBittrex(Coin):
    Price = 0
    try:
        url = 'https://bittrex.com/api/v1.1/public/getticker?market=BTC'+'-'+Coin
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        Price = data4['result']['Bid']
    except Exception,e:
        traceback.print_exc()
        GetBidPriceOnBittrex(Coin)
    return Price

def GetAskPriceOnBittrex(Coin):
    Price = 0
    try:
        url = 'https://bittrex.com/api/v1.1/public/getticker?market=BTC'+'-'+Coin
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        Price = data4['result']['Ask']
    except Exception,e:
        traceback.print_exc()
        GetAskPriceOnBittrex(Coin)

    return Price

def GetBuyOrderBookOnBittrex(Coin):
    df = pd.DataFrame()
    try:
        url = "https://bittrex.com/api/v1.1/public/getorderbook?market="+'BTC'+'-'+Coin+"&type=both"
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['result']['sell'], orient='columns')
        df.rename(columns={'Quantity': 'Qty','Rate':'Price'}, inplace=True)
        df['Total'] = df['Price']*df['Qty']
    except Exception,e:
        traceback.print_exc()
        GetBuyOrderBookOnBittrex(Coin)
    return df

def GetSellOrderBookOnBittrex(Coin):
    df = pd.DataFrame()
    try:
        url = "https://bittrex.com/api/v1.1/public/getorderbook?market="+'BTC'+'-'+Coin+"&type=both"
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['result']['buy'], orient='columns')
        df.rename(columns={'Quantity': 'Qty','Rate':'Price'}, inplace=True)
        df['Total'] = df['Price']*df['Qty']
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetSellOrderBookOnBittrex(Coin)
    return df

def GetSellOrderBookVolumeOnBittrex(Coin,SellingPrice):
    OrderBookVolume2 = 0
    OB = pd.DataFrame()
    try:
        OB = GetSellOrderBookOnBittrex(Coin)
        OB = OB[(OB['Price']>=SellingPrice)]
        OrderBookVolume2 = OB["Total"].sum()
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetSellOrderBookVolumeOnBittrex(Coin,SellingPrice)
    return OrderBookVolume2

def float_to_str(f):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')

def PopulateBittrexPriceList():
    global control
    try:
        url = "https://bittrex.com/api/v1.1/public/getmarketsummaries"
        response = urllib.urlopen(url)
        data = json.loads(response.read())
    except Exception,e:
        traceback.print_exc()
        control = True

    markets = []
    markets3 = []
    asks = []
    bids = []

    bittcoin, bitstatus = GetBittrexCoinStatus()
    for i in range(len(data['result'])): #
        cont = False
        try:
            Coin2 = str(data['result'][i]['MarketName']).split("-",1)[1]
            Coin1 = str(data['result'][i]['MarketName']).split("-",1)[0]
            for j in range(len(bittcoin)):
                if (bittcoin[j] in (str(Coin2 +Coin1))):
                    if (bitstatus[j] == False):
                        cont = True
                        break
            if cont == True:
                continue
            markets.append(Coin2 +Coin1)
            markets3.append(Coin2 +"-"+ Coin1)
            asks.append(float(data['result'][i]['Ask']))
            bids.append(float(data['result'][i]['Bid']))
        except Exception,e:
            markets.append(Coin2 +Coin1)
            markets3.append(Coin2 +"-"+ Coin1)
            asks.append(0)
            bids.append(0)

    BittrexPriceList = pd.DataFrame(columns=['A'])
    BittrexPriceList = BittrexPriceList.drop(['A'], axis=1)

    BittrexPriceList['symbol2'] =markets3
    BittrexPriceList['symbol'] =markets3
    BittrexPriceList['BittrexAskPrice'] = asks
    BittrexPriceList['BittrexBidPrice'] = bids

    return BittrexPriceList

def BuyOnBittrex(Pair,Price):
    print("BuyOnBittrex...")
    Coin2 = Pair.split("-",1)[1]
    #print(Coin2)
    Coin1 = Pair.split("-",1)[0]

    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/market/buylimit?apikey="+api_key +"&nonce=" + str(nonce) + "&market=" + str(Coin2) +"-"+str(Coin1) + "&quantity=" + str(GetBittrexCoinBalance(Coin2)*0.95/Price) + "&rate=" + str(Price)

    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    import requests
    r = requests.post(request_url, headers=header)

    #print(request_url)
    print("BuyOnBittrex: "+str(r.json()))

def GetBittrexCoinBalance(Coin):
    print("GetBittrexCoinBalance...")

    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/account/getbalance?apikey="+api_key +"&currency=" + Coin +"&nonce=" + str(nonce)

    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    try:
        import requests
        r = requests.post(request_url, headers=header)

        print("GetBittrexCoinBalance: "+ str(r.json()))
        data = r.json()
        if (data['result']["Available"] == None):
            return 0
        else:
            return float(data['result']["Available"])
    except Exception,e:
        traceback.print_exc()
        GetBittrexCoinBalance(Coin)

def GetBittrexAddress(Coin):
    print("GetBittrexAddress...")
    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/account/getdepositaddress?apikey="+api_key +"&currency=" + Coin +"&nonce=" + str(nonce)

    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    import requests
    r = requests.post(request_url, headers=header)

    print("GetBittrexAddress: " + str(r.json()))
    try:
        data = r.json()
        if (data["success"]== False or data['result']["Address"] == '' or data['result'] == None):
            GetBittrexAddress(Coin)
        return (data['result']["Address"])
    except Exception,e:
        traceback.print_exc()
        GetBittrexAddress(Coin)

def SellOnBittrex(Pair,Price):
    print("SellOnBittrex...")
    Coin2 = Pair.split("-",1)[1]
    #print(Coin2)
    Coin1 = Pair.split("-",1)[0]

    wait = GetBittrexCoinBalance(Coin1)
    while wait < 0.05 or wait == 'None':
        time.sleep(3*1)
        try:
            wait = GetBittrexCoinBalance(Coin1)
        except Exception,e:
            traceback.print_exc()
            time.sleep(5)
            wait = GetBittrexCoinBalance(Coin1)
        print(wait)
        time.sleep(30*1)

    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/market/selllimit?apikey="+api_key +"&nonce=" + str(nonce) + "&market=" + Coin2 +"-"+Coin1 + "&quantity=" + str(wait) + "&rate=" + str(Price)
    #print(host)
    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    import requests
    r = requests.post(request_url, headers=header)

    #print(request_url)
    print("SellOnBittrex: "+str(r.json()))

def GetRecentTradeValueBittrex(Pair):
    Coin2 = Pair.split("-",1)[1]
    Coin1 = Pair.split("-",1)[0]

    wait = GetBittrexCoinBalance(Coin1)
    while wait == 0:
        wait = GetBittrexCoinBalance(Coin1)
        print(wait)
        time.sleep(60*1)


    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/account/getorderhistory?apikey="+api_key +"&nonce=" + str(nonce) + "&market=" + Pair

    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    import requests
    r = requests.post(request_url, headers=header)

    print(r.json())
    return float(data['result']["Quantity"])

def GetOpenOrdersOnBittrex():
    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/market/getopenorders?apikey="+api_key +"&nonce=" + str(nonce)

    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    import requests
    r = requests.post(request_url, headers=header)
    data = r.json()
    print("GetOpenOrdersOnBittrex: "+str(data))
    return str(data['result'][0]["OrderUuid"])

def CancelTradesOnBittrex(OrderId):
    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/market/cancel?apikey="+api_key +"&nonce=" + str(nonce) + "&uuid=" + OrderId

    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    import requests
    r = requests.post(request_url, headers=header)

    print("CancelTradesOnBittrex: "+str(r.json()))

def GetBittrexCoinBalanceForUnsettledTrade(Coin):
    print("GetBittrexCoinBalance...")

    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)
    host = "https://bittrex.com/api/v1.1/account/getbalance?apikey="+api_key +"&currency=" + Coin +"&nonce=" + str(nonce)

    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring


    import requests
    r = requests.post(request_url, headers=header)

    print("GetBittrexCoinBalance: "+ str(r.json()))
    data = r.json()
    if (data['result']["Balance"] == None):
        return 0
    else:
        return float(data['result']["Balance"])

def GetBittrexCoinStatus():
    url2 = 'https://bittrex.com/api/v1.1/public/getcurrencies'
    response2 = urllib.urlopen(url2)
    data2 = json.loads(response2.read())

    #Coin1 = pair.split("-",1)[0]
    bittcoin = []
    bittstatus = []
    for i in range(len(data2['result'])):
        bittcoin.append(data2['result'][i]['Currency'])
        bittstatus.append(data2['result'][i]['IsActive'])


    return bittcoin,bittstatus

def WithdrawFromBittrex(Coin,SaleOrPurchase,address, qty):
    print("WithdrawFromBittrex...")
    wait = GetBittrexCoinBalance(Coin)
    while wait == 0:
        wait = GetBittrexCoinBalance(Coin)
        time.sleep(60*1)


    api_key = ''
    api_secret = ''
    nonce = int(time.time() * 1000)

    if(SaleOrPurchase == 'Purchase'):
        host = "https://bittrex.com/api/v1.1/account/withdraw?apikey="+api_key +"&currency=" + str(Coin) + "&quantity="+str(GetBittrexCoinBalance(Coin)) + "&address="+str(address) +"&nonce=" + str(nonce)
    else:
        host = "https://bittrex.com/api/v1.1/account/withdraw?apikey="+api_key +"&currency=" + str(Coin) + "&quantity="+str(qty) + "&address="+str(address) +"&nonce=" + str(nonce)


    secret = ''

    request_url = host

    # Coin2 = pair.split("-",1)[1]
    # Coin1 = pair.split("-",1)[0]
    # price = round(Price*PriceAdj,GetTradePrecision(Coin2))
    # #print(GetTradePrecision(Coin1))
    # amount = round(float(GetCoinBalance(Coin2)*0.995/Price), GetTradePrecision(Coin1))
    # #print(amount)
    # type1 = 'BUY'
    #
    # querystring = "amount="+ str(amount) +"&price="+ str(price) + "&type="+str(type1)

    querystring = ''

    # strForSign = endpoint + "/" + str(nonce) +"/"+ querystring
    # import base64
    # signatureStr = base64.b64encode(strForSign.encode('utf-8'))

    signature = hmac.new(secret.encode('utf-8'), request_url.encode('utf-8'), hashlib.sha512).hexdigest()

    header ={"apisign": signature}

    request_url += querystring

    import requests
    r = requests.post(request_url, headers=header)

    #print(request_url)
    print("WithdrawFromBittrex: "+str(r.json()))
    data = r.json()
    if ("False" in data):
        WithdrawFromBittrex(Coin,SaleOrPurchase,Pair)

"Trading Mechanisms"

def InitiateOnBittrex(Pair,Price,address):
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]

    BuyOnBittrex(Pair,Price)
    WithdrawFromBittrex(Coin1,'Purchase',address, '')

def CloseOnBittrex(Pair,Price,address):
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]

    A = GetBittrexCoinBalance(Coin2)
    C = 1
    counter = 1
    while C > 0.5:
        counter = counter + 1
        SellOnBittrex(Pair,Price)
        time.sleep(15)
        C = GetBittrexCoinBalanceForUnsettledTrade(Coin1)
        time.sleep(10)
        print(C)
        if (C >0.5):
            CancelTradesOnBittrex(GetOpenOrdersOnBittrex())
            incre = incre*(counter/2)
            PriceAdj2 = 1-(incre)
        time.sleep(5)
    B = GetBittrexCoinBalance(Coin2)
    WithdrawFromBittrex(Coin2,"Sale",address,B-A)
