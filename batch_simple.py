""" batch mode """

# TODO look into Mesa's BatchRunner class...

import json
import time
import pandas as pd
import argparse
#from collections import Counter
from pathlib import Path
import shutil

# suppress deprecation warning we can't do anything about
import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import geopandas as gpd
from shapely import wkt

import humanleague as hl

from popm.simple_model import PublicOrderPolicing
from popm.utils import sample_all_locations, sample_locations_quasi, run_context, collate_and_write_results, adjust_staffing
from popm.initialisation import load_force_data, PSU_OFFICERS, CORE_FUNCTIONS


# load this data once only (its a bottleneck and its constant anyway)
df = pd.read_csv("./data/force_centroid_routes.zip")
df["geometry"] = df["geometry"].apply(wkt.loads)
df["time"] = df["time"] / 3600.0 # convert travel time seconds to hours
routes = gpd.GeoDataFrame(df).set_index(["origin", "destination"])
n_locations = len(routes.index.levels[0])
force_data, centroids = load_force_data()


def run(config, run_no):

  model = PublicOrderPolicing(
    config["event_locations"],
    config["event_resources"],
    config["event_start"],
    config["event_duration"],
    routes,
    force_data,
    centroids)
  return model.run_model()


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

    # location_lookup = pd.DataFrame(index=range(run_no, run_no+n_runs), columns={"EventLocations": ""})
    # location_lookup.index.rename("RunId", inplace=True)
    # deployments = pd.DataFrame(columns=["RunId", "Time", "Event", "Events", "EventStart", "EventDuration", "DeployedPct", "AllocatedPct"])
    # allocations = pd.DataFrame(columns=["RunId", "EventForce", "AssignedForce", "Alliance", "PSUs"])
    # resources = pd.DataFrame()

    # resources_baseline = adjust_staffing(force_data[["name", "Alliance", "Officers", "POP"] \
    #   + CORE_FUNCTIONS + [c+"_POP" for c in CORE_FUNCTIONS] + [c+"_MIN" for c in CORE_FUNCTIONS]],
    #   master_config["staff_absence"]/100, master_config["duty_ratio"]/100)

    deployment_times = pd.DataFrame(columns=["RunId"])
    active_psus = pd.DataFrame(columns=["RunId"])

    config = master_config.copy()
    # iterate event resource requirement
    for s in master_config["event_resources"]:
      config["event_resources"] = s
      # iterate event start
      for t in master_config["event_start"]:
        config["event_start"] = t
        for l in locations:
          config["event_locations"] = l
          #agents, allocs,
          d, p = run(config, run_no)#, resources_baseline)
          d["RunId"] = run_no
          p["RunId"] = run_no
          #location_lookup.loc[run_no, "EventLocations"] = "/".join(sorted(allocs.EventForce.unique()))
          deployment_times = deployment_times.append(d, ignore_index=True)
          active_psus = active_psus.append(p, ignore_index=True)
          # allocations = allocations.append(allocs, ignore_index=True)
          # resources = resources.append(res, ignore_index=True)
          run_no += 1

  #collate_and_write_results(args.config, location_lookup, deployments, allocations, resources, resources_baseline)
  path = Path(args.config.replace("scenario", "model-output").replace(".json", "/"))
  path.mkdir(parents=True, exist_ok=True)
  shutil.copy(args.config, path)
  deployment_times.to_csv(path / "deployment_times.csv", index=False)
  active_psus.to_csv(path / "active_psus.csv", index=False)

  print("Runtime: %ss" % (time.time() - start_time))

