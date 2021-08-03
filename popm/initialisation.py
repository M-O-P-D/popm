# suppress deprecation warning we can't do anything about
import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.ops import cascaded_union

PSU_OFFICERS = 25
CORE_FUNCTIONS = ["emergency", "firearms", "major_incident", "public_order", "serious_crime", "custody"]
# must come after CORE_FUNCTIONS is defined
from .utils import npbitgen

def load_force_data():

  geojson = "./data/force_boundaries_ugc.geojson"
  force_data_file = "./data/PFAs-VECTOR-NAMES-Basic-with-Core-with-Alliance.csv"
  # From https://www.ons.gov.uk/peoplepopulationandcommunity/crimeandjustice/datasets/policeforceareadatatables
  # 6/2019 is the latest complete dataset
  population_data = "./data/population_data.csv"

  # remove and rename columns
  gdf = gpd.read_file(geojson, crs={"init": "epsg:4326"}) \
           .drop(["OBJECTID"], axis=1) \
           .rename({"PFA16CD": "code", "PFA16NM": "name"}, axis=1) \
           .set_index("code", drop=True) \
           .to_crs(epsg=27700)

  # Merge Beds/Cambs/Herts (only)
  gdf.at["E23000026", "geometry"] = cascaded_union([gdf.at["E23000023", "geometry"], gdf.at["E23000026", "geometry"], gdf.at["E23000027", "geometry"]])
  gdf.drop(["E23000023", "E23000027"], inplace=True)
  gdf.at["E23000026", "name"] = "Beds Cambs Herts"

  data = pd.read_csv(force_data_file) \
           .replace({"Metropolitan": "Metropolitan Police", "Bedfordshire": "Beds Cambs Herts"}) \
           .rename({"Force": "name"}, axis=1)
  # POP = Public Order (trained) Police

  populations = pd.read_csv(population_data) \
    .replace({"London, City of": "City of London"}) \
    .rename({"Police Force": "name", "MYE2018": "population", "SNHP2017": "households"}, axis=1)[["name", "population", "households"]]

  gdf = gdf.merge(data, on="name", how="left").fillna(0).merge(populations, on="name")

  # NOTE warnings (which have been silenced):
  # pandas/core/generic.py:5155: UserWarning: Geometry is in a geographic CRS. Results from 'area' are likely incorrect. Use 'GeoSeries.to_crs()'
  # to re-project geometries to a projected CRS before this operation.
  # pyproj/crs/crs.py:53: FutureWarning: '+init=<authority>:<code>' syntax is deprecated. '<authority>:<code>' is the preferred initialization method.
  # When making the change, be mindful of axis order changes: https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6

  # extract boundary data
  columns = ['name', 'geometry', 'Officers', 'POP', 'Percentage', 'Alliance', 'population', 'households', 'reserved_psus'] \
    + CORE_FUNCTIONS + [f + "_POP" for f in CORE_FUNCTIONS] + [f + "_MIN" for f in CORE_FUNCTIONS]
  force_data = gpd.GeoDataFrame(gdf[columns])

  # extract centroid data
  centroids = gpd.GeoDataFrame(gdf[["name", "Alliance"]], geometry=gpd.points_from_xy(gdf.LONG, gdf.LAT), crs={"init": "epsg:4326"}) \
    .to_crs(epsg=27700) \
    .set_index("name", drop=True)

  # ensure data is not geographically linked by sorting alphabetically
  force_data = force_data.sort_values(["name"]).reset_index(drop=True)

  # # generate alliance boundaries (uncomment if needed)
  # alliance_boundaries = gpd.GeoDataFrame(data={"name": force_data.Alliance.unique()}, crs={"init": "epsg:4326"})
  # alliance_boundaries["geometry"] = alliance_boundaries.name.apply(lambda n: cascaded_union(force_data[force_data.Alliance == n]["geometry"]))
  # alliance_boundaries.to_crs(epsg=27700)
  # alliance_boundaries.to_file("./data/alliances.geojson", driver="GeoJSON")

  return force_data, centroids


def create_psu_data(forces, centroids):

  # 1 PSU = 1 inspector + 3 sergeants + 21 constables
  # taken from non-absent POP-trained officers

  # Assumption that each core function has a core of essential officers that can't be deployed elsewhere
  avail = 0
  for _, f in enumerate(CORE_FUNCTIONS):
    avail += np.minimum(forces[f + "_POP"], np.maximum(0, forces[f] - forces[f + "_MIN"]))

  forces["available_psus"] = np.floor(avail / PSU_OFFICERS).astype(int)
  forces["dispatched_psus"] = 0

  psu_data = forces[["name", "Alliance", "geometry"]].copy()
  # switch from boundary to centroid
  psu_data["geometry"] = centroids.loc[psu_data["name"]]["geometry"].values

  # switch geometry from boundary to centroid
  for _, r in forces.iterrows():
    n = r.available_psus
    nres = min(r.reserved_psus, r.available_psus)  # in case the reserve number is higher than the available
    name = forces.name[r.name]  # no idea why r.name is a number not a string
    if n < 1:
      psu_data.drop(psu_data[psu_data.name == name].index, inplace=True)
    if n > 1:  # first add reserved psus (that don't leave force area)
      psu = psu_data[psu_data["name"] == name]
      psu_data = psu_data.append([psu] * (n - 1), ignore_index=True)
    psu_data.loc[psu_data["name"] == name, "reserved"] = [True] * nres + [False] * (n - nres)
    # check we have the right number
    assert len(psu_data[psu_data.name == name]) == n, "%s %d vs %d" % (name, len(psu_data[psu_data.name == name]), n)

  # all now live at force centroid for routing purposes

  # for name in forces.name:
  #   single_psu_data = psu_data[psu_data.name == name]
  #   for idx, r in single_psu_data.iterrows():
  #     # p = deserialise_geometry(r["centroid"])
  #     # x = p.x - rows * dx / 2
  #     # y = p.y - rows * dy / 2

  #     # # NB // is integer division
  #     psu_data.at[idx, "geometry"] = r["centroid"] #Point([x + j // rows * dx, y + j % rows * dy])
  #     #print(psu_data.at[idx, "geometry"])

  # # now covert geometry from the force area polygon a unique offset from the centroid
  # for name in forces.name:

  #   dx = 1000
  #   dy = 1000
  #   single_psu_data = psu_data[psu_data.name == name]

  #   rows = ceil(sqrt(len(single_psu_data)))
  #   j = 0
  #   for idx, r in single_psu_data.iterrows():
  #     p = deserialise_geometry(r["centroid"])
  #     x = p.x - rows * dx / 2
  #     y = p.y - rows * dy / 2

  #     # # NB // is integer division
  #     psu_data.at[idx, "geometry"] = Point([x + j // rows * dx, y + j % rows * dy])
  #     #print(psu_data.at[idx, "geometry"])
  #     j = j + 1

  psu_data["assigned_to"] = None
  psu_data["assigned"] = False
  psu_data["dispatched"] = False
  psu_data["deployed"] = False
  psu_data.index += 1000  # ensure unique

  return psu_data


def initialise_event_data(model, event_resources, event_start, event_duration, force_data, centroids):
  # activate events as per parameters and randomise the order
  

  # if locations are force names convert to index values
  if isinstance(model.event_locations[0], str):
    event_locations = force_data.index[force_data.name.isin(model.event_locations)].tolist()
  else:
    event_locations = model.event_locations

  #print(force_data)
  event_data = force_data.loc[event_locations, ["name", "Alliance", "geometry"]].sample(frac=1, random_state=npbitgen).reset_index(drop=True)

  # switch from boundary to centroid
  event_data["geometry"] = centroids.loc[event_data["name"]]["geometry"].values

  # no longer random in force area
  # for i, r in event_data.iterrows():
  #   min_x, min_y, max_x, max_y = r.geometry.bounds
  #   while True:
  #     p = Point([model.random.uniform(min_x, max_x), model.random.uniform(min_y, max_y)])
  #     if p.within(r.geometry):
  #       event_data.at[i, "geometry"] = p
  #       break

  event_data["resources_required"] = event_resources
  event_data["resources_allocated"] = 0
  event_data["resources_present"] = 0
  # times relative to current step
  event_data["time_to_start"] = event_start
  event_data["time_to_end"] = event_start + event_duration

  event_data.index += 100  # ensure unique

  return event_data
