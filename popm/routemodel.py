from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import AgentCreator # GeoAgent
from mesa_geo import GeoSpace

from shapely.geometry import Point
from .utils import *

from .agents import ForceAreaAgent
from .ford_granada import FordGranada
from .initialisation import load_data
from .data_collection import * #get_num_assigned, get_num_deployed, get_num_shortfall, get_num_deficit

def initialise_car_data(model, force_data):
  # activate events as per parameters
  event_data = force_data.loc[model.event_locations, ["name", "Alliance", "geometry"]].copy().reset_index(drop=True)

  for i, r in event_data.iterrows():
    min_x, min_y, max_x, max_y = r.geometry.bounds
    while True:
      p = Point([model.random.uniform(min_x, max_x), model.random.uniform(min_y, max_y)])
      if p.within(r.geometry):
        event_data.at[i, "geometry"] = p
        event_data.at[(i+1)%len(event_data), "destination"] = serialise_geometry(p)
        break

  event_data.index += 100 # ensure unique
  print(event_data)

  return event_data

class RouteModel(Model):
  # below ends up in the "About" menu
  """
  An agent-based model of resource allocation in response to public order events.
  Source code at https://github.com/M-O-P-D/popm
  """
  def __init__(self, no_of_events, event_resources, event_start, event_duration, staff_absence, timestep, event_locations): #params...

    self.log = ["Initialising model"]

    # hourly (input is minutes)
    self.timestep = timestep / 60

    if event_locations == "Fixed":
      self.reset_randomizer(19937)

    # Set up the grid and schedule.
    self.schedule = SimultaneousActivation(self)
    self.grid = GeoSpace(crs="epsg:27700")

    force_data, self.distances, self.travel_times = load_data()
    # create PSU dataset (which appends to force data too, so must do this *before* creating the force agents)

    # Set up the force agents
    factory = AgentCreator(ForceAreaAgent, {"model": self}, crs="epsg:27700")
    force_agents = factory.from_GeoDataFrame(force_data)
    self.grid.add_agents(force_agents)
    for agent in force_agents:
      self.schedule.add(agent)

    # then the public order event data and agents
    # for fixed events
    if event_locations == "Breaking Point":
      self.event_locations = [0, 4, 13]
    # otherwise random (with or without fixed seed, see above)
    else:
      self.event_locations = self.random.sample(list(force_data.index.values), min(no_of_events, len(force_data)))
    car_data = initialise_car_data(self, force_data)
    self.log.append("Cars started in %s" % car_data["name"].values)
    factory = AgentCreator(FordGranada, { "model": self}, crs="epsg:27700")
    car_agents = factory.from_GeoDataFrame(car_data)
    self.grid.add_agents(car_agents)
    self.car_routes = {}
    for agent in car_agents:
      #self.car_routes[agent.unique_id] = agent.route()
      self.schedule.add(agent)

    import pickle
    # with open("routes.pickle", "wb") as f:
    #   pickle.dump(self.car_routes, f)
    with open("routes.pickle", "rb") as f:
      self.car_routes = pickle.load(f)


    self.running = True # doesnt work?

    # TODO assign car's endpoint to next agent's start point

  def time(self):
    return self.schedule.steps * self.timestep

  def step(self):
    """
    Have the scheduler advance each cell by one step
    """
    self.log.append("t=%f" % self.time())
    #self.datacollector.collect(self)
    self.schedule.step()

  # This override is not called running in server mode, but it is called in batch mode
  def run_model(self):
    while self.running:
      self.step()
      # flush the log
      for msg in self.log:
        print(msg)
      self.log = []

