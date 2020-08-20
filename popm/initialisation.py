
import numpy as np
import pandas as pd
import geopandas as gpd

import random

from shapely.geometry import Point
from shapely.ops import cascaded_union

def load_data():

  # TODO use code as index?

  # remove and rename columns
  geojson = "./data/force_boundaries_ugc.geojson"
  force_data = "./data/PFAs-VECTOR-NAMES-Basic-with-Core-with-Alliance.csv"
  # From https://www.ons.gov.uk/peoplepopulationandcommunity/crimeandjustice/datasets/policeforceareadatatables
  # 6/2019 is the latest complete dataset
  population_data = "./data/population_data.csv"

  gdf = gpd.read_file(geojson, crs={ "init": "epsg:4326" }) \
    .drop(["OBJECTID"], axis=1) \
    .rename({"PFA16CD": "code", "PFA16NM": "name" }, axis=1) \
    .set_index("code", drop=True)

  # Merge: W.Midlands+W.Mercia and Beds+Cambs+Beds+Herts
  gdf.at["E23000014", "geometry"] = cascaded_union([gdf.at["E23000014", "geometry"], gdf.at["E23000016", "geometry"]])
  gdf.at["E23000026", "geometry"] = cascaded_union([gdf.at["E23000023", "geometry"], gdf.at["E23000026", "geometry"], gdf.at["E23000027", "geometry"]])
  gdf.drop(["E23000016", "E23000023", "E23000027"], inplace=True)
  # breaks some later merge
  #gdf.at["E23000014", "name"] = "W Midlands & W Mercia"
  #gdf.at["E23000014", "name"] = "Beds, Cambs & Herts"

  # length/area units are defined by the crs
  # df.crs.axis_info[0].unit_name

  data = pd.read_csv(force_data) \
    .replace({"Metropolitan": "Metropolitan Police"}) \
    .rename({"Force": "name",
             "Core-function-1 ": "core_function1",
             "Core-function-2": "core_function2",
             "Core-function-1-POP": "core_function1_pop",
             "Core-function-2-POP": "core_function2_pop"
            }, axis=1)
  # POP = Public Order (trained) Police

  populations = pd.read_csv(population_data) \
    .replace({"London, City of": "City of London"}) \
    .rename({"Police Force": "name", "MYE2018": "population", "SNHP2017": "households"}, axis=1)[["name", "population", "households"]]

  gdf = gdf.merge(data, on="name", how="left").fillna(0).merge(populations, on="name")

  # # ratio of police to people (hacks for missing data)
  # for i in [15,22,26]:
  #   gdf.at[i, "Officers"] = 0.004 * gdf.at[i, "population"]

  # TODO this will be wrong for merged
  #gdf["cops_per_pop"] = gdf.Officers / gdf.population

  # NOTE warnings:
  # pandas/core/generic.py:5155: UserWarning: Geometry is in a geographic CRS. Results from 'area' are likely incorrect. Use 'GeoSeries.to_crs()'
  # to re-project geometries to a projected CRS before this operation.
  # pyproj/crs/crs.py:53: FutureWarning: '+init=<authority>:<code>' syntax is deprecated. '<authority>:<code>' is the preferred initialization method.
  # When making the change, be mindful of axis order changes: https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6

  # extract boundary data
  boundaries = gpd.GeoDataFrame(gdf[['name', 'geometry', 'Officers', 'POP', 'Percentage', 'core_function1',
    'core_function2', 'core_function1_pop', 'core_function2_pop', 'Alliance', 'population', 'households']])

  # extract centroid data
  # TODO the geojson contains latlong and BNG coords for centroids so could directly compute distances from east/northings (if simpler)

  # compute centroids and shift index so that agent ids arent duplicated
  # for now the centroids dont have the force data
  centroids = gpd.GeoDataFrame(gdf[["name", "Alliance"]], geometry=gpd.points_from_xy(gdf.LONG, gdf.LAT), crs = {"init": "epsg:4326"})
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

def create_psu_data(boundaries, centroids, staff_absence):

  # Assumption (as per netlogo) that each core function has 200 essential officers that can't be deployed elsewhere

  # 1 PSU = 1 inspector + 3 sergeants + 21 constables
  # taken from non-absent POP-trained officers

  # must have at least 200 officers per function (assume dont have to be POP trained)
  presence = 1-staff_absence/100
  f1_avail = np.minimum(boundaries.core_function1_pop * presence, np.maximum(0, boundaries.core_function1 * presence - 200))
  f2_avail = np.minimum(boundaries.core_function2_pop * presence, np.maximum(0, boundaries.core_function2 * presence - 200))

  boundaries["available_psus"] = np.floor((f1_avail + f2_avail) / 25).astype(int)
  boundaries["dispatched_psus"] = 0

  psu_data = boundaries[["name", "Alliance", "geometry"]]
  for _, r in boundaries.iterrows():
    n = r.available_psus
    name = boundaries.name[r.name] # no idea why r.name is a number not a string
    if n < 1:
      psu_data.drop(psu_data[psu_data.name == name].index, inplace=True)
    if n > 1:
      psu = psu_data[psu_data["name"] == name]
      psu_data = psu_data.append([psu]*(n-1),ignore_index=True)
    # check we have the right number
    assert len(psu_data[psu_data.name == name]) == n

  # now covert geometry from the force area polygon to a random point in it
  for i, r in psu_data.iterrows():
    min_x, min_y, max_x, max_y = r.geometry.bounds

    while True:
      random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
      if random_point.within(r.geometry):
        psu_data.at[i, "geometry"] = random_point
        break

  psu_data["dispatched_to"] = ""
  psu_data["deployed"] = False
  psu_data.index += 1000 # ensure unique

  return psu_data


def initialise_events(no_of_events, event_resources, event_duration, force_centroid_agents):
  # activate events as per parameters
  active = random.sample(range(len(force_centroid_agents)), min(no_of_events, len(force_centroid_agents)))

  for a in active:
    force_centroid_agents[a].public_order_events = 1
    force_centroid_agents[a].event_resources_required = event_resources
    force_centroid_agents[a].event_resources_allocated = 0
    force_centroid_agents[a].event_resources_present = 0
    force_centroid_agents[a].event_duration = event_duration

  return active