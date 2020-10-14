""" batch mode """

# TODO look into Mesa's BatchRunner class...

import json
import time
import pandas as pd
import argparse
from collections import Counter

# suppress deprecation warning we can't do anything about
import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import geopandas as gpd
from shapely import wkt

from popm.model import PublicOrderPolicing
from popm.agents import ForcePSUAgent
from popm.utils import sample_all_locations, sample_locations_quasi, run_context
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


def run(config, run_no):

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
  allocations["AssignedForce"] = allocations["index"].apply(lambda e: e[1])
  allocations["EventAlliance"] = allocations["AssignedForce"].apply(lambda e: force_data[force_data.name == e]["Alliance"].values[0])
  allocations["AssignedAlliance"] = allocations["AssignedForce"].apply(lambda e: force_data[force_data.name == e]["Alliance"].values[0])
  allocations["Alliance"] = allocations["EventAlliance"] == allocations["AssignedAlliance"]
  allocations["RunId"] = run_no
  allocations["Requirement"] = config["event_resources"] / PSU_OFFICERS
  allocations.drop(["index", "EventAlliance", "AssignedAlliance"], axis=1, inplace=True)
  model.run_model()

  # indices for KPI metrics
  # index_1h = (config["event_start"] + 1) / model.timestep
  # index_4h = (config["event_start"] + 4) / model.timestep
  # index_8h = (config["event_start"] + 8) / model.timestep
  indices_1h = [(config["event_start"] + h) / model.timestep for h in range(25) ]

  agent_data = model.datacollector.get_agent_vars_dataframe().dropna()
  agent_data = agent_data.loc[agent_data.index.isin(indices_1h, level="Step")]
  agent_data.Allocated *= 100.0 / config["event_resources"]
  agent_data.Deployed *= 100.0 / config["event_resources"]
  agent_data.rename({"Allocated": "AllocatedPct", "Deployed": "DeployedPct"}, axis=1, inplace=True)
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
  args = parser.parse_args()

  start_time = time.time()

  rank, size = run_context()

  # load config
  with open(args.config) as f:
    master_config = json.load(f)

    n_runs = len(master_config["event_resources"]) * len(master_config["event_start"])

    # NB model also supports a string: Fixed/Random/Breaking Point
    # Get all combinations for given number of events, subject to a maximum if specified

    # event_locations sampling behaviour:
    # - if not specifed, sample all combinations
    # - if an integer, sample that many combinations
    # - if an array, use the values as the event locations (each one itself an array)
    # - if a string [web client only], use pre-specified random or fixed locations
    if "event_locations" not in master_config:
      locations = sample_all_locations(n_locations, master_config["no_of_events"])
    elif isinstance(master_config["event_locations"], int):
      locations = sample_locations_quasi(n_locations, master_config["no_of_events"], master_config["event_locations"])
    else:
      locations = master_config["event_locations"]
    n_runs *= len(locations)

    print("Total runs = %d" % n_runs)
    # make run_no unique across multiple processes (note exact no. of runs might be different for each process, so just offset by 1e6)
    run_no = rank * 1000000

    location_lookup = pd.DataFrame(index=range(run_no, run_no+n_runs), columns={"EventLocations": ""})
    location_lookup.index.rename("RunId", inplace=True)
    deployments = pd.DataFrame(columns=["RunId", "Time", "Event", "Events", "EventStart", "EventDuration", "DeployedPct", "AllocatedPct"])
    allocations = pd.DataFrame(columns=["RunId", "EventForces", "EventForce", "AssignedForce", "Alliance", "PSUs"])

    config = master_config.copy()
    # iterate event resource requirement
    for s in master_config["event_resources"]:
      config["event_resources"] = s
      # iterate event start
      for t in master_config["event_start"]:
        config["event_start"] = t
        for l in locations:
          config["event_locations"] = l
          agents, allocs = run(config, run_no)
          location_lookup.loc[run_no, "EventLocations"] = "/".join(sorted(allocs.EventForce.unique()))
          deployments = deployments.append(agents, ignore_index=True)
          allocations = allocations.append(allocs, ignore_index=True)
          run_no += 1

  location_lookup.to_csv(args.config.replace(".json", "_locations%d-%d.csv" % (rank, size)))
  deployments.to_csv(args.config.replace(".json", "%d-%d.csv" % (rank, size)), index=False)
  allocations.to_csv(args.config.replace(".json", "_allocations%d-%d.csv" % (rank, size)), index=False)
  print("Runtime: %ss" % (time.time() - start_time))

