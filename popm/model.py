from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import AgentCreator # GeoAgent
from mesa_geo import GeoSpace

import pandas as pd
import geopandas as gpd
import numpy as np

from .agents import ForceAreaAgent, ForceCentroidAgent, ForcePSUAgent
from .initialisation import load_data, create_psu_data, initialise_events
from .negotiation import allocate

class PublicOrderPolicing(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """
  def __init__(self, no_of_events, event_resources, event_duration, staff_absence): #params...

    self.log = ["Initialising model"]

    self.datacollector = DataCollector(model_reporters={})

    # Set up the grid and schedule.

    # Use SimultaneousActivation which simulates all the cells
    # computing their next state simultaneously.  This needs to
    # be done because each cell's next state depends on the current
    # state of all its neighbors -- before they've changed.
    self.schedule = SimultaneousActivation(self)

    # Use a multi grid so that >1 agent can occupy the same location
    self.grid = GeoSpace()

    # Ultra Generalised Clipped otherwise too much rendering
    boundaries, centroids, _distances = load_data()

    # create PSUs
    psu_data = create_psu_data(boundaries, centroids, staff_absence)

    # Set up the force agents
    factory = AgentCreator(ForceAreaAgent, {"model": self})
    force_area_agents = factory.from_GeoDataFrame(boundaries)
    self.grid.add_agents(force_area_agents)
    for agent in force_area_agents:
      self.schedule.add(agent)

    factory = AgentCreator(ForceCentroidAgent, {"model": self})
    force_centroid_agents = factory.from_GeoDataFrame(centroids)
    self.grid.add_agents(force_centroid_agents)

    # factory = AgentCreator(ForcePSUAgent, { "model": self})
    # force_psu_agents = factory.from_GeoDataFrame(psu_data)
    # self.grid.add_agents(force_psu_agents)

    active = initialise_events(no_of_events, event_resources, event_duration, force_centroid_agents)
    self.log.append("Events started in %s" % [force_centroid_agents[a].name for a in active])

    allocate(active, force_area_agents, force_centroid_agents)

    for agent in force_centroid_agents:
      self.schedule.add(agent)

    self.running = True # doesnt work
    # self.log.append("running=%s" % self.running)

  def step(self):
    """
    Have the scheduler advance each cell by one step
    """
    # self.log.append("stepping")
    # self.log = self.log[-3:]
    self.schedule.step()
    #self.datacollector.collect(self)

    # Halt the model
    #self.running=False


# if __name__ == "__main__":
#   (b,c) = _load_data()
#   print(b.head())
#   print(c.head())