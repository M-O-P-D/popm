# %%
import json
from popm.model import PublicOrderPolicing

with open("./scenario/fixed.json") as f:
  config = json.load(f)

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

agent_data.head()

# %%

def get_name(id):
  for a in model.schedule.agents:
    if a.unique_id == id:
      return a.name
  return str(id)

from matplotlib import pyplot as plt

%matplotlib inline

ids = agent_data.index.get_level_values("AgentID").unique().values

#agent_data.xs(129, level="AgentID").plot()

cols = ["Required", "Allocated", "Present"]

fig, axs = plt.subplots(len(ids), sharex=True, figsize=(10,10))

for i, id in enumerate(ids):
  df = agent_data.xs(id, level="AgentID")

  axs[i].plot(df.Time, df[cols])
  axs[i].set_title(get_name(id))
  #axs[i].set_xlabel("Time (h)")
  axs[i].set_ylabel("Officers")
fig.legend(cols);
axs[-1].set_xlabel("Time (h)");



# %%

