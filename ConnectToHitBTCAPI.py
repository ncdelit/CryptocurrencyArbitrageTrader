import time
import hmac
import urllib
import requests
import hashlib
import base64
import sys
import json
import datetime
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
from math import floor, ceil

import pandas as pd
import traceback

API_KEY = ''
API_SECRET = ''

def GetBidPriceOnHitBTC(Coin):
    Price = 0
    try:
        url = 'https://api.hitbtc.com/api/2/public/ticker/'+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        Price = data4['bid']
    except Exception,e:
        traceback.print_exc()
        GetBidPriceOnHitBTC(Coin)

    return float(Price)

def GetAskPriceOnHitBTC(Coin):
    Price = 0
    try:
        url = 'https://api.hitbtc.com/api/2/public/ticker/'+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        Price = data4['ask']
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetAskPriceOnHitBTC(Coin)

    return float(Price)

def GetSellOrderBookOnHitBTC(Coin):
    df = pd.DataFrame()
    try:
        url = "https://api.hitbtc.com/api/2/public/orderbook/"+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['bid'], orient='columns')

        df.rename(columns={'price': 'Price','size':'Qty'}, inplace=True)
        df[['Qty','Price']] = df[['Qty','Price']].apply(pd.to_numeric)
        df['Total'] = df['Price']*df['Qty']
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        if 'Symbol not found' in str(data4):
            return df
        else:
            GetSellOrderBookOnHitBTC(Coin)
    return df

def GetBuyOrderBookOnHitBTC(Coin):
    df = pd.DataFrame()
    try:
        url = "https://api.hitbtc.com/api/2/public/orderbook/"+Coin+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['ask'], orient='columns')

        #pd.DataFrame(index = ['pbp'], columns = ['a','b'], dtype = np.dtype([('str','float')])) this initialises a DF setting datatypes too
        df[['Qty','Price']] = df[['Qty','Price']].apply(pd.to_numeric)
        df['Total'] = df['Price']*df['Qty']
        df.rename(columns={'price': 'Price','size':'Qty'}, inplace=True)
    except Exception,e:
        traceback.print_exc()
        GetBuyOrderBookOnHitBTC(Coin)
    return df

def GetSellOrderBookVolumeOnHitBTC(Coin,SellingPrice):
    OrderBookVolume2 = 0
    OB = pd.DataFrame()
    try:
        OB = GetSellOrderBookOnHitBTC(Coin)
        OB = OB[(OB['Price']>=SellingPrice)]
        OrderBookVolume2 = OB["Total"].sum()
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetSellOrderBookVolumeOnHitBTC(Coin,SellingPrice)
    return OrderBookVolume2

def roundDown(n, d):
    d = int('1' + ('0' * d))
    return floor(n * d) / d

def roundUp(n, d):
    d = int('1' + ('0' * d))
    return ceil(n * d) / d

def PopulateHitBTCPriceList():
    global control
    HitBTCPriceList = pd.DataFrame(columns=['A'])
    HitBTCPriceList = HitBTCPriceList.drop(['A'], axis=1)

    url = "https://api.hitbtc.com/api/2/public/ticker"
    response = urllib.urlopen(url)
    data = json.loads(response.read())


    marketsh = []
    marketsh2 = []
    askh = []
    bidh = []
    conth = False

    Coins,Statuses = GetHitBTCCoinStatus()
    for i in range(len(data)):
        sym = data[i]['symbol']
        Coin1 = sym[:len(sym)-3]
        Coin2 = sym[len(sym)-3:len(sym)]
        conth = False
        if data[i]['ask'] == None or data[i]['bid'] == None or 'FCN' in data[i]['symbol'] or 'CAT' in data[i]['symbol'] or 'BTG' in data[i]['symbol'] or 'LDC' in data[i]['symbol'] or 'WRC' in data[i]['symbol'] or 'SMART' in data[i]['symbol'] :
            continue
        for j in range(len(Coins)):
            if Coins[j] in data[i]['symbol']:
                if Statuses[j] == False:
                    conth = True
                    break
                    #pass
        if conth == True:
            continue
        marketsh.append(Coin1+Coin2)
        marketsh2.append(Coin1 +"-" + Coin2)
        askh.append(float(data[i]['ask']))
        bidh.append(float(data[i]['bid']))

    HitBTCPriceList['symbol'] = marketsh2
    HitBTCPriceList['symbol2'] = marketsh2
    HitBTCPriceList['HitBTCAskPrice'] = askh
    HitBTCPriceList['HitBTCBidPrice'] = bidh

    return HitBTCPriceList

def GetHitBTCCoinBalance(Coin):
    print("GetHitBTCCoinBalance...")
    session = requests.session()
    session.auth = ("publicKey", "secretKey")

    session = requests.session()
    session.auth = ("", "")
    b = session.get('https://api.hitbtc.com/api/2/trading/balance').json()

    Balances = []
    Coins = []

    filtereddict = [x for x in b if x['currency'] == Coin]
    print("GetHitBTCCoinBalance: "+str(filtereddict))
    return float(filtereddict[0]['available'])

"Core Trading Functions"

def GetHitBTCAccountCoinBalance(Coin):
    print("GetHitBTCCoinBalance...")
    session = requests.session()
    session.auth = ("publicKey", "secretKey")

    session = requests.session()
    session.auth = ("", "")
    b = session.get('https://api.hitbtc.com/api/2/account/balance').json()

    Balances = []
    Coins = []

    filtereddict = [x for x in b if x['currency'] == Coin]
    print("GetHitBTCCoinBalance: "+str(filtereddict))
    return float(filtereddict[0]['available'])

def BuyOnHitBTC(Pair,Price):
    print("BuyOnHitBTC...")

    Coin2 = Pair.split("-",1)[1]
    #print(Coin2)
    Coin1 = Pair.split("-",1)[0]

    session = requests.session()
    session.auth = ("2575dd3ea4440d03a17a14c1a9d0bf61", "cbc6566aca1e16a3a57bdd0dd87ad7d8")

    A = str(GetStepSizeOnHitBTC(Coin1+Coin2))
    bal = (GetHitBTCCoinBalance(Coin2)*0.90)/Price

    qty = ''
    #print(int((A.replace('.', '')).find('1')))
    if (int((A.replace('.', '')).find('1')) == 0):
        if A.find('.') == 3:
            qty = 100*roundDown(bal/100,0)
        else:
            qty = str(int(bal))
    else:
        qty =str(roundDown(bal, d=int((A.replace('.', '')).find('1'))))

    print(qty)
    orderData = {'symbol':str(Coin1) + str(Coin2), 'side': 'buy', 'quantity': qty, 'type': 'market' }
    r = session.post('https://api.hitbtc.com/api/2/order', data = orderData)
    print("BuyOnHitBTC"+str(r.json()))

def SellOnHitBTC(Pair,Price):
    print("SellOnCryptopia...")

    Coin2 = Pair.split("-",1)[1]
    #print(Coin2)
    Coin1 = Pair.split("-",1)[0]

    wait = GetHitBTCAccountCoinBalance(Coin1)
    while wait < 0.05:
        wait = GetHitBTCAccountCoinBalance(Coin1)
        print(wait)
        time.sleep(60*1)

    TransferToTradingAccount(Coin1)

    session = requests.session()
    session.auth = ("2575dd3ea4440d03a17a14c1a9d0bf61", "cbc6566aca1e16a3a57bdd0dd87ad7d8")
    orderData = {'symbol':Coin1 + Coin2, 'side': 'sell', 'quantity': GetHitBTCCoinBalance(Coin1), 'type': 'market' }
    r = session.post('https://api.hitbtc.com/api/2/order', data = orderData)
    print("SellOnHitBTC: "+str(r.json()))

def WithdrawFromHitBTC(Coin,SaleOrPurchase,Address,Qty):
    print("WithdrawFromHitBTC...")
    session = requests.session()
    session.auth = ("2575dd3ea4440d03a17a14c1a9d0bf61", "cbc6566aca1e16a3a57bdd0dd87ad7d8")

    if SaleOrPurchase == 'Purchase':
        amt = GetHitBTCAccountCoinBalance(Coin) - GetHitBTCWithdrawalFee(Coin)
    else:
        amt = Qty - GetHitBTCWithdrawalFee(Coin)

    print(amt)
    orderData = {'currency':Coin,'amount': amt, 'address': Address}

    r = session.post('https://api.hitbtc.com/api/2/account/crypto/withdraw', data = orderData)
    print("WithdrawFromHitBTC: "+str(r.json()))
    if 'required' in r:
        WithdrawFromHitBTC(Coin,SaleOrPurchase,Address,Qty)

def GetHitBTCAddress(Coin):
    print("GetHitBTCAddress...")
    session = requests.session()
    session.auth = ("2575dd3ea4440d03a17a14c1a9d0bf61", "cbc6566aca1e16a3a57bdd0dd87ad7d8")

    orderData = {'currency':Coin}
    #+str(Coin)
    #data =  orderData
    r = session.get('https://api.hitbtc.com/api/2/account/crypto/address/'+Coin)
    print("GetHitBTCAddress:"+ str(r.json()))
    return r.json()['address']

def GetHitBTCCoinStatus():
    #print("GetHitBTCCoinStatus...")

    session = requests.session()
    session.auth = ("publicKey", "secretKey")

    session = requests.session()
    session.auth = ("", "")
    b = session.get('https://api.hitbtc.com/api/2/public/currency').json()

    Statuses = []
    Coins = []

    for i in range(len(b)):
        Coins.append(b[i]['id'])
        #print(b[i]['id'])
        Statuses.append(b[i]['payinEnabled'])
        #print(b[i]['payinEnabled'])

    return Coins,Statuses


    #filtereddict = [x for x in b if x['currency'] == Coin]
    # print("GetHitBTCCoinBalance: "+str(filtereddict))
    # return b[0]['available']

def TransferToTradingAccount(Coin):
    print("TransferToTradingAccount...")

    session = requests.session()
    session.auth = ("2575dd3ea4440d03a17a14c1a9d0bf61", "cbc6566aca1e16a3a57bdd0dd87ad7d8")
    qty = GetHitBTCAccountCoinBalance(Coin)
    print(qty)
    orderData = {'currency':Coin, 'amount': qty, 'type': 'bankToExchange'}
    r = session.post('https://api.hitbtc.com/api/2/account/transfer', data = orderData)
    print("TransferToTradingAccount: "+str(r.json()))


    #filtereddict = [x for x in b if x['currency'] == Coin]
    # print("GetHitBTCCoinBalance: "+str(filtereddict))
    # return b[0]['available']

def DownloadStepSizesOnHitBTC():
    print("GetHitBTCCoinStatus...")

    session = requests.session()
    session.auth = ("publicKey", "secretKey")

    session = requests.session()
    session.auth = ("", "")
    data = session.get('https://api.hitbtc.com/api/2/public/symbol').json()

    Symbols = []
    Stepsizes = []
    print(len(data))
    for i in range(len(data)):
        Symbols.append(data[i]['id'])
        print(float(data[i]['quantityIncrement']))
        try:
            Stepsizes.append(float(data[i]['quantityIncrement']))
        except Exception,e:
            Stepsizes.append(0)


    StepSizes = pd.DataFrame(columns=['A'])
    StepSizes = StepSizes.drop(['A'], axis=1)

    StepSizes['symbol'] = Symbols
    StepSizes['step'] = Stepsizes

    print(StepSizes)
    import pickle

    StepSizes.to_pickle('StepSizesOnHitBTC.db')

def GetStepSizeOnHitBTC(Coin):
    df = pd.read_pickle('StepSizesOnHitBTC.db')

    df = df[(df['symbol'] == Coin)]

    return float(df.head(1)['step'].values[0])

def TransferToBank(Coin,qty):
    print("TransferToTradingAccount...")

    session = requests.session()
    session.auth = ("2575dd3ea4440d03a17a14c1a9d0bf61", "cbc6566aca1e16a3a57bdd0dd87ad7d8")
    print(qty)
    orderData = {'currency':Coin, 'amount': qty, 'type': 'exchangeToBank'}
    r = session.post('https://api.hitbtc.com/api/2/account/transfer', data = orderData)
    print("TransferToTradingAccount: "+str(r.json()))


    #filtereddict = [x for x in b if x['currency'] == Coin]
    # print("GetHitBTCCoinBalance: "+str(filtereddict))
    # return b[0]['available']

def GetHitBTCWithdrawalFee(Coin):
    print("GetHitBTCCoinStatus...")

    session = requests.session()
    session.auth = ("publicKey", "secretKey")

    session = requests.session()
    session.auth = ("", "")
    b = session.get('https://api.hitbtc.com/api/2/public/currency').json()

    filtereddict = [x for x in b if x['id'] == Coin]
    return float(filtereddict[0]['payoutFee'])

"Trading Mechanisms"

def InitiateOnHitBTC(Pair,Price,address):
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]

    BuyOnHitBTC(Pair,Price)
    TransferToBank(Coin1,GetHitBTCCoinBalance(Coin1))
    WithdrawFromHitBTC(Coin1,"Purchase",address, "")

def CloseOnHitBTC(Pair,Price,address):
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]

    A = GetHitBTCCoinBalance(Coin2)
    SellOnHitBTC(Pair,Price)
    time.sleep(10)
    B = GetHitBTCCoinBalance(Coin2)
    TransferToBank(Coin2,B-A)
    WithdrawFromHitBTC(Coin2,"Sale",address,(B-A))
