# the following code will listen for book/trade info from poloniex

from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import pymysql.cursors
#from dataFiller import dataFiller
from threading import Thread
from datetime import datetime, timedelta
from os import execv
from sys import argv, executable

# make sql server connections
conn = pymysql.connect(
        host = 'localhost',
        user = 'root',
        password = 'toor',
        db = 'poloDB')        
cursor = conn.cursor()

# theFiller = dataFiller()

class MyComponent(ApplicationSession):

    z = 0
    queue = {}
    calcList= []

    @inlineCallbacks
    def onJoin(self, details):
        print("session joined")
        
        def oncounter_books(*count, **kw):
	    #print('books')
	    
            #print ('--- MSG RECV\'D ---')
            #print ('\t' + str(kw['seq']))
            #print (str(count))
       	    #print(len(self.queue))
            
            self.execute_sql(count)

        try:
            yield self.subscribe(oncounter_books, u'BTC_ETH')
            print("subscribed to topic - tradeHistory")
	    #yield self.subscribe(oncounter_ticker, u'ticker')
            #print("subscribed to topic - ticker")

	    # preload calcList
	    self.syncCalcList()
        except Exception as e:
            print("could not subscribe to topic: " + str(e))
    
    def onLeave(self, details):
        print("--- onLeave --- " + str(details))
	execv(executable, ['python'] + argv)
        print('--- onLeave --- after execv()')
	

    def onDisconnect(self):
        print("--- onDisconnect --- restarting")
	execv(executable, ['python'] + argv)
   	print('--- onDisconnect --- after execv()')
	 
    def execute_sql(self, mess):
        # prepare sql statement
        for thing in mess:
        
            #print('\t\t' + '-'*5)
            #print(thing)
            #print(thing['data']) 

            if thing['type'] == 'orderBookModify': continue
            elif thing['type'] == 'orderBookRemove': continue
            elif thing['type'] == 'newTrade':
                # add this entry to order history table
                # print (thing)
                tradeID = thing['data']['tradeID']
                rate = thing['data']['rate']
                amount = thing['data']['amount']
		amount = float(amount)
                total = thing['data']['total']
                typ = thing['data']['type']
                dt = thing['data']['date']
		
		# add datetime,rate to calcList
		d = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
		self.calcList.append({'date': d, 'rate': rate, 'type': typ, 'amount': amount})

		# calculate fiveMin avg
		thirtyMinDiff = timedelta(0,1800)
		newList = [float(x['rate']) for x in self.calcList if x['date']>d-thirtyMinDiff]
		thirtyMinAvg = sum(newList)/len(newList)
		#print(len(newList))
		# calculate 1Hr avg
		oneHrDiff = timedelta(0,3600)
                newList = [float(x['rate']) for x in self.calcList if x['date']>d-oneHrDiff]
                #print(sum(newList))
		#print(len(newList))
		oneHrAvg = sum(newList)/len(newList)


                time_start = datetime.now()
		# calc macd
		macd = thirtyMinAvg - oneHrAvg

		# calc b/s
		fiveMinDiff = timedelta(0,1800)
		fiveMinList = [x for x in self.calcList if x['date']>d-fiveMinDiff]
		sells = 0
		buys = 0
		for item in fiveMinList:
			if item['type'] == 'sell': sells += item['amount']
			elif item['type'] == 'buy': buys += item['amount']
			else: print('---calc bs: invalid type---')
		# calc b/s ratio
		bsratio = float(buys-sells)/(buys+sells)		
		
		# accel
		if item['type'] == 'sell': accel = sells/30
		elif item['type'] == 'buy': accel = buys/30
		
		# keep calcList short
		limit = timedelta(0,3720)
		self.calcList = [x for x in self.calcList if x['date']>d-limit]
                time_stop = datetime.now()
                #print('--- execute_sql --- time it took to do calculations: ' + str(time_stop-time_start))

                time_start = datetime.now()
                qString = 'INSERT INTO tradeHistory (tradeID, rate, amount, total, type, poloDt, oneHr, thirtyMin, MACD, bsratio, accel) VALUES (%s, %s, %s, %s, "%s", "%s", %s, %s, %s, %s, %s)' % (tradeID, rate, amount, total, typ, dt, oneHrAvg, thirtyMinAvg, macd, bsratio, accel)
                #print(qString)
                time_stop = datetime.now()
                #print('--- execute_sql --- time it took to do INSERT INTO: ' + str(time_stop-time_start))
            else:
                print('poloBooks - recvd invalid type')
                exit()
	            
            # attempt to execute
            try:
                #print('\t\tEXECUTING -- ' + qString)
                cursor.execute(qString)
                conn.commit()
		# append data to dataFiller queue
		# if thing['type'] == 'newTrade':Thread(target=theFiller.queue.append, args=(thing['data'],)).start()
	    except Exception as e:
                print('SQL ERROR - ' + str(e))
                exit()


    # {date, rate, type, amount}
    def syncCalcList(self):
	# query data
	qString = 'SELECT UNIX_TIMESTAMP(poloDt),rate,type,amount FROM tradeHistory WHERE poloDt>date_add(now(), interval -3720 second)'
        try:
                # execute qString
                cursor.execute(qString)
                results = cursor.fetchall()
		conn.commit()
	except Exception as e:
		return 'Melting Down - ' + str(e)

	for thing in results:
		#print(thing)
		self.calcList.append({'date':datetime.fromtimestamp(thing[0]), 'rate':thing[1], 'type':thing[2], 'amount':thing[3]})		    

if __name__ == '__main__':
    try:
        runner = ApplicationRunner(url=u"wss://api.poloniex.com", realm=u"realm1")
        runner.run(MyComponent)
	print('--- main --- done ApplicationRunner.run()')
    finally:
	print('--- main --- finally:')
	conn.close()
    


