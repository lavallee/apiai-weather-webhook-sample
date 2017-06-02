#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/')
def hello():
    return json.dumps(json.loads(TEMPLATE))


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    print("in processRequest")
    if req.get("result").get("action") != "weather":
        print("i don't know how to handle this action")
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    print("in makeYqlQuery")
    result = req.get("result")
    parameters = result.get("parameters")
    #city = parameters.get("geo-city")
    address = parameters.get("address")
    city = address.get("city")
    if city is None:
        return None

    print("city is '%s'" % city)

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


TEMPLATE = """
    {
   "status" : {
      "code" : 200,
      "errorType" : "success"
   },
   "lang" : "en",
   "id" : "955edd22-2610-4c87-a091-16d66a39b873",
   "timestamp" : "2017-06-02T21:43:12.974Z",
   "sessionId" : "4a565d68-f6a7-e798-cdcd-0cb44accb6a6",
   "result" : {
      "source" : "agent",
      "parameters" : {
         "address" : {
            "city" : "New York"
         },
         "unit" : "",
         "date-time" : ""
      },
      "action" : "weather",
      "speech" : "",
      "contexts" : [
         {
            "lifespan" : 2,
            "name" : "weather",
            "parameters" : {
               "date-time" : "",
               "address.original" : "new york",
               "unit" : "",
               "date-time.original" : "",
               "address" : {
                  "city" : "New York",
                  "city.original" : "new york"
               },
               "unit.original" : ""
            }
         }
      ],
      "metadata" : {
         "intentId" : "f1b75ecb-a35f-4a26-88fb-5a8049b92b02",
         "webhookUsed" : "true",
         "webhookForSlotFillingUsed" : "false",
         "intentName" : "weather"
      },
      "score" : 1,
      "actionIncomplete" : false,
      "fulfillment" : {
         "speech" : "",
         "messages" : [
            {
               "type" : 0,
               "speech" : ""
            }
         ]
      },
      "resolvedQuery" : "what's the weather in new york?"
   }
}
"""


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
