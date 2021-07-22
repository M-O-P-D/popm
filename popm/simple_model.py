

import numpy as np
import pandas as pd
import geopandas as gpd
from pandas.core.indexes.api import all_indexes_same
from shapely import wkt
from math import ceil
from .initialisation import PSU_OFFICERS, load_force_data, create_psu_data, initialise_event_data
from .negotiation_simple import allocate

MOBILISATION_TIMES = {
  1: 0.1, # 10% in 1 hour
  4: 0.4, # 40% in 4 hours
  8: 0.6,  # 60% in 8 hours
  16: 1.0 # NB this figure is not part of the nationally recognised public order mobilsation timelines
}


class PublicOrderPolicing():

  def __init__(self, event_locations, event_resources, event_start, event_duration, routes, force_data, centroids, ignore_alliance=False):

    self.event_locations = event_locations

    self.routes = routes

    self.psus = create_psu_data(force_data, centroids).drop(["geometry", "dispatched", "deployed"], axis=1)

    self.psus["mobilisation"] = 1.0
    self.psus["travel"] = np.nan

    for force in self.psus.name.unique():
      n = len(self.psus[self.psus.name == force])

      mob = [1.0] * int(ceil(MOBILISATION_TIMES[1] * n))
      mob.extend([4.0] * (int(ceil(MOBILISATION_TIMES[4] * n)) - len(mob)))
      mob.extend([8.0] * (int(ceil(MOBILISATION_TIMES[8] * n)) - len(mob)))
      mob.extend([16.0] * (n - len(mob)))

      self.psus.loc[self.psus.name == force, "mobilisation"] = np.array(mob)

    self.event_data = initialise_event_data(self, event_resources, event_start, event_duration, force_data, centroids)

    print(f"Simulating events in {self.event_data.name.values}")

    # if ignore_alliance flag is set, each force is in alliance with itself only, apart from Met/City of London
    if ignore_alliance:
      self.psus.loc[self.psus.Alliance != "LONDON", "Alliance"] = self.psus.name

    allocate(self.event_data, force_data, self.psus, self.routes)

    assert np.all(self.event_data.resources_required - self.event_data.resources_allocated == 0), "event(s) not fully allocated"


  def location_names(self):
    return list(filter(None, self.psus.assigned_to.unique()))

  def run_model(self):
    """
    Produces times at which *deployment* of 10%, 40%, 60% and 100% are achieved for each event location,
    based on the nationally recognised mobilisation timelines and travel times
    """

    active = self.psus[self.psus.assigned == True].copy()
    active["deployed"] = active["mobilisation"] + active["travel"]

    dep_times = pd.DataFrame()

    for _, r in self.event_data.iterrows():
      req = r["resources_required"] // PSU_OFFICERS

      result = pd.DataFrame(data={"location": r["name"], "total_requirement": req, "mobilisation_time": MOBILISATION_TIMES.keys()}) #, "time": np.nan})
      result["requirement_frac"] = result.mobilisation_time.apply(lambda k: MOBILISATION_TIMES[k])
      result["requirement"] = np.ceil(result.requirement_frac * req).astype(np.int64)
      # take the i'th deployment time from a sorted array of deployment times to get the time at which i are deployed 
      result["actual"] = result.requirement.apply(lambda i: active[active.assigned_to==r["name"]].sort_values("deployed").head(i)["deployed"].values[-1])

      dep_times = dep_times.append(result)

    return dep_times, active


