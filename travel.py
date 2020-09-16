
import os
import json
import requests
import numpy as np
from dotenv import load_dotenv, find_dotenv

# API key should be in .env
load_dotenv(find_dotenv())

BASE_URL = "https://graphhopper.com/api/1/"

# need a custom url builder as have duplicate param names
def url(endpoint, query=[]):
  query.append(("key", os.getenv("GRAPHHOPPER_API_KEY")))
  url = BASE_URL + endpoint + "?"
  url += "&".join(["%s=%s" % (param, val) for param, val in query])
  return url

endpoint = "route"

query = [
  ("point", "53.9261829,-1.8270279"),
  ("point", "53.9233771,-1.8003073"),
  ("vehicle", "car"),
  ("calc_points", "false"),
]

response = requests.get(url(endpoint, query))

if not response.ok:
  print(response)
else:
  result = response.json()
  if not "paths" in result:
    print("no paths found")
  else:
    dist = result["paths"][0]["distance"] / 1000.0 #km
    time = result["paths"][0]["time"] / 3600000 # h 
    print("%.2fkm in %.2fh" % (dist, time))


body = json.dumps({
  "from_points": [
    [-1.8270279, 53.9261829],
    [-1.8003073, 53.9233771],
    [-1.5540781,53.8039043]
  ],
  "to_points": [
    [-1.8270279, 53.9261829],
    [-1.8003073, 53.9233771],
    [-1.5540781,53.8039043]
  ],
  "vehicle": "car",
  "elevation": False,
  "calc_points": False,
  "out_arrays": ["distances", "times"]
})
#curl -X POST -H "Content-Type: application/json" "https://graphhopper.com/api/1/route?key=[YOUR_KEY]" -d '{"elevation":false,"points":[[-0.087891,51.534377],[-0.090637,51.467697]],"vehicle":"car"}'

response = requests.post(url("matrix", []), body, headers={"Content-Type": "application/json"})

if not response.ok:
  print(response)
else:
  result = response.json()
  dists = np.array(result["distances"]) / 1000.0 # km
  times = np.array(result["times"]) / 3600.0 # h
  print(dists)
  print(times)