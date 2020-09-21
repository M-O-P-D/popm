# %%

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
  ("calc_points", "true"),
  ("points_encoded", "false"), # means points are just lon/lat, which is what we want
  ("details", "max_speed")
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

# %%
import numpy as np
from matplotlib import pyplot as plt

route = result["paths"][0]
bbox = [[route["bbox"][1], route["bbox"][0]], [route["bbox"][3], route["bbox"][2]]] 
points = np.array([[p[1],p[0]] for p in route["points"]["coordinates"]])
#legs = [(node["time"]/1000.0, node["interval"]) for node in route["instructions"]]
#points seems to be roughtly evenly space in time, i.e. further apart on faster roads
# so just linspace the end time (rather than each leg)

times = np.linspace(0, result["paths"][0]["time"], len(points))

plt.plot(times, points[:,0])

plt.plot(times, points[:,1])

# %%
import folium
from folium.plugins import MarkerCluster
import pandas as pd

map=folium.Map(location=[53.9261829,-1.8270279], zoom_start=12)
map.fit_bounds(bbox) # doesnt work
map
# %%

for i, p in enumerate(points):
  folium.CircleMarker(p, popup=str(i)).add_to(map) 

map
# %%
m = folium.CircleMarker(points[0], radius=20, popup="movable?")

m.add_to(map)
# %%
l = folium.PolyLine(points)
l.add_to(map)nazi 
map

# %%
