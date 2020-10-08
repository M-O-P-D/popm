""" batch mode """

# TODO look into Mesa's BatchRunner class...

import json
import time
import pandas as pd
import argparse
import warnings
from collections import Counter

# suppress deprecation warning we can't do anything about
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import geopandas as gpd
from shapely import wkt

from popm.model import PublicOrderPolicing
from popm.agents import ForcePSUAgent
from popm.utils import sample_locations
from popm.initialisation import load_force_data, PSU_OFFICERS

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
force_data = load_force_data()


def run(config, run_no, results):

  model = PublicOrderPolicing(
    config["no_of_events"],
    config["event_resources"],
    config["event_start"],
    config["event_duration"],
    config["staff_absence"],
    config["timestep"],
    config["event_locations"],
    routes,
    force_data)

  allocation_data = [(a.assigned_to, a.name) for a in model.schedule.agents if isinstance(a, ForcePSUAgent) and a.assigned]
  allocations = pd.DataFrame.from_dict(Counter(allocation_data), orient="index", columns=["PSUs"]).reset_index()
  # split the to, from column
  allocations["EventForce"] = allocations["index"].apply(lambda e: e[0])
  allocations["HomeForce"] = allocations["index"].apply(lambda e: e[1])
  allocations["EventAlliance"] = allocations["EventForce"].apply(lambda e: force_data[force_data.name == e]["Alliance"].values[0])
  allocations["HomeAlliance"] = allocations["HomeForce"].apply(lambda e: force_data[force_data.name == e]["Alliance"].values[0])
  allocations["Alliance"] = allocations["EventAlliance"] == allocations["HomeAlliance"]
  allocations["RunId"] = run_no
  allocations["Requirement"] = config["event_resources"] / PSU_OFFICERS
  allocations.drop(["index", "EventAlliance", "HomeAlliance"], axis=1, inplace=True)

  print(allocations)

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

  return agent_data, allocations


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

    # if event_locations is an array, its assumed that this is a pre-specifed location
    # NB model also supports a string: Fixed/Random/Breaking Point
    # Get all combinations for given number of events, subject to a maximum if specified

    # TODO check array of event_locations works correctly

    if "event_locations" not in master_config or isinstance(master_config["event_locations"], int):
      locations = sample_locations(n_locations, master_config["no_of_events"], master_config.get("event_locations", None))
    else:
      locations = [master_config["event_locations"]]
    n_runs *= len(locations)

    print("Total runs = %d" % n_runs)

    results = pd.DataFrame(columns={"Deployed(%)", "Allocated(%)", "Time", "Event", "RunId", "Events", "EventStart", "EventDuration"})
    allocations = pd.DataFrame(columns={"EventForce", "HomeForce", "Alliance", "PSUs", "RunId"})

    run_no = 0

    config = master_config.copy()
    # iterate event resource requirement
    for s in master_config["event_resources"]:
      config["event_resources"] = s
      # iterate event start
      for t in master_config["event_start"]:
        config["event_start"] = t
        for l in locations:
          config["event_locations"] = l
          #print(config)
          agents, allocs = run(config, run_no, results)
          results = results.append(agents, ignore_index=True)
          allocations = allocations.append(allocs, ignore_index=True)
          run_no += 1

  results.to_csv(args.outfile, index=False)
  allocations.to_csv(args.outfile.replace(".csv", "_allocations.csv"), index=False)
  print("Runtime: %ss" % (time.time() - start_time))

