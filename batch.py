""" batch mode """

# TODO look into Mesa's BatchRunner class...

import json
import argparse
from popm.model import PublicOrderPolicing

from matplotlib import pyplot as plt

def get_name(model, id):
  for a in model.schedule.agents:
    if a.unique_id == id:
      return a.name
  return str(id)


def main(config, runs):

  for _ in range(runs):
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
    agent_data = model.datacollector.get_agent_vars_dataframe().dropna()

    # change required to zero before event
    agent_data.loc[agent_data["Active"] == False, "Required"] = 0.0

    ids = agent_data.index.get_level_values("AgentID").unique().values

    #agent_data.xs(129, level="AgentID").plot()

    cols = ["Required", "Allocated", "Present"]

    fig, axs = plt.subplots(len(ids), sharex=True, figsize=(6,8))

    for i, id in enumerate(ids):
      df = agent_data.xs(id, level="AgentID")

      axs[i].plot(df.Time, df[cols])
      axs[i].set_title(get_name(model, id))
      #axs[i].set_xlabel("Time (h)")
      axs[i].set_ylabel("Officers")
    fig.legend(cols)
    axs[-1].set_xlabel("Time (h)")

    # agent_data.plot()
    plt.show()

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="popm batch run")
  parser.add_argument("config", type=str, help="the model configuration file (json)")
  parser.add_argument("runs", nargs="?", type=int, default=1, help="the number of runs to execute, default 1")
  args = parser.parse_args()

  # load config
  with open(args.config) as f:
    config = json.load(f)
    
    main(config, args.runs)
