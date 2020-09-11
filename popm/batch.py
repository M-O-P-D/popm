""" batch mode """

import json
import argparse
from .model import PublicOrderPolicing

def main(config, runs):

  # no_of_events = 3
  # event_resources = 1000
  # event_start = 2
  # event_duration = 8
  # staff_absence = 0.02
  # timestep = 15
  # event_locations = "Fixed"

  for r in range(runs):
    model = PublicOrderPolicing(
      config["no_of_events"],
      config["event_resources"],
      config["event_start"],
      config["event_duration"],
      config["staff_absence"],
      config["timestep"],
      config["event_locations"])

    model.run_model()

    # model_data = model.datacollector.get_model_vars_dataframe()
    # print(model_data)
    # agent_data = model.datacollector.get_agent_vars_dataframe()
    # print(agent_data)

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="popm batch run")
  parser.add_argument("config", type=str, help="the model configuration file (json)")
  parser.add_argument("runs", type=int, help="the number of runs to execute")
  args = parser.parse_args()
  # load config
  with open(args.config) as f:
    config = json.load(f)
    print(config)
    main(config, args.runs)

