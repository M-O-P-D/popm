""" batch mode """

# TODO look into Mesa's BatchRunner class...

import json
import time
import pandas as pd
import argparse
from itertools import combinations
import warnings

warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import geopandas as gpd
from shapely import wkt

from popm.model import PublicOrderPolicing

def get_name(model, unique_id):
  for a in model.schedule.agents:
    if a.unique_id == unique_id:
      return a.name
  return str(unique_id)

# load this data once only (its a bottleneck and its constant anyway)
df = pd.read_csv("./data/force_centroid_routes.zip")
df["geometry"] = df["geometry"].apply(wkt.loads)
df["time"] = df["time"] / 3600.0 # convert travel time seconds to hours
routes = gpd.GeoDataFrame(df).set_index(["origin", "destination"])
n_locations = len(routes.index.levels[0])

def run(config, index, results):

  model = PublicOrderPolicing(
    config["no_of_events"],
    config["event_resources"],
    config["event_start"],
    config["event_duration"],
    config["staff_absence"],
    config["timestep"],
    config["event_locations"],
    routes)

  model.run_model()

  model_data = model.datacollector.get_model_vars_dataframe() * 100.0 / config["event_resources"] / config["no_of_events"]
  #print(model_data.loc[[index_1h, index_4h]])

  # indices for KPI metrics
  index_1h = (config["event_start"] + 1) / model.timestep
  index_4h = (config["event_start"] + 4) / model.timestep
  results.loc[index] = { 
    "location": [get_name(model, id) for id in model.event_locations], 
    "start": config["event_start"], 
    "resources-per-event": config["event_resources"], 
    "KPI-1h-deployed-pct": model_data.loc[index_1h, "Deployed"], 
    "KPI-4h-deployed-pct": model_data.loc[index_4h, "Deployed"]
  }
  
  
if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="popm batch run")
  parser.add_argument("config", type=str, help="the model configuration file (json)")
  #parser.add_argument("runs", nargs="?", type=int, default=1, help="the number of runs to execute, default 1")
  args = parser.parse_args()

  start_time = time.time()

  # load config
  with open(args.config) as f:
    master_config = json.load(f)

    n_runs =  len(master_config["event_resources"]) * len(master_config["event_start"])

    # Get all combinations for given number of events
    if "event_locations" not in master_config:
      locations = list(combinations(range(n_locations), master_config["no_of_events"]))
      n_runs *= len(locations)

    print("Total runs = %d" % n_runs)

    results = pd.DataFrame(index = range(n_runs), columns={"location", "start", "resources-per-event", "KPI-1h-deployed-pct", "KPI-4h-deployed-pct"})
    index = 0

    config = master_config.copy()
    # iterate event resource requirement
    for s in master_config["event_resources"]:
      config["event_resources"] = s
      # iterate event start
      for t in master_config["event_start"]:
        config["event_start"] = t
        if "event_locations" not in master_config:
          for l in locations:
            config["event_locations"] = l
            #print(config)
            run(config, index, results)
            index += 1
        else:
          #print(config)
          run(config, index, results)
          index += 1

  print(results)
  print("Runtime: %ss" % (time.time() - start_time))

