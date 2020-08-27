from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import AgentCreator # GeoAgent
from mesa_geo import GeoSpace

from .agents import ForceAreaAgent, ForcePSUAgent, PublicOrderEventAgent
from .initialisation import load_data, create_psu_data, initialise_event_data
from .negotiation import allocate

class PublicOrderPolicing(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """
  def __init__(self, no_of_events, event_resources, event_duration, staff_absence, timestep, seed=None): #params...

    self.log = ["Initialising model"]

    self.timestep = timestep

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
    force_data, distances = load_data()
    # create PSU dataset (which appends to force data too, so must do this *before* creating the force agents)
    psu_data = create_psu_data(force_data, staff_absence)

    # Set up the force agents
    factory = AgentCreator(ForceAreaAgent, {"model": self})
    force_agents = factory.from_GeoDataFrame(force_data)
    self.grid.add_agents(force_agents)
    for agent in force_agents:
      self.schedule.add(agent)

    # Set up the PSU agents
    factory = AgentCreator(ForcePSUAgent, {"model": self})
    psu_agents = factory.from_GeoDataFrame(psu_data)
    self.grid.add_agents(psu_agents)
    for agent in psu_agents:
      self.schedule.add(agent)

    # then the public order event data and agents
    event_data = initialise_event_data(no_of_events, event_resources, event_duration, force_data)
    self.log.append("Events started in %s" % event_data["name"].values)
    factory = AgentCreator(PublicOrderEventAgent, { "model": self})
    event_agents = factory.from_GeoDataFrame(event_data)
    self.grid.add_agents(event_agents)
    for agent in event_agents:
      self.schedule.add(agent)

    # now assign PSUs to events
    allocate(event_agents, force_agents, psu_agents, distances, self.log)

    self.running = True # doesnt work
    # self.log.append("running=%s" % self.running)

  def step(self):
    """
    Have the scheduler advance each cell by one step
    """
    self.schedule.step()


# if __name__ == "__main__":
#   (b,c) = _load_data()
#   print(b.head())
#   print(c.head())