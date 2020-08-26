
import numpy as np
import pandas as pd
import geopandas as gpd

import random
from math import ceil, sqrt

from shapely.geometry import Point
from shapely.ops import cascaded_union

PSU_OFFICERS = 25

def load_data():

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
  gdf.at["E23000014", "name"] = "W Midlands W Mercia"
  gdf.at["E23000026", "name"] = "Beds Cambs Herts"

  # length/area units are defined by the crs
  # df.crs.axis_info[0].unit_name

  data = pd.read_csv(force_data) \
    .replace({"Metropolitan": "Metropolitan Police",
              "Bedfordshire": "Beds Cambs Herts",
              "West Midlands": "W Midlands W Mercia"}) \
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

  gdf = gdf.merge(data, on="name", how="left", left_index=True).fillna(0).merge(populations, on="name")

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

  # add centroid column, but not as Shapely object as will get a serialisation error
  boundaries = boundaries.merge(centroids.rename({"geometry": "centroid"}, axis=1)[["name", "centroid"]], on="name")
  boundaries.centroid = boundaries.centroid.apply(lambda p: (p.x, p.y))

  # compute distance matrix
  # convert to different projection for distance computation
  # see https://gis.stackexchange.com/questions/293310/how-to-use-geoseries-distance-to-get-the-right-answer
  # index offset by 100 needs to be reset for loop below to work
  c = centroids.to_crs(epsg=3310).reset_index(drop=True)
  m = np.zeros((len(c), len(c)))
  for i in range(len(c)):
    m[i,:] = c.distance(c.geometry[i]) / 1000.0
  distances = pd.DataFrame(m, columns=c.name, index=c.name)


  return boundaries, distances

def create_psu_data(forces, staff_absence):

  # Assumption (as per netlogo) that each core function has 200 essential officers that can't be deployed elsewhere

  # 1 PSU = 1 inspector + 3 sergeants + 21 constables
  # taken from non-absent POP-trained officers

  # must have at least 200 officers per function (assume dont have to be POP trained)
  presence = 1-staff_absence/100
  f1_avail = np.minimum(forces.core_function1_pop * presence, np.maximum(0, forces.core_function1 * presence - 200))
  f2_avail = np.minimum(forces.core_function2_pop * presence, np.maximum(0, forces.core_function2 * presence - 200))

  forces["available_psus"] = np.floor((f1_avail + f2_avail) / PSU_OFFICERS).astype(int)
  forces["dispatched_psus"] = 0

  psu_data = forces[["name", "Alliance", "geometry", "centroid"]]
  for _, r in forces.iterrows():
    n = r.available_psus
    name = forces.name[r.name] # no idea why r.name is a number not a string
    if n < 1:
      psu_data.drop(psu_data[psu_data.name == name].index, inplace=True)
    if n > 1:
      psu = psu_data[psu_data["name"] == name]
      psu_data = psu_data.append([psu]*(n-1),ignore_index=True)
    # check we have the right number
    assert len(psu_data[psu_data.name == name]) == n

  # now covert geometry from the force area polygon a unique offset from the centroid
  for name in forces.name:

    dx = 0.02
    dy = 0.01
    single_psu_data = psu_data[psu_data.name == name]

    rows = ceil(sqrt(len(single_psu_data)))
    j = 0
    for idx, r in single_psu_data.iterrows():

      x = r["centroid"][0] - rows * dx / 2
      y = r["centroid"][1] - rows * dy / 2

      # # NB // is integer division
      psu_data.at[idx, "geometry"] = Point([x + j // rows * dx, y + j % rows * dy])
      j = j + 1

  psu_data["dispatched_to"] = ""
  psu_data["deployed"] = False
  psu_data.index += 1000 # ensure unique

  return psu_data


def initialise_event_data(no_of_events, event_resources, event_duration, forces):
  # activate events as per parameters
  # TODO use only Model RNG for reproducibility
  random.seed(19937)
  active = random.sample(list(forces.index.values), min(no_of_events, len(forces)))

  event_data = forces.loc[active, ["name", "Alliance", "geometry"]].copy()
  
  for i, r in event_data.iterrows():
    min_x, min_y, max_x, max_y = r.geometry.bounds
    while True:
      p = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
      if p.within(r.geometry):
        event_data.at[i, "geometry"] = p
        break

  event_data["resources_required"] = event_resources
  event_data["resources_allocated"] = 0
  event_data["resources_present"] = 0
  event_data["start_time"] = 0
  event_data["duration"] = event_duration

  return event_data