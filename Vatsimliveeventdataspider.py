import requests
from datetime import datetime
import time

def getAirports(event):
    ports = []
    for port in event["airports"]:
        ports.append(port["icao"])
    return ports

def loop_event_data(data):
    now = datetime.now()
    epoch = str(int(now.timestamp()))

    events_memory = []
    events_now = {}

    is_event = []
    no_event = []

    for event in data:
        if event["organisers"][0]["division"] == "EUD": #Event in VATUED
           
            #Safe vateud event in memory
            events_memory.append(event)


            #Check if active
            start = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ")
            end = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if now < end: #now > start and now < end
                print("Active %s" % (event["name"])) 
                if event["type"] == "Event":
                    is_event.extend(getAirports(event))
                else:
                    no_event.extend(getAirports(event))
                
    
    tmp = {"1" : is_event,
            "0" : no_event}

    events_now[epoch] = tmp
    print(str(events_now))
    return events_memory, str(events_now)


while True:                
    time.sleep(5)
    try:
        #Get events from website
        url = "https://my.vatsim.net/api/v1/events/all"
        data = requests.get(url).json()["data"]
        vateud_events,events_now = loop_event_data(data)
    
    except Exception as e: #url uncallable
        print(e)
        #Get events from memory
        vateud_events,events_now = loop_event_data(vateud_events)
        print()
    
    finally:
        print()



    



