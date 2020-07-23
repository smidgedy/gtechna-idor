#!/usr/bin/python3
################################################################################
#
#   parking.py - scraper for Wilsons parking infringement ticket system
#
#   Please forgive me, I am bad at Python.
#
#   ./parking.py --min 760590321 --max 770000000 --destination tickets-nz/ --threads 32
#   for i in $( seq 6 9 ); do ../parking.py --min "101${i}00000" --max "101${i}99999" --destination "101${i}/" --threads 16; done
################################################################################

import concurrent.futures
import datetime
import json
import random
import re
import requests
import threading
import time
import os.path
import argparse


################################################################################
#
#   C O N F I G U R E     M E     P L E A S E
#
################################################################################

# These are the endpoints we're hitting for data
ticketServlet = "https://ebreach-gtechna.pesau.com.au/officercc/TicketServlet"
ticketSearch  = "https://ebreach-gtechna.pesau.com.au/userportal/ticketSearch.xhtml"
################################################################################

parser = argparse.ArgumentParser()
parser.add_argument("--min", type=int, help="Only check serials equal to or above this")
parser.add_argument("--max", type=int, help="Only check serials equal to or below this")
parser.add_argument("--threads", type=int, default=32, help="Run this many threads simultaneously (default 32)")
parser.add_argument("--overwrite", action="store_true", default=False, help="re-scrape records already present in the output folder")
parser.add_argument("--destination", default="tickets", help="specify the output folder for all the files (default tickets/)")
args = parser.parse_args()

# Hit the webpage that shows ticket details and use shitty shitty
# regexes to scrape the data and save as a JSON object.
def scrape( id ):
    global args

    if os.path.exists(args.destination + str(id) + ".json") == True and args.overwrite == False:
        return True

    params = {
        'lastName': '',
        'companyName': '',
        'plate': '',
        'operation': 'search',
        'ticketNumber': id
    }
    output = {}

    # trying out a random sleep to reduce the hammering of the server
    time.sleep(random.uniform(0, 2.0))

    r = requests.get(url = ticketSearch, params = params, timeout = 5.0)

    if r.status_code == 200:
        text = r.text
        if "Infrac" in text:
            output['id'] = id
            output['status'] = re.search('Breach - [0-9]+  \( (.+?) \)', text).group(1)
            output['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(re.findall('Infrac. Date</div>.*?<div class="col-xs-9 col-sm-10">(.+?)</div>', text, re.MULTILINE|re.DOTALL)[0].strip(), '%b %d %Y %I:%M %p'))
            output['plate'] = re.findall('Plate</div>.*?<div class="col-xs-9 col-sm-10">(.+?)</div>', text, re.MULTILINE|re.DOTALL)[0].strip()
            output['amount'] = float(re.findall('Amount</div>.*?<div class="col-xs-9 col-sm-10">\$(.+?)</div>', text, re.MULTILINE|re.DOTALL)[0].strip())
            
            # some fields are not always present - I don't yet know of
            # a better way to first check for the presence of results
            # before  attempting to read them.
            tmp = re.findall('Balance </div>.*?<div class="col-xs-9 col-sm-10">.*?<h2>\$([^\s]+?)\s+</h2>\s*</div>', text, re.MULTILINE|re.DOTALL)
            if len(tmp) > 0:
                output['outstanding'] = float(tmp[0].strip())
            tmp = re.findall('<iframe.*?v1/place\?q=(.+?),(.+?)&', text, re.MULTILINE|re.DOTALL)
            if len(tmp) > 0:
                output['location'] = { 'lat': float(tmp[0][0]), 'lon': float(tmp[0][1])}

            tmp = re.findall('<div class="col-xs-3 col-sm-2">Appeal Status</div>.*?<div class="col-xs-9 col-sm-10">\s*?([^\s]+?)\s*?</div>', text, re.MULTILINE|re.DOTALL)
            if len(tmp) > 0:
                output['appeal'] = {'status': tmp[0]}            
                
                tmp = re.findall('<div class="col-xs-3 col-sm-2">Reason</div>.*?<div class="col-xs-9 col-sm-10">(.+?)</div>', text, re.MULTILINE|re.DOTALL)
                if len(tmp) > 0:
                    output['appeal']['reason'] = tmp[0].strip()

                tmp = re.findall('<div class="col-xs-3 col-sm-2">Appeals</div>.*?<div class="col-xs-9 col-sm-10">(.+?)</div>', text, re.MULTILINE|re.DOTALL)
                if len(tmp) > 0:
                    output['appeal']['count'] = int(tmp[0].strip())

            with open(args.destination + str(id) + ".json", "wt") as f:
                f.writelines(json.dumps(output, sort_keys=True, indent=4))
        
            return True
        else:
            return False                  
    else:
        print ('http error ', str(id))
        return False

def ticketImage( id ):

    if os.path.exists(args.destination + str(id) + ".ticket.png"):
        return False

    params = {
        'type': 'ticketPng',
        'plate': '',
        'height': '',
        'ticketNo': id
    }

    r = requests.get(url = ticketServlet, params = params)

    if r.status_code == 200:
        with open(args.destination + str(id) + ".ticket.png", 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        # Add a refrence to the ticket image to the JSON
        with open(args.destination + str(id) + ".json", "r+") as f:
            data = json.load(f)
            data ['ticketImage'] = str(id) + ".ticket.png"
            f.seek(0)
            f.writelines(json.dumps(data, sort_keys=True, indent=4))
            f.truncate()
        return True
    else:
        return False
        
# Recursive function grabs any photos of the parking infringement one at a time
def pics( id, index = 1):

    if os.path.exists(args.destination + str(id) + ".pic" + str(index) + ".jpg"):
        return pics(id, index+1)

    params = {
        'type': 'picture',
        'plate': '',
        'sequenceId': index,
        'ticketNo': id
    }

    r = requests.get(url = ticketServlet, params = params)
    if r.status_code == 200:
        with open(args.destination + str(id) + ".pic" + str(index) + ".jpg", 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

         # Add a refrence to the ticket image to the JSON
        with open(args.destination + str(id) + ".json", "r+") as f:
            data = json.load(f)
            if not 'photos' in data:
                data['photos'] = []            
            data ['photos'].append(str(id) + ".pic" + str(index) + ".jpg")
            f.seek(0)
            f.writelines(json.dumps(data, sort_keys=True, indent=4))
            f.truncate()        
        pics(id, index+1)

# Using a value to sleep threads when we get an exception. Didn't bother
# making it threadsafe, but roughly every time there are sequential exceptions
# (i.e. the WAF fucks us) this value will double. When requests start working
# this gets set back to 1 second.
standoff = 1

exceptionLock = threading.Lock()

# Wrapper for the worker threads.  Tests, scrapes, and saves images + handles
# exceptions by logging the ID numbers we missed and sleeping the thread to
# slow us down.
def process (id):
    global exceptionLock

    try:
        if scrape (id) == True:
            standoff = 1
            print("found ", id)
            ticketImage(id)
            pics(id)

    except Exception as e:
        print("Exception raised, sleeping " + str(standoff) + " seconds\n")
        print(e)
        standoff *= 2
        exceptionLock.acquire()
        with open(args.destination + 'exceptions.txt', "a") as f:
            f.write(str(id) + "\n")
        exceptionLock.release()
        time.sleep(standoff)
    return

# Script entry point. Run some threads.
if args.min and args.max:
    min = args.min
    while min < args.max:        
        tmpMax = min + 1000 if args.max - min > 1000 else args.max
        print("queuing up search ", min, " to ", tmpMax)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers = args.threads)
        executor.map(process, range(min, tmpMax, 1))
        executor.shutdown(wait=True)
        min = min + 1000
else:
    parser.print_help()