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
       'Wiltshire']

def analysis(scenario):
  path = Path(f"./model-output/{scenario}")
  #allocations = pd.read_csv(path / "acitve_psus.csv", index_col=["RunId", "EventForce", "AssignedForce"])
  deployments = pd.read_csv(path / "deployment_times.csv").set_index(["RunId", "location", "requirement_frac"])#.unstack(level=[1,2]) #.unstack(level=2)
  #print(allocations)
  #deployments = deployments[deployments.index.get_level_values("location") == "Greater Manchester"]
  #deployments.to_csv("./gm.csv")
  print(deployments)

  means = deployments["actual"].unstack(level=[1,2]).mean().unstack(level=1).add_prefix("mean-")
  print(means)

  stddevs = deployments["actual"].unstack(level=[1,2]).std().unstack(level=1).add_prefix("stddev-")
  print(stddevs)

  means.merge(stddevs, left_index=True, right_index=True).to_csv(f"{scenario}_summary.csv")

  # # appearances = {force: len(locations[locations.EventLocations.str.contains(force)]) for force in forces}

  # appearances = pd.DataFrame(data={"Force": forces})
  # appearances["Appearances"] = appearances.Force.apply(lambda force: len(locations[locations.EventLocations.str.contains(force)]))
  # appearances = appearances.drop_duplicates() \
  #                          .set_index("Force") \
  #                          .sort_values(by="Appearances")

  # print(appearances.to_string())
  # print(appearances.mean())

  # # subtract mobilisation times
  # deployments.Hit10Pct -= 1.0
  # deployments.Hit40Pct -= 4.0
  # deployments.Hit60Pct -= 8.0
  # deployments.Hit100Pct -= 16.0

  # print(deployments)
  # # need to drop metric as it persists as an index level
  # means = pd.DataFrame(data={ metric: deployments[[metric]].unstack(level=1).mean().droplevel(0) for metric in ["Hit10Pct", "Hit40Pct", "Hit60Pct", "Hit100Pct"]}) \
  #   .add_prefix("mean-")

  # stddevs = pd.DataFrame(data={ metric: deployments[[metric]].unstack(level=1).std().droplevel(0) for metric in ["Hit10Pct", "Hit40Pct", "Hit60Pct", "Hit100Pct"]}) \
  #   .add_prefix("stddev-")

  # dep_times = means.merge(stddevs, left_index=True, right_index=True)

  # print(dep_times)
  # #assert len(dep_times) == 41
  # dep_times.to_csv(f"./{scenario}_dep_times.csv")


if __name__ == "__main__":
  assert len(sys.argv) == 2
  analysis(sys.argv[1])
  #visualise(sys.argv[1])
