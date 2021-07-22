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
from popm.utils import sample_all_locations, sample_locations_quasi, run_context, adjust_staffing # <- TODO
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
    centroids,
    config.get("ignore_alliance", False))
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
    # - if a string use pre-specified random or fixed locations
    if "event_locations" not in master_config:
      locations = sample_all_locations(n_locations, master_config["no_of_events"])
    elif isinstance(master_config["event_locations"], int):
      locations = sample_locations_quasi(n_locations, master_config["no_of_events"], master_config["event_locations"])
    elif isinstance(master_config["event_locations"], str) and master_config["event_locations"] == "Breaking Point":
      # locations = 6*[list(force_data.name[force_data.name.isin(["Metropolitan Police", "Greater Manchester", "West Midlands"])].index)]
      # this hack ensures all 6 permutations are simulated after the event order has been randomised (only for seed 19937!)
      locations = [[13,22,38]] * 4 + [[38,22,13], [38,13,22]]
    else:
      locations = master_config["event_locations"]
    n_runs *= len(locations)

    print("Total runs = %d" % n_runs)

    # make run_no unique across multiple processes (note exact no. of runs might be different for each process, so just offset by 1e6)
    run_no = rank * 1000000

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

  rank, size = run_context()

  if size == 1:
    # single-process case
    deployment_times.to_csv(path / "deployment_times.csv", index=False)
    active_psus.to_csv(path / "active_psus.csv", index=False)
  else:
    # root process gets data from all the others and writes it
    from mpi4py import MPI
    comm = MPI.COMM_WORLD

    all_deployment_times = comm.gather(deployment_times, root=0)
    all_active_psus = comm.gather(active_psus, root=0)
    if rank == 0:
      pd.concat(all_deployment_times).to_csv(path / "deployment_times.csv", index=False)
      pd.concat(all_active_psus).to_csv(path / "active_psus.csv", index=False)

  print("Runtime: %ss" % (time.time() - start_time))

