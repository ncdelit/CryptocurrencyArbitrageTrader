import urllib, json
import pandas as pd
import numpy as np
import re
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+
from urllib import urlretrieve
import urllib
import time
# from ConnectToKuCoinAPI import BuyOnKuCoin
# from ConnectToKuCoinAPI import GetAccountBalance
# from ConnectToKuCoinAPI import WithdrawCoin
from ConnectToBinanceAPI import *
from ConnectToBittrexAPI import *
from ConnectToCryptopiaAPI import *
from ConnectToHitBTCAPI import *
import sys, os
import traceback
from collections import defaultdict
import smtplib

CumulativeInvestment = 10
BTCMin = 0 #0.00334519  #around 30 dollars
ETHMin = 0 #0.06602400 #around 30 dollars
DiffMin = 15

tradecounter = 0
tradecounterWait = 0

def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

def condition(value):
    if value>1000:
        return 0
    return value

def SendEmail(Subject,Body):
    fromaddr = ''
    toaddrs  = ''
    msg = 'Subject: {}\n\n{}'.format(Subject, Body)
    username = ''
    password = ''
    server = smtplib.SMTP('smtp.gmail.com:587')
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()

while True: #alt... while True:
    control = False
    print("...")
    incre = 0.15/100
    PriceAdj = 1+(incre)
    PriceAdj2 = 1-(incre)
    time.sleep(5)
    if tradecounter != tradecounterWait:
        time.sleep(60*30)
        tradecounterWait = tradecounterWait + 1
        TransferToTradingAccount('BTC')
        break

    Exchanges = []
    Exchanges.append("Binance")
    Exchanges.append("Bittrex")
    Exchanges.append("Cryptopia")
    Exchanges.append("HitBTC")

    try:
        BinancePriceList = locals()["Populate"+Exchanges[0]+"PriceList"]()
        BittrexPriceList = locals()["Populate"+Exchanges[1]+"PriceList"]()
        CryptopiaPriceList = locals()["Populate"+Exchanges[2]+"PriceList"]()
        HitBTCPriceList = locals()["Populate"+Exchanges[3]+"PriceList"]()
    except Exception, e:
        print(str(e))
        continue

    "Remove any ETH Pairs"
    Regex = "[a-zA-Z0-9]*ETH"
    BinancePriceList['ETH'] = BinancePriceList.symbol.str.contains(Regex)
    BittrexPriceList['ETH'] = BittrexPriceList.symbol.str.contains(Regex)
    CryptopiaPriceList['ETH'] = CryptopiaPriceList.symbol.str.contains(Regex)
    HitBTCPriceList['ETH'] = HitBTCPriceList.symbol.str.contains(Regex)

    BinancePriceList = BinancePriceList[(BinancePriceList['ETH']==False)]
    BittrexPriceList = BittrexPriceList[(BittrexPriceList['ETH']==False)]
    CryptopiaPriceList = CryptopiaPriceList[(CryptopiaPriceList['ETH']==False)]
    HitBTCPriceList = HitBTCPriceList[(HitBTCPriceList['ETH']==False)]

    Directions = []
    Exchange1 = []
    Exchange2 = []
    Differences= []
    Methods1 = []
    Methods2 =[]
    Thresholds = []

    # for i in range(len(Exchanges)):
    #     for x in range(len(Exchanges)):
    #         if (Exchanges[i] != Exchanges[x]):
    #             Directions.append(Exchanges[i] + str("To") + Exchanges[x])
    #             Exchange1.append(Exchanges[i])
    #             Exchange2.append(Exchanges[x])

    d = {}
    for i in range(len(Exchanges)):
        for b in range(len(Exchanges)-1):
            if ((Exchanges[b+1] +"&"+ Exchanges[i] not in d)):
                if((Exchanges[b+1]!=Exchanges[i])):
                    d[Exchanges[i] +"&"+ Exchanges[b+1]] = pd.merge(locals()[Exchanges[i]+"PriceList"],locals()[Exchanges[b+1]+"PriceList"], on='symbol2', how='inner')

    differences = pd.DataFrame(columns=['A'])
    differences = differences.drop(['A'], axis=1)
    for table in d:
        FirstExchange = table[:table.find("&")]
        SecondExchange = table[table.find("&")+1:len(table)]

        Directions.append(FirstExchange + str("To") + SecondExchange)
        Directions.append(SecondExchange + str("To") + FirstExchange)
        if "HitBTC" in FirstExchange or "HitBTC" in SecondExchange:
            Thresholds.append(17.5)
            Thresholds.append(17.5)
        else:
            Thresholds.append(7.5)
            Thresholds.append(7.5)
        Exchange1.append(FirstExchange)
        Exchange2.append(SecondExchange)
        Exchange1.append(SecondExchange)
        Exchange2.append(FirstExchange)

        d[table][FirstExchange + "To" +SecondExchange+"Difference"] = ((d[table][SecondExchange+'BidPrice'] -d[table][FirstExchange+'AskPrice'])/(d[table][FirstExchange+'AskPrice']))*100

        d[table][FirstExchange + "To" +SecondExchange+"Difference"] = d[table][FirstExchange + "To" +SecondExchange+"Difference"].apply(condition)

        d[table][SecondExchange + "To" +FirstExchange+"Difference"] = ((d[table][FirstExchange+'BidPrice'] -d[table][SecondExchange+'AskPrice'])/(d[table][SecondExchange+'AskPrice']))*100


        d[table][SecondExchange + "To" +FirstExchange+"Difference"] = d[table][SecondExchange + "To" +FirstExchange+"Difference"].apply(condition)

        try:
            max1 = max(d[table][FirstExchange + "To" +SecondExchange+"Difference"])
            max2 = max(d[table][SecondExchange + "To" +FirstExchange+"Difference"])
        except Exception,e:
            print("Error in Max Determinination: "+str(e))
            continue

        FirstRow1 = d[table][(d[table][FirstExchange + "To" +SecondExchange+"Difference"]==max1)]

        FirstRow2 = d[table][(d[table][SecondExchange + "To" +FirstExchange+"Difference"]==max2)]

        differences = differences.append(FirstRow1,ignore_index=True)
        differences = differences.append(FirstRow2,ignore_index=True)

    NumberOfDirections = len(Exchanges)*(len(Exchanges)-1)

    Pairs = []
    PurchasePrices = []
    SellingPrices = []
    try:
        for i in range(len(Directions)):
            Differences.append(differences.loc[[i]][Directions[i]+"Difference"].values[0])
            Pairs.append(differences.loc[[i]]['symbol2'].values[0])
            PurchasePrices.append(differences.loc[[i]][Exchange1[i]+'AskPrice'].values[0])
            SellingPrices.append(differences.loc[[i]][Exchange2[i]+'BidPrice'].values[0])
    except Exception,e:
        print("Error in Price population: "+str(e))
        continue

    for i in range(len(Directions)):
        Methods1.append("InitiateOn" +Exchange1[i])
        Methods2.append("CloseOn"+ Exchange2[i])

    PriceDifferencesTable = pd.DataFrame(columns=['A'])
    PriceDifferencesTable = PriceDifferencesTable.drop(['A'], axis=1)

    PriceDifferencesTable['Direction'] = Directions
    PriceDifferencesTable['Exchange1'] = Exchange1
    PriceDifferencesTable['Exchange2'] = Exchange2
    PriceDifferencesTable['Difference'] = Differences
    PriceDifferencesTable['Initiation'] = Methods1
    PriceDifferencesTable['Closing'] = Methods2
    PriceDifferencesTable['Pair'] = Pairs
    PriceDifferencesTable['PurchasePrice'] = PurchasePrices
    PriceDifferencesTable['SellingPrice'] = SellingPrices
    PriceDifferencesTable['Treshold'] = Thresholds
    PriceDifferencesTable['Net Profit'] = PriceDifferencesTable['Difference']- PriceDifferencesTable['Treshold']

    #Turn off exchange where we don't have seed money yet
    PriceDifferencesTable = PriceDifferencesTable[(PriceDifferencesTable['Exchange1']!='Binance') & (PriceDifferencesTable['Exchange1']!='Bittrex')]

    PriceDifferencesTable= PriceDifferencesTable.sort_values(by=['Net Profit'],ascending=False)

    #if (PriceDifferencesTable.head(1)['Difference'].values[0]>=15):
        #SendEmail("Price difference greater than 15% found")

    #print("Difference: "+str(PriceDifferencesTable.head(1)['Difference'].values[0]))
    print(str(PriceDifferencesTable.head(1)['Net Profit'].values[0]))

    if (PriceDifferencesTable.head(1)['Net Profit'].values[0]<=0):
        continue

    print(PriceDifferencesTable)

    "Parameters"
    Pair = PriceDifferencesTable.head(1)['Pair'].values[0]
    Coin1 = Pair.split("-",1)[0]
    Coin2 = Pair.split("-",1)[1]
    PurchasePrice = PriceDifferencesTable.head(1)['PurchasePrice'].values[0]
    SellingPrice = PriceDifferencesTable.head(1)['SellingPrice'].values[0]
    SellingExchange = PriceDifferencesTable.head(1)['Exchange2'].values[0]
    PurchasingExchange = PriceDifferencesTable.head(1)['Exchange1'].values[0]
    address1 = locals()["Get"+SellingExchange+"Address"](Coin1)
    address2 = locals()["Get"+PurchasingExchange+"Address"](Coin2)

    "Begin Trading"
    Initiate = locals()[PriceDifferencesTable.head(1)['Initiation'].values[0]]

    Initiate(Pair,PurchasePrice,address1)
    if control == True:
        continue

    Close = locals()[PriceDifferencesTable.head(1)['Closing'].values[0]]
    Close(Pair,SellingPrice,address2)

    tradecounter = tradecounter + 1
    SendEmail("Bought "+str(Coin1)+" on " +str(PurchasingExchange) +" to sell on "+str(SellingExchange) +" for a price difference of "+str(PriceDifferencesTable.head(1)['Difference'].values[0])+"%",PriceDifferencesTable)

    time.sleep(60)
