import os
from mesa_geo.geoagent import GeoAgent
from shapely.geometry import Point
import requests
import numpy as np
from dotenv import load_dotenv, find_dotenv

from .utils import *

# API key should be in .env
load_dotenv(find_dotenv())

BASE_URL = "https://graphhopper.com/api/1/"

# need a custom url builder as have duplicate param names
def url(endpoint, query=[]):
  query.append(("key", os.getenv("GRAPHHOPPER_API_KEY")))
  url = BASE_URL + endpoint + "?"
  url += "&".join(["%s=%s" % (param, val) for param, val in query])
  return url


def get_route(start_bng, end_bng):

  print(start_bng)
  print(type(start_bng))

  start = bng2lonlat(start_bng)
  end = bng2lonlat(end_bng)

  query = [
    ("point", ("%f,%f" % (start.y, start.x))), # "53.9261829,-1.8270279"),
    ("point", ("%f,%f" % (end.y, end.x))), # "53.9233771,-1.8003073"),
    ("vehicle", "car"),
    ("calc_points", "true"),
    ("points_encoded", "false"), # means points are just lon/lat, which is what we want
    ("details", "max_speed")
  ]

  print(query)

  response = requests.get(url("route", query))

  assert response.ok, response

  result = response.json()
  route = result["paths"][0]
  #bbox = [[route["bbox"][1], route["bbox"][0]], [route["bbox"][3], route["bbox"][2]]]
  points = np.array([[p[1],p[0]] for p in route["points"]["coordinates"]])
  times = np.linspace(0, result["paths"][0]["time"]/1000.0, len(points))

  s = [lonlat2bng(shapely.geometry.Point(p[1], p[0])) for p in points]

  x = [p.x for p in s]
  y = [p.y for p in s]

  return times, x, y

class FordGranada(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and track public order events within the force area """
  def __init__(self, unique_id, model, shape):
    super().__init__(unique_id, model, shape)

    self.route_points = []
    self.route_times = 0.0

  # routes are stored in model otherwise would get serialised and sent to client
  def route(self):
    return get_route(self.shape, deserialise_geometry(self.destination))

  def step(self):
    t = self.model.time() * 3600
    rt, rx, ry = self.model.car_routes[self.unique_id]

    px = np.interp(t, rt, rx)
    py = np.interp(t, rt, ry)
    #print(self.unique_id, t, px, py)
    self.shape = Point([px, py])

  def render(self):
    return { "radius": 2, "color": "Red", "Layer": 0 }


