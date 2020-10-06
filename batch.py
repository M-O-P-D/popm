""" batch mode """

# TODO look into Mesa's BatchRunner class...

import json
import time
import pandas as pd
import argparse
from itertools import combinations
import warnings
#import humanleague

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

def run(config, run_no, results):

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

  #model_data = model.datacollector.get_model_vars_dataframe() * 100.0 / config["event_resources"] / config["no_of_events"]
  #print(model_data.loc[[index_1h, index_4h]])
  # indices for KPI metrics
  index_1h = (config["event_start"] + 1) / model.timestep
  index_4h = (config["event_start"] + 4) / model.timestep
  index_8h = (config["event_start"] + 8) / model.timestep

  agent_data = model.datacollector.get_agent_vars_dataframe().dropna()
  agent_data = agent_data.loc[agent_data.index.isin([index_1h, index_4h, index_8h], level="Step")]
  agent_data.Allocated *= 100.0 / config["event_resources"]
  agent_data.Deployed *= 100.0 / config["event_resources"]
  agent_data.rename({"Allocated": "Allocated(%)", "Deployed": "Deployed(%)"}, axis=1, inplace=True)
  agent_data["Time"] = agent_data.index.get_level_values(0) * config["timestep"] / 60
  agent_data["Event"] = [get_name(model, uid) for uid in agent_data.index.get_level_values(1)]
  agent_data["RunId"] = run_no
  agent_data["Events"] = config["no_of_events"]
  agent_data["EventStart"] = config["event_start"]
  agent_data["EventDuration"] = config["event_duration"]

  return agent_data


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="popm batch run")
  parser.add_argument("config", type=str, help="the model configuration file (json)")
  parser.add_argument("outfile", type=str, help="the output csv file")
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

    results = pd.DataFrame(columns={"Deployed(%)", "Allocated(%)", "Time", "Event", "RunId", "Events", "EventStart", "EventDuration"})

    run_no = 0

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
            results = results.append(run(config, run_no, results), ignore_index=True)
            run_no += 1
        else:
          #print(config)
          results = results.append(run(config, run_no, results), ignore_index=True)
          run_no += 1

  results.to_csv(args.outfile, index=False)
  print("Runtime: %ss" % (time.time() - start_time))

