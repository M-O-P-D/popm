import numpy as np
from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import AgentCreator # GeoAgent
from mesa_geo import GeoSpace

from .agents import ForceAreaAgent, ForcePSUAgent, PublicOrderEventAgent
from .initialisation import load_force_data, create_psu_data, initialise_event_data
from .negotiation import allocate
from .data_collection import * #get_num_assigned, get_num_deployed, get_num_shortfall, get_num_deficit

class PublicOrderPolicing(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """
  def __init__(self, no_of_events, event_resources, event_start, event_duration, staff_absence, timestep, event_locations, routes, force_data): #params...

    self.log = ["Initialising model"]

    # CustomChartVisualisation needs this to scaled deployed as a % of required (the member var is not used anywhere else)
    # TODO this is bad and is it even correct?
    self.event_resources = event_resources / 100

    # hourly (input is minutes)
    self.timestep = timestep / 60

    self.datacollector = DataCollector(
      model_reporters={
        "Assigned": get_num_assigned,
        "Deployed": get_num_deployed,
        "Shortfall": get_num_shortfall,
        "Deficit": get_num_deficit
      },
      agent_reporters={
        # "Time": lambda _: self.time(),
        # "Active": lambda a: (a.time_to_start <= 0.0 and a.time_to_end >= 0.0) if isinstance(a, PublicOrderEventAgent) else None,
        "Required": lambda a: a.resources_required if isinstance(a, PublicOrderEventAgent) else None,
        "Allocated": lambda a: a.resources_allocated if isinstance(a, PublicOrderEventAgent) else None,
        "Deployed": lambda a: a.resources_present if isinstance(a, PublicOrderEventAgent) else None
      }
    )

    if isinstance(event_locations, str) and event_locations == "Fixed":
      self.reset_randomizer(19937)

    # Set up the grid and schedule.
    self.schedule = SimultaneousActivation(self)
    self.grid = GeoSpace(crs="epsg:27700")

    self.routes = routes

    # create PSU dataset (which appends to force data too, so must do this *before* creating the force agents)
    psu_data = create_psu_data(force_data, staff_absence)

    # Set up the force agents
    factory = AgentCreator(ForceAreaAgent, {"model": self}, crs="epsg:27700")
    force_agents = factory.from_GeoDataFrame(force_data)
    self.grid.add_agents(force_agents)
    for agent in force_agents:
      self.schedule.add(agent)

    # Set up the PSU agents
    factory = AgentCreator(ForcePSUAgent, {"model": self}, crs="epsg:27700")
    psu_agents = factory.from_GeoDataFrame(psu_data)
    self.grid.add_agents(psu_agents)
    for agent in psu_agents:
      self.schedule.add(agent)

    # then the public order event data and agents
    # for fixed events
    if isinstance(event_locations, str) and event_locations == "Breaking Point":
      self.event_locations = [0, 4, 13]
    # otherwise random (with or without fixed seed, see above)
    elif isinstance(event_locations, (list, np.ndarray)):
      if len(event_locations) != no_of_events:
        raise ValueError("event number (%d) and locations (%s) mismatch" % (no_of_events, event_locations))
      self.event_locations = event_locations
    else:
      self.event_locations = self.random.sample(list(force_data.index.values), min(no_of_events, len(force_data)))

    event_data = initialise_event_data(self, event_resources, event_start, event_duration, force_data)
    self.log.append("Events started in %s" % event_data["name"].values)
    factory = AgentCreator(PublicOrderEventAgent, { "model": self}, crs="epsg:27700")
    event_agents = factory.from_GeoDataFrame(event_data)
    self.grid.add_agents(event_agents)
    for agent in event_agents:
      self.schedule.add(agent)

    self.running = True # doesnt work?
    # now assign PSUs to events
    allocate(event_agents, force_agents, psu_agents, self.routes, self.log)

  def time(self):
    return (self.schedule.steps+1) * self.timestep

  def step(self):
    """
    Have the scheduler advance each cell by one step
    """
    self.datacollector.collect(self)
    self.schedule.step()

  # This override is not called running in server mode, but it is called in batch mode
  def run_model(self):
    while self.running:
      self.step()
      # flush the log
      for msg in self.log:
        print(msg)
      self.log = []
      # stop when all police are back home i.e. not assigned or dispatched
      active_psus = [a for a in self.schedule.agents if isinstance(a, ForcePSUAgent) and (a.assigned == True or a.dispatched == True)]
      if not any(active_psus):
        print("All PSUs inactive at time %.2f, halting model" % self.time())
        self.running = False

