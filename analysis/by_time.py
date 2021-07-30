import pandas as pd
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
       'Wiltshire']

def analysis(scenario):
  path = Path(f"./model-output/{scenario}")
  #allocations = pd.read_csv(path / "active_psus.csv", index_col=["RunId", "EventForce", "AssignedForce"])
  deployments = pd.read_csv(path / "deployment_times.csv").set_index(["RunId", "location", "requirement_frac"])#.unstack(level=[1,2]) #.unstack(level=2)
  #print(deployments)

  means = deployments["actual"].unstack(level=[1,2]).mean().unstack(level=1).add_prefix("mean-")

  # for col in ["mean-0.1", "mean-0.4", "mean-0.6", "mean-1.0"]:
  #   means[col] = means[col].apply(lambda t: f"{int(t)}h{int(t*60)%60}m")
  #means = means.apply(lambda t: f"{int(t)}h{int(t*60)%60}m")
  print(means)

  stddevs = deployments["actual"].unstack(level=[1,2]).std().unstack(level=1).add_prefix("stddev-")
  print(stddevs)

  means.merge(stddevs, left_index=True, right_index=True).to_csv(f"./model-output/{scenario}_summary.csv")


if __name__ == "__main__":
  assert len(sys.argv) == 2
  analysis(sys.argv[1])
  #visualise(sys.argv[1])
