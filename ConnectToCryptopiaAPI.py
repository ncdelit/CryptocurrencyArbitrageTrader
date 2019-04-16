import time
import hmac
import urllib
import requests
import hashlib
import base64
import sys
import json
import sys, os
import traceback
import pandas as pd

API_KEY = ''
API_SECRET = ''

"Core Trading Functions"

def GetBidPriceOnCryptopia(Coin):
    Price = 0
    try:
        url = 'https://www.cryptopia.co.nz/api/GetMarket/'+Coin+'_'+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        Price = data4['Data']['BidPrice']
    except Exception,e:
        traceback.print_exc()
        GetBidPriceOnCryptopia(Coin)

    return float(Price)

def GetAskPriceOnCryptopia(Coin):
    Price = 0
    try:
        url = 'https://www.cryptopia.co.nz/api/GetMarket/'+Coin+'_'+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())

        Price = data4['Data']['AskPrice']
    except Exception,e:
        traceback.print_exc()
        GetAskPriceOnCryptopia(Coin)

    return float(Price)

def GetSellOrderBookOnCryptopia(Coin):
    df = pd.DataFrame()
    try:
        url = "https://www.cryptopia.co.nz/api/GetMarketOrders/"+Coin+'_'+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['Data']['Buy'], orient='columns')
        df.rename(columns={'Volume': 'Qty'}, inplace=True)
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetSellOrderBookOnCryptopia(Coin)
    return df

def GetBuyOrderBookOnCryptopia(Coin):
    df = pd.DataFrame()
    try:
        url = "https://www.cryptopia.co.nz/api/GetMarketOrders/"+Coin+'_'+'BTC'
        response = urllib.urlopen(url)
        data4 = json.loads(response.read())
        df = pd.DataFrame.from_dict(data4['Data']['Sell'], orient='columns')
        df.rename(columns={'Volume': 'Qty'}, inplace=True)
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetBuyOrderBookOnCryptopia(Coin)
    return df

def GetSellOrderBookVolumeOnCryptopia(Coin,SellingPrice):
    OrderBookVolume2 = 0
    OB = pd.DataFrame()
    try:
        OB = GetSellOrderBookOnCryptopia(Coin)
        OB = OB[(OB['Price']>=SellingPrice)]
        OrderBookVolume2 = OB["Total"].sum()
    except Exception,e:
        traceback.print_exc()
        time.sleep(15)
        GetSellOrderBookVolumeOnCryptopia(Coin,SellingPrice)
    return OrderBookVolume2

def PopulateCryptopiaPriceList():
    try:
        global control
        url = 'https://www.cryptopia.co.nz/api/GetMarkets'
        response = urllib.urlopen(url)
        data = json.loads(response.read())

        url2 = 'https://www.cryptopia.co.nz/api/GetCurrencies'
        response2 = urllib.urlopen(url2)
        data2 = json.loads(response2.read())

        markets3 = []
        markets4 = []
        asks3 = []
        bids3 = []
        statuses = []
        for i in range(len(data['Data'])):
            temp = ""
            try:
                coin1 = data['Data'][i]['Label'].split("/",1)[0]
                coin2 = data['Data'][i]['Label'].split("/",1)[1]
                if (coin1 == 'VMR' or coin1 == 'CMT' or coin2 == 'USDT' or coin1 == 'GBYTE' or coin1 == 'BTG'):
                    continue
                for b in range(len(data2['Data'])):
                    if (str(data2['Data'][b]['Symbol']) == coin1):
                        if(str(data2['Data'][b]['Status']) == 'Maintenance'):
                            temp = "True"
                            break
                if temp == "True":
                    continue
                markets3.append(coin1 + coin2)
                markets4.append(coin1 +"-"+ coin2)
                asks3.append(float(data['Data'][i]['AskPrice']))
                bids3.append(float(data['Data'][i]['BidPrice']))
            except Exception,e:
                print("Error in Populating Cryptopia Prices:" + str(e))
                markets3.append(str(data['Data'][i]['Label']))
                asks3.append(0)
                bids3.append(0)
    except Exception, e:
        print("Error in Cryptopia price population:" + str(e))
        time.sleep(5)
        control = True

    CryptopiaPriceList = pd.DataFrame(columns=['A'])
    CryptopiaPriceList = CryptopiaPriceList.drop(['A'], axis=1)

    CryptopiaPriceList['symbol'] =markets4
    CryptopiaPriceList['symbol2'] =markets4
    CryptopiaPriceList['CryptopiaAskPrice'] = asks3
    CryptopiaPriceList['CryptopiaBidPrice'] = bids3

    return CryptopiaPriceList

def GetCryptopiaCoinBalance(Coin):
     print("GetCryptopiaCoinBalance...")
     method = "GetBalance"
     req = {'Currency':Coin}
     url = "https://www.cryptopia.co.nz/Api/" + method
     nonce = str( int( time.time() ) )
     post_data = json.dumps(req);
     m = hashlib.md5()
     m.update(post_data)
     requestContentBase64String = base64.b64encode(m.digest())
     signature = API_KEY + "POST" + urllib.quote_plus( url ).lower() + nonce + requestContentBase64String
     hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature, hashlib.sha256).digest())
     header_value = "amx " + API_KEY + ":" + hmacsignature + ":" + nonce
     headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
     try:
         r = requests.post( url, data = post_data, headers = headers )
         data = r.json()
         #print("GetCryptopiaCoinBalance: " + str(data))

         Bal = data['Data'][0]["Available"]
         print(Bal)
         if (False == data['Success'] or None is data['Data'][0]["Available"] or 'None' in str(data['Data'][0]["Available"]) or str(data['Data'][0]["Available"]) ==''):
             #print("in the none")
             GetCryptopiaCoinBalance(Coin)
         else:
            #print(Bal)
            return Bal
                #print("Success in GetCryptopiaCoinBalance")

     except Exception,e:
         #print("Error in GetCryptopiaCoinBalance: " + str(e))
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         #print(exc_type, fname, exc_tb.tb_lineno)
         time.sleep(5)
         GetCryptopiaCoinBalance(Coin)

     #print(data)

def BuyOnCryptopia(Pair,Price,QtyForPurchase):
    print("BuyOnCryptopia...")
    Coin2 = Pair.split("-",1)[1]
    #print(Coin2)
    Coin1 = Pair.split("-",1)[0]

    ForCryptopia = Coin1 + "/" + Coin2
    method = "SubmitTrade"
    req = {'Market':ForCryptopia,'Type':'Buy','Rate':Price,'Amount':QtyForPurchase}
    url = "https://www.cryptopia.co.nz/Api/" + method
    nonce = str( int( time.time() ) )
    post_data = json.dumps(req);
    m = hashlib.md5()
    m.update(post_data)
    requestContentBase64String = base64.b64encode(m.digest())
    signature = API_KEY + "POST" + urllib.quote_plus( url ).lower() + nonce + requestContentBase64String
    hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature, hashlib.sha256).digest())
    header_value = "amx " + API_KEY + ":" + hmacsignature + ":" + nonce
    headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
    r = requests.post( url, data = post_data, headers = headers )

    try:
        data = r.json()
        print("BuyOnCryptopia: " + str(data))
        if ("False" or "false") in data:
            return "Failed"

        #return str(data['Data']["OrderId"])
    except Exception,e:
        print("Error in BuyOnCryptopia" + str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        time.sleep(5)
        BuyOnCryptopia(Pair,Price,QtyForPurchase)

def SellOnCryptopia(Pair,Price):
    print("SellOnCryptopia...")
    Coin2 = Pair.split("-",1)[1]
    #print(Coin2)
    Coin1 = Pair.split("-",1)[0]

    wait = GetCryptopiaCoinBalance(Coin1)
    while wait < 0.05 or wait == 'None':
        time.sleep(3*1)
        wait = GetCryptopiaCoinBalance(Coin1)
        print(wait)
        time.sleep(30*1)
    ForCryptopia = Coin1 + "/" + Coin2
    method = "SubmitTrade"
    req = {'Market':ForCryptopia,'Type':'Sell','Rate':Price,'Amount':wait}
    url = "https://www.cryptopia.co.nz/Api/" + method
    nonce = str( int( time.time() ) )
    post_data = json.dumps(req);
    m = hashlib.md5()
    m.update(post_data)
    requestContentBase64String = base64.b64encode(m.digest())
    signature = API_KEY + "POST" + urllib.quote_plus( url ).lower() + nonce + requestContentBase64String
    hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature, hashlib.sha256).digest())
    header_value = "amx " + API_KEY + ":" + hmacsignature + ":" + nonce
    headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }

    try:
        r = requests.post(url, data = post_data, headers = headers )


        data = r.json()
        print("SellOnCryptopia: " + str(data))

        if (False == data['Success']):
            SellOnCryptopia(Pair,Price)
    except Exception,e:
         print("Error in SellOnCryptopia" + str(e))
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         print(exc_type, fname, exc_tb.tb_lineno)
         time.sleep(5)
         SellOnCryptopia(Pair,Price)

def WithdrawFromCryptopia(Coin,SaleOrPurchase,Address,Qty,QtyForPurchase):
    print("WithdrawFromCryptopia...")
    wait = GetCryptopiaCoinBalance(Coin)
    counter = 0
    if SaleOrPurchase == 'Purchase':
        while wait < 0.99*QtyForPurchase:
            counter = counter + 1
            print(counter)
            if counter >= 4:
                return "Took too long to buy"
            time.sleep(2*1)
            wait = GetCryptopiaCoinBalance(Coin)
            time.sleep(29*1)
    else:
        while wait < 0.75*Qty:
            counter = counter + 1
            if counter >= 30:
                pass
            wait = GetCryptopiaCoinBalance(Coin)
            time.sleep(30*1)

    method = "SubmitWithdraw"
    if SaleOrPurchase == 'Purchase':
        req = {'Currency':Coin,'Address':Address,'Amount':wait}
    else:
        req = {'Currency':Coin,'Address':Address,'Amount':Qty}

    url = "https://www.cryptopia.co.nz/Api/" + method
    nonce = str( int( time.time() ) )
    post_data = json.dumps(req);
    m = hashlib.md5()
    m.update(post_data)
    requestContentBase64String = base64.b64encode(m.digest())
    signature = API_KEY + "POST" + urllib.quote_plus( url ).lower() + nonce + requestContentBase64String
    hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature, hashlib.sha256).digest())
    header_value = "amx " + API_KEY + ":" + hmacsignature + ":" + nonce
    headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
    r = requests.post( url, data = post_data, headers = headers )
    print(req)
    try:
        data = r.json()
        print("WithdrawFromCryptopia: " + str(data))
        # if ("False" or "false") in data['Success']:
        #     WithdrawFromCryptopia(Coin,SaleOrPurchase,Address,Qty,QtyForPurchase)
    except Exception,e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("Error in WithdrawFromCryptopia" + str(e))
        print(exc_type, fname, exc_tb.tb_lineno)
        time.sleep(5)
        WithdrawFromCryptopia(Coin,SaleOrPurchase,Address,Qty,QtyForPurchase)

def GetCryptopiaAddress(Coin):
    print("GetCryptopiaAddress...")
    method = "GetDepositAddress"

    req = {'Currency':Coin}


    url = "https://www.cryptopia.co.nz/Api/" + method
    nonce = str( int( time.time() ) )
    post_data = json.dumps(req);
    m = hashlib.md5()
    m.update(post_data)
    requestContentBase64String = base64.b64encode(m.digest())
    signature = API_KEY + "POST" + urllib.quote_plus( url ).lower() + nonce + requestContentBase64String
    hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature, hashlib.sha256).digest())
    header_value = "amx " + API_KEY + ":" + hmacsignature + ":" + nonce
    headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
    r = requests.post( url, data = post_data, headers = headers )

    try:
        data = r.json()
        print("GetCryptopiaAddress: " + str(data))
        return str(data['Data']["Address"])
    except Exception,e:
       print("Error in GetCryptopiaAddress" + str(e))
       exc_type, exc_obj, exc_tb = sys.exc_info()
       fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
       print(exc_type, fname, exc_tb.tb_lineno)
       time.sleep(5)
       GetCryptopiaAddress(Coin)

def GetCryptopiaQtyForTrade(Pair,Price):
    Coin2 = Pair.split("-",1)[1]
    #print(Coin2)
    Coin1 = Pair.split("-",1)[0]
    return (0.95*GetCryptopiaCoinBalance(Coin2))/Price

def CancelTradeOnCryptopia ():
    print("CancelTradeOnCryptopia...")
    method = "CancelTrade"

    req = {'Type':'All'}

    url = "https://www.cryptopia.co.nz/Api/" + method
    nonce = str( int( time.time() ) )
    post_data = json.dumps(req);
    m = hashlib.md5()
    m.update(post_data)
    requestContentBase64String = base64.b64encode(m.digest())
    signature = API_KEY + "POST" + urllib.quote_plus( url ).lower() + nonce + requestContentBase64String
    hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature, hashlib.sha256).digest())
    header_value = "amx " + API_KEY + ":" + hmacsignature + ":" + nonce
    headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
    r = requests.post( url, data = post_data, headers = headers )

    try:
        data = r.json()
        print("CancelTradeOnCryptopia: " + str(data))

        if (False == data['Success']):
            CancelTradeOnCryptopia ()
    except Exception,e:
       print("Error in CancelTradeOnCryptopia" + str(e))
       exc_type, exc_obj, exc_tb = sys.exc_info()
       fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
       print(exc_type, fname, exc_tb.tb_lineno)
       time.sleep(5)
       CancelTradeOnCryptopia ()

def GetCryptopiaCoinBalanceForUnsettledTrade(Coin):
     print("GetCryptopiaCoinBalance...")
     method = "GetBalance"
     req = {'Currency':Coin}
     url = "https://www.cryptopia.co.nz/Api/" + method
     nonce = str( int( time.time() ) )
     post_data = json.dumps(req);
     m = hashlib.md5()
     m.update(post_data)
     requestContentBase64String = base64.b64encode(m.digest())
     signature = API_KEY + "POST" + urllib.quote_plus( url ).lower() + nonce + requestContentBase64String
     hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature, hashlib.sha256).digest())
     header_value = "amx " + API_KEY + ":" + hmacsignature + ":" + nonce
     headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
     r = requests.post( url, data = post_data, headers = headers )

     try:
         data = r.json()
         print("GetCryptopiaCoinBalance: " + str(data))
         if (None == float(data['Data'][0]["Total"])):
             if(data['Data'][0]["Total"] == 'No balance found'):
                 return 0
             GetCryptopiaCoinBalanceForUnsettledTrade(Coin)
         else:
             #print(float(data['Data'][0]["Available"]))
             return float(data['Data'][0]["Total"])
             #print("Success in GetCryptopiaCoinBalance")

     except Exception,e:
         print("Error in GetCryptopiaCoinBalance: " + str(e))
         exc_type, exc_obj, exc_tb = sys.exc_info()
         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
         print(exc_type, fname, exc_tb.tb_lineno)
         time.sleep(5)
         GetCryptopiaCoinBalanceForUnsettledTrade(Coin)

     #print(data)

"Trading Mechanisms"

def InitiateOnCryptopia(Pair,Price,address):
    global control
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]
    cont = False
    QtyForPurchase = GetCryptopiaQtyForTrade(Pair,Price)
    time.sleep(3*1)
    if BuyOnCryptopia(Pair,Price,QtyForPurchase) == 'Failed':
        control = True
        return control
    time.sleep(5*1)
    if WithdrawFromCryptopia(Coin1,"Purchase",address,"",QtyForPurchase) == "Took too long to buy":
        CancelTradeOnCryptopia()
        if GetCryptopiaCoinBalance(Coin1) < 0.5:
            control = True
            return control
        else:
            WithdrawFromCryptopia(Coin1,"Purchase",address,"",QtyForPurchase)

def CloseOnCryptopia(Pair,Price,address):
    incre = 0.15/100
    PriceAdj = 1+(incre)
    PriceAdj2 = 1-(incre)

    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]

    A = GetCryptopiaCoinBalance(Coin2)
    C = 1
    counter = 1
    while C > 0.5:
        counter = counter + 1
        SellOnCryptopia(Pair,Price*PriceAdj2)
        time.sleep(15)
        C = GetCryptopiaCoinBalanceForUnsettledTrade(Coin1)
        print(C)
        if (C >0.5):
            CancelTradeOnCryptopia()
            incre = incre*(counter/2)
            PriceAdj2 = 1-(incre)
    B = GetCryptopiaCoinBalance(Coin2)
    WithdrawFromCryptopia(Coin2,"Sale",address,B-A,"")
