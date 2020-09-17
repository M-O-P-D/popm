# %%
import os
from dotenv import load_dotenv, find_dotenv

from popm.initialisation import load_data
from popm.utils import *


forces, _dists, _times = load_data()

print(forces.columns.values)

# %%

coords = []

for _,r in forces.iterrows():
  #print(deserialise_geometry(r.centroid), end=" -> ")
  ll = bng2lonlat(deserialise_geometry(r.centroid))
  coords.append([ll.x, ll.y])

print(coords)

# %%

import requests

# API key should be in .env
load_dotenv(find_dotenv())

BASE_URL = "https://graphhopper.com/api/1/"

query = {
  "point": "%.5f,%.5f" % (coords[0][1], coords[0][0]),
  "time_limit": 600,
  "vehicle": "car",
  "reverse_flow": "true",
  "key": os.getenv("GRAPHHOPPER_API_KEY")
}


response = requests.get(BASE_URL + "isochrone", params=query)

if not response.ok:
  print(response.status_code, response.text)

result = response.json()

print(result["polygons"][0]["type"])
print(result["polygons"][0]["geometry"]["type"])
print(len(result["polygons"][0]["geometry"]["coordinates"]))
print(len(result["polygons"][0]["geometry"]["coordinates"][0]))

# %%
from shapely.geometry import shape, GeometryCollection
import geopandas as gpd

gc = GeometryCollection([shape(feature["geometry"]).buffer(0) for feature in result["polygons"]])

p = gpd.GeoSeries(gc[0])

print(p)
# %%
from popm.utils import *
q = lonlat2bng(p[0])
print(q)

# %%
import matplotlib.pyplot as plt

plt.plot(*q.exterior.xy)
# %%

# %%
