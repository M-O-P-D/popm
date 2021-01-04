import numpy as np
from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import AgentCreator # GeoAgent
from mesa_geo import GeoSpace

from .agents import ForceAreaAgent, ForcePSUAgent, PublicOrderEventAgent
from .initialisation import load_force_data, create_psu_data, initialise_event_data
from .utils import adjust_staffing, hmm
from .negotiation import allocate
from .data_collection import get_num_assigned, get_num_deployed, get_num_shortfall, get_num_deficit

class PublicOrderPolicing(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """
  def __init__(self, no_of_events, event_resources, event_start, event_duration, staff_absence, duty_ratio, timestep, event_locations, routes, unadjusted_force_data, centroids): #params...

    self.log = ["Initialising model"]

    self.force_data = adjust_staffing(unadjusted_force_data, staff_absence/100, duty_ratio/100)

    # CustomChartVisualisation needs this to scaled deployed as a % of required (the member var is not used anywhere else)
    # TODO this is bad and is it even correct?
    self.event_resources = event_resources / 100

    # hourly (input is minutes)
    self.timestep = timestep / 60

    if isinstance(event_locations, str) and event_locations == "Fixed":
      self.reset_randomizer(19937)

    self.routes = routes
    # cache centroids to avoid (de)serialisation inefficiencies
    self.centroids = centroids

    # create PSU dataset (which appends to force data too, so must do this *before* creating the force agents)
    psu_data = create_psu_data(self.force_data, centroids)

    # for fixed events
    if isinstance(event_locations, str) and event_locations == "Breaking Point":
      self.event_locations = ["Metropolitan Police", "Greater Manchester", "West Midlands"]
    # otherwise random (with or without fixed seed, see above)
    elif isinstance(event_locations, (tuple, list, np.ndarray)):
      if len(event_locations) != no_of_events:
        raise ValueError("event number (%d) and locations (%s) mismatch" % (no_of_events, event_locations))
      self.event_locations = [self.force_data.index[i] for i in event_locations]
    else:
      self.event_locations = self.random.sample(list(self.force_data.index.values), min(no_of_events, len(self.force_data)))

    event_data = initialise_event_data(self, event_resources, event_start, event_duration, self.force_data, centroids)

    # do negotiation/allocation on the dataframe representation, faster and more portable
    psu_data = allocate(event_data, self.force_data, psu_data, self.routes, self.logger)

    # Mesa-specific initialisation

    # Set up the grid and schedule.
    self.schedule = SimultaneousActivation(self)
    self.grid = GeoSpace(crs="epsg:27700")

    # Set up the force agents - unique index offset 0
    factory = AgentCreator(ForceAreaAgent, {"model": self}, crs="epsg:27700")
    self.force_data["id"] = range(len(self.force_data))
    force_agents = factory.from_GeoDataFrame(self.force_data.reset_index(), unique_id="id")
    self.grid.add_agents(force_agents)
    for agent in force_agents:
      self.schedule.add(agent)

    # Set up the PSU agents - unique index offset 1000
    factory = AgentCreator(ForcePSUAgent, {"model": self}, crs="epsg:27700")
    psu_data["id"] = range(1000, 1000 + len(psu_data))
    psu_agents = factory.from_GeoDataFrame(psu_data.reset_index(), unique_id="id")
    self.grid.add_agents(psu_agents)
    for agent in psu_agents:
      self.schedule.add(agent)

    # then the public order event data and agents - unique index offset 100
    self.logger("Events started in %s" % event_data.index.values)
    factory = AgentCreator(PublicOrderEventAgent, { "model": self}, crs="epsg:27700")
    event_data["id"] = range(100, 100 + len(event_data))
    event_agents = factory.from_GeoDataFrame(event_data.reset_index(), unique_id="id")
    self.grid.add_agents(event_agents)
    for agent in event_agents:
      self.schedule.add(agent)

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

    self.running = True # doesnt work?
    # now assign PSUs to events

  def logger(self, msg):
    self.log.append(msg)

  def time(self):
    return (self.schedule.steps) * self.timestep

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
        print("All PSUs inactive at time %s, halting model" % hmm(self.time()))
        self.running = False

