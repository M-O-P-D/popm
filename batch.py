""" batch mode """

# TODO look into Mesa's BatchRunner class...

import json
import time
import pandas as pd
import geopandas as gpd
from shapely import wkt
import argparse
from itertools import combinations
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

def run(config, runs):

  for _ in range(runs):
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

    # model_data = model.datacollector.get_model_vars_dataframe()
    # print(model_data)
    agent_data = model.datacollector.get_agent_vars_dataframe().dropna()

    # change required to zero before event
    # agent_data.loc[agent_data["Active"] == False, "Required"] = 0.0

    ids = agent_data.index.get_level_values("AgentID").unique().values

    # TODO get KPI metrics

    #cols = ["Deployed"] #, "Allocated", "Present"]
    # fig, axs = plt.subplots(len(ids), sharex=True, figsize=(6,8))
    # for i, unique_id in enumerate(ids):
    #   df = agent_data.xs(unique_id, level="AgentID")
    #   axs[i].plot(df.index.values, df[cols])
    #   axs[i].set_title(get_name(model, unique_id))
    #   #axs[i].set_xlabel("Time (h)")
    #   axs[i].set_ylabel("Officers")
    # fig.legend(cols)
    # axs[-1].set_xlabel("Time (h)")

    # # agent_data.plot()
    # plt.show()

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
            run(config, 1)
        else:
          #print(config)
          run(config, 1)

  print("Runtime: %ss" % (time.time() - start_time))

