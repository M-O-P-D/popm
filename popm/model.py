from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import GeoAgent, AgentCreator
from mesa_geo import GeoSpace

import geopandas as gpd

class ForceAgent(GeoAgent):
  """ 
  Agent representing a police force
  """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

  def step(self):
    pass

class PublicOrderPolicing(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """

  def __init__(self): #params...

    self.log = []
    self.datacollector = DataCollector(
        model_reporters={
        }
    )

    # Set up the grid and schedule.

    # Use SimultaneousActivation which simulates all the cells
    # computing their next state simultaneously.  This needs to
    # be done because each cell's next state depends on the current
    # state of all its neighbors -- before they've changed.
    self.schedule = RandomActivation(self)

    # Use a multi grid so that >1 agent can occupy the same location
    self.grid = GeoSpace()

    # Set up the force agents 
    boundaries = gpd.read_file("../../protocop/cache/data/boundaries/forces.shp")
    # coordinates are east/northings 
    #boundaries = gpd.read_file("../model-data-for-andrew/Police_Force_Areas_December_2016_Full_Clipped_Boundaries_in_England_and_Wales.shp")
    #boundaries.crs = { "init": "epsg:3857" } 
    boundaries.crs = { "init": "epsg:4326" } 
    #print(boundaries.head())
    factory = AgentCreator(ForceAgent, {"model": self})
    force_agents = factory.from_GeoDataFrame(boundaries)
    self.grid.add_agents(force_agents) 

    for agent in force_agents:
      self.schedule.add(agent)     

    self.log.append("Initialised model")
    self.running = True
    self.log.append("running=%s" % self.running)

  def step(self):
    """
    Have the scheduler advance each cell by one step
    """
    # self.log.append("stepping")
    # self.log = self.log[-3:]
    self.schedule.step()
    #self.datacollector.collect(self)

    # Halt the model
    running=False

