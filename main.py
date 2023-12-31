from flask import Flask, Response, request, jsonify, abort
from flask_cors import CORS
import requests
from ics import Calendar, Event
import os
from datetime import datetime as dt, timedelta
from time import sleep
import json
import hashlib
import codecs


app = Flask(__name__)
### Enable CORS so the webApp can use it###
CORS(app)

### Temp Folders ###
CACHE_DIR_PROCESSED = './temp/processed/'
CACHE_DIR_RAW = './temp/raw/'


### Calendar Fetching ###
def fetch_ics_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    buff = response.content
    ics_data = buff.decode("cp1252") 
    ics_data = ics_data.encode("utf-8")
    ics_data = str(ics_data)
    return ics_data

def fetch_ics_from_url_cached(url):
    # Caching raw calendar
    json = caching(CACHE_DIR_RAW,fetch_ics_from_url,[url],url,"ics",1)
    return json

### Parsing Calendars ###
def merge_calendars(ics_texts:str):
    combined_calendar = Calendar()
    i=0
    for ics_text in ics_texts:
        calendar = Calendar(ics_text)
        if i==0:
            combined_calendar.events.update(calendar.events)
        else:
            combined_calendar.events.add(calendar.events)
        i+=1
    return combined_calendar

    def merge_calendars(calendars:[Calendar]):
    counter = 0
    for calendar in calendars:
        if counter == 0:
            merged_calendar = calendar
        else:
            merged_calendar.events.update(calendar.events)
        counter += 1
    return merged_calendar

def generate_ics_http_response(ics: Calendar):
    return Response(ics.serialize(), mimetype='text/calendar')

### Routes ###
@app.route('/available_events', methods=['GET'])
def available_events_cached():
    ### Get URLS ###
    urls_param = request.args.get('URL', '')
    urls = [url.strip('"') for url in urls_param.split(',')]
    ### Fetch Calendars ###
    ics_texts = [fetch_ics_from_url_cached(url) for url in urls]
    ### Cache Events Calendar ###
    events = {}
    counter_calendar = 0
    for ics_text in ics_texts:
        events_dic_list = json.loads(caching(CACHE_DIR_RAW,available_event_from_calendar,[ics_text],urls[counter_calendar],"json",1))
        key = f'calendar_{counter_calendar}'
        events[key] = events_dic_list
        counter_calendar += 1
    ### Return Calendars Events ###
    return json.dumps(events)

def available_event_from_calendar(ics_text):
    ### Iterate ICSs ###
    event_dict = {}
    ### Parse ICS ###
    calendar = Calendar(ics_text)
    ### Get Calendar name ###
    event_dict = {}
    counter_event = 0
    for event in calendar.events:
        if event.name not in event_dict.values():
            key = f'e_{counter_event}'
            event_dict[key] = event.name
            counter_event += 1
    json_buff =  json.dumps(event_dict)
    return json.dumps(event_dict)


@app.route('/parse_calendar_whitelist', methods=['GET'])
def parse_calendar_whitelist_cached():
    return generate_ics_http_response(Calendar(caching(CACHE_DIR_PROCESSED,parse_calendar_whitelist,[request],request.url,"ics",1)))

def parse_calendar_whitelist(request):
    ### Get URLS ###
    urls_param = request.args.get('URL', '')
    urls = [url.strip('"') for url in urls_param.split(',')]
    ### Get Whitelist ###
    whitelist_param = request.args.get('whitelist', '')
    whitelist = [keyword.strip('"') for keyword in whitelist_param.split(',')]
    ### Fetch Calendars ###
    ### Check if whitelist event are available ###
    filtered_calendars = []
    error_count = 0
    for url in urls:
        ics_text = fetch_ics_from_url_cached(url)
        calendar = Calendar(ics_text);
        available_events = json.loads(caching(CACHE_DIR_RAW,available_event_from_calendar,[ics_text],url,"json",1))
        for whitelist_keyword in whitelist:
            ### Check if whitelist event are available ###
            if whitelist_keyword in available_events.values():
                ### Store Calendars Events in a list###
                temp_cal = Calendar()
                temp_cal.events.update([event for event in calendar.events if event.name in whitelist])
                filtered_calendars.append(temp_cal)
            else:
                if(error_count == len(urls)*len(whitelist) -1 ):
                    abort(404, description="whitelist event not available")
                error_count += 1
    ### Merge Calendars ###
    merged_calendar = merge_calendars(filtered_calendars)
    return merged_calendar.serialize()

@app.route('/parse_calendar_blacklist', methods=['GET'])
def parse_calendar_blacklist_cached():
    return generate_ics_http_response(Calendar(caching(CACHE_DIR_PROCESSED,parse_calendar_blacklist,[request],request.url,"ics",1)))

def parse_calendar_blacklist(request):
    ### Get URLS ###
    urls_param = request.args.get('URL', '')
    urls = [url.strip('"') for url in urls_param.split(',')]
    ### Get Whitelist ###
    blacklist_param = request.args.get('blacklist', '')
    blacklist = [keyword.strip('"') for keyword in blacklist_param.split(',')]
    ### Fetch Calendars ###
    ### Check if whitelist event are available ###
    filtered_calendars = []
    error_count = 0
    for url in urls:
        ics_text = fetch_ics_from_url_cached(url)
        calendar = Calendar(ics_text);
        available_events = json.loads(caching(CACHE_DIR_RAW,available_event_from_calendar,[ics_text],url,"json",1))
        for blacklist_keyword in blacklist:
            ### Check if whitelist event are available ###
            if blacklist_keyword in available_events.values():
                ### Store Calendars Events in a list###
                temp_cal = Calendar()
                temp_cal.events.update([event for event in calendar.events if event.name not in blacklist])
                filtered_calendars.append(temp_cal)
            else:
                if(error_count == len(urls)*len(blacklist) -1 ):
                    abort(404, description="whitelist event not available")
                error_count += 1
    ### Merge Calendars ###
    merged_calendar = merge_calendars(filtered_calendars)
    return merged_calendar.serialize()




### Performance Improvement ###
def caching(folder,content_function,content_function_params,hash_seed,file_format,cache_time_indays=1):
    cache_filename = os.path.join(folder, f'{consistent_hash(hash_seed)}.{file_format}')
    if os.path.exists(cache_filename):
        # Check if the file is older than 1 day
        modified_time = dt.fromtimestamp(os.path.getmtime(cache_filename))
        if dt.now() - modified_time < timedelta(days=cache_time_indays):
            with open(cache_filename, 'r') as file:
                console_log("Using cache on file: " + cache_filename  +" from " + hash_seed + "\n" )
                buff = file.read()
                return buff
    # If cache is not valid, generate content
    console_log("Update/New content stored it in cache: " + cache_filename  +" from " + hash_seed + "\n" )
    content = content_function(*content_function_params);
    # Write to cache
    os.makedirs(folder, exist_ok=True)
    with open(cache_filename, 'w') as file:
        if isinstance(content, Calendar):
            file.write(content.serialize())
        else:
            file.write(content)
    return content

### Make hash function consistent ###
def consistent_hash(input_string):
    sha256 = hashlib.sha256()
    sha256.update(input_string.encode('utf-8'))
    return sha256.hexdigest()

### Improve Log ###
def console_log(message):
    timestamp = dt.now().strftime("[%d/%b/%Y %H:%M:%S]")
    print(f"{timestamp} {message}")

if __name__ == '__main__':
    app.run(debug=True)