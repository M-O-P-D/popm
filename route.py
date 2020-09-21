# %%
import os
import numpy as np
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

data = {
  "from_points": coords,
  "to_points": coords,
  "vehicle": "car",
  "out_arrays": ["distances", "times"]
}

params = {"key": os.getenv("GRAPHHOPPER_API_KEY")}

response = requests.post(BASE_URL + "matrix", params=params, json=data)

if not response.ok:
  print(response.status_code, response.text)
else:
  result = response.json()
  dists = np.array(result["distances"]) / 1000.0 # km
  times = np.array(result["times"]) / 3600.0 # h
  print(dists)
  print(times)




# %%

import pandas as pd

distances = pd.DataFrame(np.array(result["distances"]) / 1000.0, columns=forces.name, index=forces.name)
times = pd.DataFrame(np.array(result["times"]) / 3600.0, columns=forces.name, index=forces.name)

# %%
distances.to_csv("data/centroid_distances.csv")
times.to_csv("data/centroid_times.csv")