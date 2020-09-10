from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import AgentCreator # GeoAgent
from mesa_geo import GeoSpace

from .agents import ForceAreaAgent, ForcePSUAgent, PublicOrderEventAgent
from .initialisation import load_data, create_psu_data, initialise_event_data
from .negotiation import allocate
from .data_collection import get_num_assigned, get_num_deployed, get_num_shortfall, get_num_deficit

class PublicOrderPolicing(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """
  def __init__(self, no_of_events, event_resources, event_start, event_duration, staff_absence, timestep, event_locations): #params...

    self.log = ["Initialising model"]

    # hourly (input is minutes)
    self.timestep = timestep / 60

    self.datacollector = DataCollector(model_reporters={
          "Assigned": get_num_assigned,
          "Deployed": get_num_deployed,
          "Shortfall": get_num_shortfall,
          "Deficit": get_num_deficit
      })

    if event_locations == "Fixed":
      self.reset_randomizer(19937)

    # Set up the grid and schedule.

    # Use SimultaneousActivation which simulates all the cells
    # computing their next state simultaneously.  This needs to
    # be done because each cell's next state depends on the current
    # state of all its neighbors -- before they've changed.
    self.schedule = SimultaneousActivation(self)

    # Use a multi grid so that >1 agent can occupy the same location
    self.grid = GeoSpace()

    # Ultra Generalised Clipped otherwise too much rendering
    force_data, self.distances = load_data()
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
    # for fixed events
    if event_locations == "Breaking Point":
      self.event_locations = [0, 4, 13]
    # otherwise random (with or without fixed seed, see above)
    else:
      self.event_locations = self.random.sample(list(force_data.index.values), min(no_of_events, len(force_data)))
    event_data = initialise_event_data(self, event_resources, event_start, event_duration, force_data)
    self.log.append("Events started in %s" % event_data["name"].values)
    factory = AgentCreator(PublicOrderEventAgent, { "model": self})
    event_agents = factory.from_GeoDataFrame(event_data)
    self.grid.add_agents(event_agents)
    for agent in event_agents:
      self.schedule.add(agent)

    self.running = True # doesnt work?

    # now assign PSUs to events
    allocate(event_agents, force_agents, psu_agents, self.distances, self.log)

  def time(self):
    return self.schedule.steps * self.timestep

  def step(self):
    """
    Have the scheduler advance each cell by one step
    """
    # ForceAreaAgent, ForcePSUAgent, PublicOrderEventAgent
    #event_agents = [a for a in self.shedule.agents if isinstance(a, PublicOrderEventAgent)]

    self.datacollector.collect(self)
    self.schedule.step()
    #print("total force agents = %d" % len([a for a in self.schedule.agents if isinstance(a, ForceAreaAgent)]))


# if __name__ == "__main__":
#   (b,c) = _load_data()
#   print(b.head())
#   print(c.head())