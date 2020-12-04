
# cache routes between force area centroids

import os
import requests
from time import sleep
from dotenv import load_dotenv, find_dotenv
from geopandas import gpd
from shapely.geometry import LineString

from popm.initialisation import load_force_data
from popm.utils import bng2lonlat

# API key should be in .env
load_dotenv(find_dotenv())

BASE_URL = "https://graphhopper.com/api/1/"

# need a custom url builder as have duplicate param names
def url(endpoint, query=[]):
  query.append(("key", os.getenv("GRAPHHOPPER_API_KEY")))
  url = BASE_URL + endpoint + "?"
  url += "&".join(["%s=%s" % (param, val) for param, val in query])
  return url

def get_route(start_ll, end_ll):

  query = [
    ("point", "%f,%f" % (start_ll.y, start_ll.x)), # "53.9261829,-1.8270279"),
    ("point", "%f,%f" % (end_ll.y, end_ll.x)), # "53.9233771,-1.8003073"),
    ("vehicle", "car"),
    ("calc_points", "true"),
    ("points_encoded", "false"), # means points are just lon/lat, which is what we want
    ("details", "max_speed")
  ]

  response = requests.get(url("route", query))

  assert response.ok, response

  result = response.json()
  route = result["paths"][0]["points"]["coordinates"]
  time = result["paths"][0]["time"]/1000.0

  return time, route


_, centroids = load_force_data()

#force_data = force_data.head(3)

nforces = len(centroids)
#nroutes = nforces * (nforces-1) # all routes
nroutes = 2 * (nforces-1) # to/from one centroid

routes = gpd.GeoDataFrame(index=range(nroutes), columns=["origin", "destination", "geometry"])

centroids.geometry = centroids.geometry.apply(bng2lonlat)
print(centroids.head())

idx = 0
for i, r in centroids.iterrows():
  for j, s in centroids.iterrows():
    if i != j and (i == "West Mercia" or j == "West Mercia"):
      print("%s -> %s" % (i,j))
      routes.loc[idx, "origin"] = i
      routes.loc[idx, "destination"] = j

      origin = r["geometry"]
      destination = s["geometry"]

      time, route = get_route(origin, destination)

      routes.loc[idx, "time"] = time
      routes.loc[idx, "geometry"] = LineString(route)

      sleep(5)
      idx += 1

print(routes.head())

routes.to_csv("data/force_centroid_routes_add.csv", index=False)
