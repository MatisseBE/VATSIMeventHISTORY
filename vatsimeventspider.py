import json
import requests
from datetime import datetime
import time
import pandas as pd
from github import Github

def save(events, dic):
    try:
        events.to_csv('out.csv')
        print("Events saved")
    except:
        events.to_csv('out_excp.csv')

    try:
        with open('file.txt', 'w') as file:
            file.write(json.dumps(dic)) # use `json.loads` to do the reverse
        print("dictionary saved")
    except:
        events.to_csv('out2_excp.csv')
def toConvert(data):
    try:
        value_counts = data['airports'].value_counts()
        ranking = []
        for index, row in data.iterrows():
            airport = row["airports"]
            if airport not in [a_tuple[0] for a_tuple in ranking]:
                savings = value_counts[airport] * len(airport)
                ranking.append((airport,savings))

        ranking.sort(key=lambda x:x[1], reverse=True)
        ports = [a_tuple[0] for a_tuple in ranking][:10]
        return ports
    except Exception as e:
        print(e)
        print("Error in toConvert")
        return []
def doConversion(data):
    #data["airports"].replace(old_num_to_val, inplace=True)
    
    num_to_val = {}
    val_to_num = {}
    to_convert = toConvert(data)
    print("to convert", to_convert)

    for i in range(len(to_convert)):
        port = to_convert[i]
        num_to_val[str(i)] = port
        val_to_num[port] = str(i)
    try:
        data["airports"].replace(val_to_num, inplace=True)
    except:
        print("Didnt convert long strings to num")

    return data,num_to_val
def uploadtoGithub(data, name):
    with open("discordtoken.gitignore","r") as file:
        token = file.read()

    g = Github(token)

    repo = g.get_user().get_repo("VATSIMeventHISTORY")
    all_files = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))

    content = data

    # Upload to github
    git_file = name
    if git_file in all_files:
        contents = repo.get_contents(git_file)
        repo.update_file(contents.path, "committing files", content, contents.sha , branch="main")
        print(git_file + ' UPDATED ' + str(datetime.now()))
    else:
        repo.create_file(git_file, "committing files", content, branch="main")
        print(git_file + ' CREATED ' + str(datetime.now()))
def getHash(airports,start,end,kind):
    s = "%s%s%s%s" % (airports,start,end,kind)
    return hash(s)
def getType(event):
    if event["type"] == "Event":
        return 1
    else:
        return 0
def toGithub(frame,num_to_val):
    try:
        data,num_to_val = doConversion(frame)
        uploadtoGithub(json.dumps(num_to_val),'dictionary.txt')
        uploadtoGithub(data.to_csv(index=False),'data.csv')
        return num_to_val
    except BaseException as e:
        save(events,num_to_val)
        print(e)
        print("Error for to github")
        return frame, {}
def fromGithub():
    num_to_val = requests.get("https://raw.githubusercontent.com/MatisseBE/VATSIMeventHISTORY/main/dictionary.txt").text
    num_to_val = json.loads(str(num_to_val))
    url = "https://raw.githubusercontent.com/MatisseBE/VATSIMeventHISTORY/main/data.csv"
    frame = pd.read_csv(url)
    frame["airports"].replace(num_to_val, inplace=True)
    print(num_to_val)
    print("0 : " + num_to_val["0"])
    
    series_hashes = []
    for index, row in frame.iterrows():
        a = row["airports"]
        b = row["start"]
        c = row["end"]
        d = row["kind"]
        series_hashes.append(getHash(a,b,c,d))
    
    frame["hash"] = series_hashes
    print(frame)
    return frame,num_to_val
def getAirports(event):
    ports = []
    for port in event["airports"]:
        ports.append(port["icao"])
    return "/".join(ports)
def loop_event_data(data,events):
    for event in data:
        if event["organisers"][0]["division"] == "EUD": #Event in VATUED
            #Get data
            start = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%y-%m-%d %H:%M")
            end = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%y-%m-%d %H:%M") #convert string to  date time, convert datetime to different time string
            airports = getAirports(event)
            kind = getType(event)
            hash = getHash(airports,start,end,kind)
            #Check if already exists
            if hash not in events["hash"].values and len(airports) > 0:
                print("Added", event["name"] + " at " + str(datetime.now()))
                row = { "airports" : airports, "start": start, "end" :end, "kind":kind, "hash" : hash}
                events = events.append(row,ignore_index=True)

    return events

#When crashed, get backup from github
events,num_to_val = fromGithub()
#events = pd.DataFrame(columns=["airports","start","end","hash","kind"])
#num_to_val = {}

#while True:
try:
    num_to_val = toGithub(events.drop(["hash"],axis=1),num_to_val) #update to github
    time.sleep(5) #86400
    #Get events from website
    url = "https://my.vatsim.net/api/v1/events/all"
    data = requests.get(url).json()["data"]
    events = loop_event_data(data,events) #current load, all history

except Exception as e: #url uncallable
    print(datetime.now())
    save(events,num_to_val)
    print(e)

input("Press any to continue...")

##TODO: group weekly or long airportss
#delete from memory



