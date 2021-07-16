

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from math import ceil
from .initialisation import load_force_data, create_psu_data, initialise_event_data
from .negotiation2 import allocate

MOBILISATION_TIMES = {
  1: 0.1, # 10% in 1 hour
  4: 0.4, # 40% in 4 hours
  8: 0.6,  # 60% in 8 hours
  16: 1.0 # NB this figure is not part of the nationally recornised public order mobilsation timelines
}


class SimpleModel():

  def __init__(self, event_locations, event_resources, event_start=0, event_duration=24):

    self.event_locations = event_locations

    f, c = load_force_data()

    df = pd.read_csv("./data/force_centroid_routes.zip")
    df["geometry"] = df["geometry"].apply(wkt.loads)
    df["time"] = df["time"] / 3600.0 # convert travel time seconds to hours
    self.routes = gpd.GeoDataFrame(df).set_index(["origin", "destination"])

    self.psus = create_psu_data(f, c)

    self.psus["mobilisation"] = 1.0
    self.psus["deployment"] = np.nan

    for force in self.psus.name.unique():
      n = len(self.psus[self.psus.name == force])

      mob = [1.0] * int(ceil(MOBILISATION_TIMES[1] * n))
      mob.extend([4.0] * (int(ceil(MOBILISATION_TIMES[4] * n)) - len(mob)))
      mob.extend([8.0] * (int(ceil(MOBILISATION_TIMES[8] * n)) - len(mob)))
      mob.extend([16.0] * (n - len(mob)))

      self.psus.loc[self.psus.name == force, "mobilisation"] = np.array(mob)

      print(n, mob)


    self.event_data = initialise_event_data(self, event_resources, event_start, event_duration, f, c)

    allocate(self.event_data, f, self.psus, self.routes)
    print(self.psus)
