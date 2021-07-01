import pandas as pd
import numpy as np
from pathlib import Path
import sys

import seaborn as sns
import matplotlib.pyplot as plt

forces = ['Avon and Somerset', 'Beds Cambs Herts', 'Cheshire',
       'City of London', 'Cleveland', 'Cumbria', 'Derbyshire',
       'Devon and Cornwall', 'Dorset', 'Durham', 'Dyfed-Powys', 'Essex',
       'Gloucestershire', 'Greater Manchester', 'Gwent', 'Hampshire',
       'Humberside', 'Kent', 'Lancashire', 'Leicestershire',
       'Lincolnshire', 'Merseyside', 'Metropolitan Police', 'Norfolk',
       'North Wales', 'North Yorkshire', 'Northamptonshire',
       'Northumbria', 'Nottinghamshire', 'South Wales', 'South Yorkshire',
       'Staffordshire', 'Suffolk', 'Surrey', 'Sussex', 'Thames Valley',
       'Warwickshire', 'West Mercia', 'West Midlands', 'West Yorkshire',
       'Wiltshire']

def analysis(scenario):
  path = Path(f"./model-output/{scenario}")
  allocations = pd.read_csv(path / "allocations.csv", index_col=["RunId", "EventForce", "AssignedForce"])
  deployments = pd.read_csv(path / "deployments.csv", index_col=["RunId", "Time", "Event"])
  locations = pd.read_csv(path / "locations.csv", index_col="RunId")

  print(allocations)
  print(deployments)
  print(locations)
  print(locations.columns.values)

  # appearances = {force: len(locations[locations.EventLocations.str.contains(force)]) for force in forces}

  appearances = pd.DataFrame(data={"Force": forces})
  appearances["Appearances"] = appearances.Force.apply(lambda force: len(locations[locations.EventLocations.str.contains(force)]))
  appearances = appearances.drop_duplicates() \
                           .set_index("Force") \
                           .sort_values(by="Appearances")

  print(appearances.to_string())
  print(appearances.mean())

  print(deployments.head())

  deployments = deployments[deployments.index.get_level_values("Time") < 24.0]

  fig, axs = plt.subplots(7,6, figsize=(15,15), sharex=True, sharey=True)
  fig.suptitle("Deployment times, "+scenario.replace("events", " simultaneous public order events"), y=0.99)
  #print(axs)

  for i, force in enumerate(forces):
    y, x = i // 6, i % 6
    print(i, x, y, force)
    dept = deployments.xs(force, level="Event")["DeployedPct"].unstack(level=0)
    # #print(dept)
    dept.plot(ax=axs[y,x], legend=False)
    axs[y,x].set_title(force)
  plt.xlabel("Time (hours)")
  plt.ylabel("Deployment (%)")
  plt.tight_layout()
  plt.savefig(f"./doc/{scenario}-deptime.png", bbox_inches="tight")
  #plt.show()




if __name__ == "__main__":
  assert len(sys.argv) == 2
  analysis(sys.argv[1])
  #visualise(sys.argv[1])
