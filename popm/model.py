from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import GeoAgent, AgentCreator
from mesa_geo import GeoSpace

import pandas as pd
import geopandas as gpd
import numpy as np

from .agents import *

def _load_data():
  # remove and rename columns 
  geojson = "./data/force_boundaries_ugc.geojson"
  force_data = "./data/PFAs-VECTOR-NAMES-Basic-with-Core-with-Alliance.csv"

  gdf = gpd.read_file(geojson, crs={ "init": "epsg:4326" }) \
    .drop(["OBJECTID", "BNG_E", "BNG_N"], axis=1) \
    .rename({"PFA16CD": "code", "PFA16NM": "name" }, axis=1)

  # length/area units are defined by the crs
  # df.crs.axis_info[0].unit_name

  data = pd.read_csv(force_data) \
    .replace({"Metropolitan": "Metropolitan Police"}) \
    .rename({"Force": "name"}, axis=1)

  gdf = gdf.merge(data, on="name", how="left").fillna(0)

  # NOTE warnings:
  # pandas/core/generic.py:5155: UserWarning: Geometry is in a geographic CRS. Results from 'area' are likely incorrect. Use 'GeoSeries.to_crs()' 
  # to re-project geometries to a projected CRS before this operation.  
  # pyproj/crs/crs.py:53: FutureWarning: '+init=<authority>:<code>' syntax is deprecated. '<authority>:<code>' is the preferred initialization method. 
  # When making the change, be mindful of axis order changes: https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6

  # extract boundary data
  boundaries = gpd.GeoDataFrame(gdf[['code', 'name', 'geometry', 'Officers', 'POP', 'Percentage', 'Core-function-1 ',
    'Core-function-2', 'Core-function-1-POP', 'Core-function-2-POP', 'Alliance']])
  # extract centroid data

  # compute centroids and shift index so that agent ids arent duplicated
  # for now the centroids dont have the force data
  centroids = gpd.GeoDataFrame(gdf[["code", "name"]], geometry=gpd.points_from_xy(gdf.LONG, gdf.LAT), crs = {"init": "epsg:4326"})
  centroids.index += 100

  # compute distance matrix
  # convert to different projection for distance computation
  # see https://gis.stackexchange.com/questions/293310/how-to-use-geoseries-distance-to-get-the-right-answer
  # index offset by 100 needs to be reset for loop below to work
  c = centroids.to_crs(epsg=3310).reset_index(drop=True)
  m = np.zeros((len(c), len(c)))
  for i in range(len(c)):
    m[i,:] = c.distance(c.geometry[i]) / 1000.0
  distances = pd.DataFrame(m, columns=c.name, index=c.name)

  return boundaries, centroids, distances

class PublicOrderPolicing(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """

  def __init__(self): #params...

    self.log = []
    self.datacollector = DataCollector(model_reporters={})

    # Set up the grid and schedule.

    # Use SimultaneousActivation which simulates all the cells
    # computing their next state simultaneously.  This needs to
    # be done because each cell's next state depends on the current
    # state of all its neighbors -- before they've changed.
    self.schedule = RandomActivation(self)

    # Use a multi grid so that >1 agent can occupy the same location
    self.grid = GeoSpace()

    # Ultra Generalised Clipped otherwise too much rendering
    boundaries, centroids, distances = _load_data()

    # Set up the force agents
    factory = AgentCreator(ForceAreaAgent, {"model": self})   
    force_area_agents = factory.from_GeoDataFrame(boundaries)
    self.grid.add_agents(force_area_agents) 
    for agent in force_area_agents:
      self.schedule.add(agent)

    factory = AgentCreator(ForceCentroidAgent, {"model": self}) 
    force_centroid_agents = factory.from_GeoDataFrame(centroids)
    self.grid.add_agents(force_centroid_agents) 
    for agent in force_centroid_agents:
      self.schedule.add(agent)

    self.log.append("Initialised model")
    self.running = True
    self.log.append("running=%s" % self.running)

  def step(self):
    """
    Have the scheduler advance each cell by one step
    """
    # self.log.append("stepping")
    # self.log = self.log[-3:]
    self.schedule.step()
    #self.datacollector.collect(self)

    # Halt the model
    self.running=False


if __name__ == "__main__":
  (b,c) = _load_data()
  print(b.head())
  print(c.head())