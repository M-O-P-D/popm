import pandas as pd
import numpy as np
from pathlib import Path
import sys

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
       'Wiltshire', 'Avon and Somerset', 'Beds Cambs Herts', 'Cheshire',
       'City of London', 'Cleveland', 'Cumbria', 'Derbyshire',
       'Devon and Cornwall', 'Dorset', 'Durham', 'Dyfed-Powys', 'Essex',
       'Gloucestershire', 'Greater Manchester', 'Gwent', 'Hampshire',
       'Humberside', 'Kent', 'Lancashire', 'Leicestershire',
       'Lincolnshire', 'Merseyside', 'Metropolitan Police', 'Norfolk',
       'North Wales', 'North Yorkshire', 'Northamptonshire',
       'Northumbria', 'Nottinghamshire', 'South Wales', 'South Yorkshire',
       'Staffordshire', 'Suffolk', 'Surrey', 'Sussex', 'Thames Valley',
       'Warwickshire', 'West Mercia', 'West Midlands', 'West Yorkshire',
       'Wiltshire', 'Avon and Somerset', 'Beds Cambs Herts', 'Cheshire',
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

  df = deployments[["DeployedPct"]].unstack(level=1)#.drop(24.0, axis=1)
  df.columns = df.columns.droplevel().astype(str)

  # drop 24h as dep=0 (event has ended)
  df = df.drop(["24.0"], axis=1)


  df["dep10"] = np.nan
  df["dep40"] = np.nan
  df["dep60"] = np.nan
  df["dep100"] = np.nan


  # this works with flat functions
  def interp(deplevel, deps, times):
    for i in range(len(times)):
      if deps[i] >= deplevel: return times[i]
    return 24.0 # this indicates event not fully resourced where it ends

  t = np.arange(0.0, 24.0, 1.0)
  for i,r in df.iterrows():
    print(i)
    r["dep10"] = interp(10.0, r.values[:24], t)
    r["dep40"] = interp(40.0, r.values[:24], t)
    r["dep60"] = interp(60.0, r.values[:24], t)
    r["dep100"] = interp(100.0, r.values[:24], t)
  
  df = df.drop([str(i) for i in t], axis=1)
  print(df)
  df.to_csv(path / "deployment_times.csv")
#print(df.columns.values)


#  print(df)

  # reqs = [10.0, 40.0, 60.0, 100.0]
  # for req in reqs:

    # df = deployments[deployments.DeployedPct >= req][["DeployedPct"]]
    # print(df.droplevel())
    # print(df.groupby(level=(0,2)).min())
  
    # for force in forces:
    #   #print(deployments[(deployments.index.get_level_values("Event") == force) & (deployments.DeployedPct >= req)]["DeployedPct"].idxmin()) # head(20))
    #   print(deployments[(deployments.index.get_level_values("Event") == force) & (deployments.DeployedPct >= req)]) #.min(level="Time"))
    #   #print(deployments.query(f'Time=={t} and Event=="{force}"').DeployedPct)
    #   break



if __name__ == "__main__":
  assert len(sys.argv) == 2
  analysis(sys.argv[1])
