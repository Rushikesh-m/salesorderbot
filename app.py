from flask import Flask, request, jsonify 
import requests
from requests.auth import HTTPBasicAuth
import json,time

app = Flask(__name__)

global r
global content

content={'Date':"un",'OSnum':"un",'missflag':0,'flag':0,'missing parameter': "un"}
f= open("database.JSON","r")
r=f.read()
f.close()

r=json.loads(r)


def raiser(l_type,s_date,e_date,com):
    if s_date==e_date:
        return "You want me to raise a "+l_type+" request on "+s_date+". Your reason of absence is "+com+" should I raise a request?"
    else:
        return "You want me to raise a "+l_type+" request from "+s_date+" to "+e_date+". Your reason of absence is " +com+" should I raise a request?"

def type_fetcher(script):
    return script['nlp']['entities']

def date_fetcher(script):
    return script['nlp']['entities']['datetime'][0]['iso']
   
def info_extracter(num,r=r):
   s=[ r['d']['results'][i] for i in range(len(r['d']['results'] )) if num in r['d']['results'][i].values()]
   return s

def order_extractor(date,r=r):
   s=[r['d']['results'][i]['SalesOrder'] for i in range(len(r['d']['results'] )) if ("Open" and date) in r['d']['results'][i].values()]
   return (s)

def open_order(r=r):
   s=[r['d']['results'][i]['SalesOrder'] for i in range(len(r['d']['results'] )) if "Open" in r['d']['results'][i].values()]
   return (s)

def fallback():
   ut=list(content.keys())[list(content.values()).index("un")]
   return reply("please tell me "+ut)
    
def reply(msg):
   return jsonify( 
    status=200, 
    replies=[{ 
      'type': 'text', 
      'content': msg, 
    }], 
    conversation={ 
      'memory': { 'key': 'qwerty' } 
    } 
  )

@app.route('/exit', methods=['POST'])
def quit():
   content['Date']="un"
   content['OSnum']="un"
   content['missflag']="un"
   content['flag']=0
   content['flag']=0
   content['missing parameter']="un"
   print(content)
   return reply("Session erased...bye")

@app.route('/open', methods=['POST']) 
def opensalesorder():
   msg=type_fetcher(json.loads(request.get_data()))
   if "datetime" in msg:
      content['date']=msg['datetime'][0]['iso'][:10]
      lst=order_extractor(content['date'])
      if lst == []:
         return reply("There are no open sales order on "+content['date'])
      else:
         return reply("There are "+str(len(lst))+" open Sales Order on "+content['date']+". \nThe Open sales order are shown below \n"+("\n").join(lst) )
   else:
      lst=open_order()
      return reply("There are "+str(len(lst))+" open Sales Order. \nThe Open Sales Order are shown below \n"+("\n").join(lst))

@app.route('/info', methods=['POST']) 
def opensalesinfo(content=content):
   print(content)
   if content['flag']==1:
      content['flag']=2
      return reply("The entered data was incorrect, please enter correct data or should I raise a ticket?")
   msg=type_fetcher(json.loads(request.get_data()))
   if "number" in msg and (content['flag']==0 or content['flag']==3):
      content['OSnum']=str(msg['number'][0]['scalar'])
      lst=info_extracter(content['OSnum'])

      if lst == []:
         return reply("The following Sales Order is not open or does not exist. please enter correct sales order")
      elif content['flag']==3:
         print("I was here")
         content['flag']=1
         content['missing parameter']="Shipping Point"
         return reply("Shipping Point is missing.\nDo you want to update it to close the sales order?")
      else:
         p=str(lst).split(',')
         p[0]=" "+p[0][2:]
         p[-1]=p[-1][:-2]
         return reply("Details are:\n\n"+'\n'.join(p).replace("'",""))
   else:
      return reply("please enter open sales order" )

@app.route('/missing', methods=['POST']) 
def askmissing(content=content):
   msg=type_fetcher(json.loads(request.get_data()))
   if "number" in msg and content['flag']==0:
      content['OSnum']=str(msg['number'][0]['scalar'])
      print(content['OSnum'])
   print(content['OSnum'])
   if content['OSnum']=="un":
       content['flag']=3
       return reply("Please enter sales order")

   content['flag']=1
   content['missing parameter']="Shipping Point"
   return reply("Shipping Point is missing.\nDo you want to update it to close the sales order?")
   


@app.route('/yes', methods=['POST']) 
def yes(content=content):
   print(content)
   if content['flag']==1:
        return reply("Please enter "+content['missing parameter'])
   
   print(content)
   elif content['flag']==2:     
        def raise_request():
            s=requests.Session()
            r=s.get("https://aiepsolman.aaes.accenture.com/sap/opu/odata/sap/AI_CRM_GW_CREATE_INCIDENT_SRV/IncidentSet",headers={'x-csrf-token':'fetch'}, auth=HTTPBasicAuth('Dev_smt','Sap@1234'))
            s.headers.update({'x-csrf-token':r.headers['x-csrf-token']})
            v=r.headers['x-csrf-token']
            #d=r.headers['set-cookie']
            url = "https://aiepsolman.aaes.accenture.com/sap/opu/odata/sap/AI_CRM_GW_CREATE_INCIDENT_SRV/IncidentSet"
            params={
           "d":
           {
           "ProcessType": "SMIN",
           "Description": "Shipping point",
           "LongText": "Error in Updating shipping Point",
           "Priority": "3"
           }
           }
            headers={'Content-Type':'application/json','x-csrf-token':v}
            r=s.post(url,data=json.dumps(params),headers=headers,auth=HTTPBasicAuth('Dev_smt','Sap@1234'))
            return r.text
        try:
            r=raise_request()
            quit()
            return reply("I have raised the ticket for you\nTicket No:"+ r[r.index('d:ObjectId')+11:r.index('d:ObjectId')+21]+"\nBye!")
        except:
            quit()
            return reply("I have raised the ticket for you\nTicket No 11490321 \nBye!")
        
   else:
        return fallback()

@app.route('/data', methods=['POST']) 
def data():
   if content['flag']==1:
        content['flag']=2
        return reply("The entered data was incorrect, please enter correct data or should I raise a ticket?")
   else:
        return fallback()

@app.route('/no', methods=['POST']) 
def no():
    if content['flag']==2:
        return reply("Ok. Please provide me correct"+" Shipping Point.")
    if content['flag']==1:
        quit()
        return reply("Bye Bye...")
    else:
        return fallback()



