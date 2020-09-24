
# cache routes between force area centroids

import os
import requests
from dotenv import load_dotenv, find_dotenv
from geopandas import gpd
from shapely.geometry import LineString

from popm.initialisation import load_data
from popm.utils import bng2lonlat, deserialise_geometry

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
    ("point", ("%f,%f" % (start_ll.y, start_ll.x))), # "53.9261829,-1.8270279"),
    ("point", ("%f,%f" % (end_ll.y, end_ll.x))), # "53.9233771,-1.8003073"),
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

  # s = [lonlat2bng(shapely.geometry.Point(p[1], p[0])) for p in points]

  # x = [p.x for p in s]
  # y = [p.y for p in s]

  return time, route


force_data, _, _ = load_data()

#force_data = force_data.head(3)

nforces = len(force_data)

routes = gpd.GeoDataFrame(index=range(nforces*(nforces-1)), columns=["origin", "destination", "geometry"])


idx = 0
for i, r in force_data.iterrows():
  for j, s in force_data.iterrows():
    if r.name != s.name:
      routes.loc[idx, "origin"] = r["name"]
      routes.loc[idx, "destination"] = s["name"]

      origin = bng2lonlat(deserialise_geometry(r["centroid"]))
      destination = bng2lonlat(deserialise_geometry(s["centroid"]))

      time, route = get_route(origin, destination)

      routes.loc[idx, "time"] = time
      routes.loc[idx, "geometry"] = LineString(route)

      idx += 1

print(routes.head())

routes.to_csv("data/force_centroid_routes.csv", index=False)
