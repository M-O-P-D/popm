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

  dep_times = deployments[["DeployedPct"]].unstack(level=1)#.drop(24.0, axis=1)
  dep_times.columns = dep_times.columns.droplevel().astype(str)

  # drop 24h as dep=0 (event has ended)
  dep_times = dep_times.drop(["24.0"], axis=1)


  dep_times["dep10"] = np.nan
  dep_times["dep40"] = np.nan
  dep_times["dep60"] = np.nan
  dep_times["dep100"] = np.nan


  # this works with flat functions
  def interp(deplevel, deps, times):
    for i in range(len(times)):
      if deps[i] >= deplevel: return times[i]
    return 24.0 # this indicates event not fully resourced where it ends

  t = np.arange(0.0, 24.0, 1.0)
  for i,r in dep_times.iterrows():
    #print(i)
    r["dep10"] = interp(10.0, r.values[:24], t)
    r["dep40"] = interp(40.0, r.values[:24], t)
    r["dep60"] = interp(60.0, r.values[:24], t)
    r["dep100"] = interp(100.0, r.values[:24], t)
  
  dep_times = dep_times.drop([str(i) for i in t], axis=1)
  print(dep_times)
  dep_times.to_csv(path / "deployment_times.csv")
#print(df.columns.values)


def visualise(scenario):
  path = Path(f"./model-output/{scenario}")

  dep_times = pd.read_csv(path / "deployment_times.csv", index_col=["RunId", "Event"])
  print(dep_times.head())

  fig, axs = plt.subplots(nrows=4, figsize=(15,18), sharex=True)
  i = 0
  for dep in ["dep10", "dep40", "dep60", "dep100"]:
    dep_time = dep_times[dep].unstack()
    axs[i] = sns.boxplot(ax=axs[i], data=dep_time, showfliers = False)#, boxprops=dict(alpha=.3))
    plt.xticks(rotation=90)
    axs[i].set_xlabel("")
    axs[i].set_ylabel("Time to %s%% deployment (hours)" % dep.replace("dep", ""))
    i = i + 1

  axs[3].set_xlabel("Event location")
  fig.suptitle(scenario.replace("events", " simultaneous public order events"), y=0.99)
  plt.tight_layout()
  plt.savefig(f"./doc/{scenario}.png", bbox_inches="tight")
  plt.show()

def summarise(scenario):
  path = Path(f"./model-output/{scenario}")

  dep_times = pd.read_csv(path / "deployment_times.csv", index_col=["RunId", "Event"])
  print(dep_times.head())

  #i = 0
  # for dep in ["dep10", "dep40", "dep60", "dep100"]:
  #   dep_time = dep_times[dep].unstack()
  #   print(dep_time.mean())
  #   break
  # mean_dep_times = pd.concat([dep_times[dep].unstack().mean() for dep in ["dep10", "dep40", "dep60", "dep100"] ], axis=1)
  # print(mean_dep_times)

  mean_dep_times = pd.DataFrame(data={dep: dep_times[dep].unstack().mean() for dep in ["dep10", "dep40", "dep60", "dep100"] })
  print(mean_dep_times)
  mean_dep_times.to_csv(path / "mean_dep_times.csv")

  #print(dep_times["dep10"].unstack())

  stddev_dep_times = pd.DataFrame(data={dep: dep_times[dep].unstack().std() for dep in ["dep10", "dep40", "dep60", "dep100"] })
  print(stddev_dep_times)
  stddev_dep_times.to_csv(path / "stddev_dep_times.csv")


if __name__ == "__main__":
  assert len(sys.argv) == 2
  analysis(sys.argv[1])
  summarise(sys.argv[1])
  #visualise(sys.argv[1])
