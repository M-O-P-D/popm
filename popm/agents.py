from mesa_geo.geoagent import GeoAgent

from shapely.geometry import Point

import numpy as np
#from math import atan2, sin, cos, sqrt

from .initialisation import PSU_OFFICERS
from .utils import hmm#, serialise_geometry, deserialise_geometry, hmm

class ForceAreaAgent(GeoAgent):

  """ Agent representing a police force area """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    self.available_psus = 0
    self.dispatched_psus = 0

  def step(self):
    pass

  def render(self):
    if self.dispatched_psus == 0:
      colour = "#BFBFBF"
      layer = 0
    elif self.available_psus > 0:
      colour = "#9F9F9F"
      layer = 1
    else:
      colour = "#7F7F7F"
      layer = 2
    return { "color": colour, "Layer": layer }

class ForcePSUAgent(GeoAgent):

  MOBILISATION_TIMES = {
    1: 0.1, # 10% in 1 hour
    4: 0.4, # 40% in 4 hours
    8: 0.6,  # 60% in 8 hours
    16: 1.0 # NB this figure is not part of the nationally recornised public order mobilsation timelines
  }

  # this is "extra" mobilisation time (on top of above) if needed
  MIN_MOBILISATION_TIME = 0

  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    self.assigned = False
    self.dispatched = False
    self.dispatch_time = None
    self.deployed = False
    self.dest = None
    self.dest_id = None

    # TODO Can't use a ref to agents directly as its not JSON serialisable
    # self.event_id = None
    # self.force_id = None


  def render(self):
    colour = "Blue"
    if self.reserved:
      colour = "#000080"
    if self.assigned:
      colour = "Red" if self.deployed else "Orange"
    return { "color": colour, "radius": "1", "Layer": 1 }

  # TODO implement more efficiently?
  def __get_event_agent(self):
    for a in self.model.schedule.agents:
      if isinstance(a, PublicOrderEventAgent) and a.name == self.assigned_to:
        return a
    #return None # when returning from an event not assigned to anything
    raise ValueError("no event associated with PSU agent from %s assigned to %s" % (self.name, self.assigned_to))

  def __get_force_agent(self):
    for a in self.model.schedule.agents:
      if isinstance(a, ForceAreaAgent) and a.name == self.name:
        return a
    raise ValueError("no force associated with PSU agent from %s" % self.name)

  def step(self):

    # case 0: not assigned and at base
    if (not self.assigned and not self.dispatched) or self.dest is None:
      return

    # case 0.5: not yet dispatched
    if self.model.time() < self.dispatch_time:
      return

    dest = self.model.centroids.loc[self.dest, "geometry"]

    # TODO performance is awful, cache interpolations
    #r = self.model.active_routes[(self.__get_force_agent().unique_id, self.dest_id)]
    # if r is None:
    #   print(self.__get_force_agent().unique_id, self.dest_id)

    # case 1: assigned but not yet dispatched...potentially falls though to case 2
    if self.assigned and not self.dispatched:
      # we no longer require PSUs to *arrive* at the event by the dispatch time
      # e = self.__get_event_agent()
      # if self.name == self.dest:
      #   travel_time = 0
      # else:
      #   travel_time = self.model.routes.loc[self.name, self.assigned_to]["time"]
      # if travel_time > e.time_to_start - self.model.timestep:
      #   self.dispatched = True
      #   print(self.dispatch_time, self.model.time())
      # must be time to leave
      self.dispatched = True
      #print("t=%f dispatching PSU from %s to %s" % (self.model.time(), self.name, self.dest))

    # case 2: assigned and dispatched, i.e. en route to event
    if self.assigned and self.dispatched and not self.deployed:

      if self.name == self.assigned_to:
        time = 0.0
      else:
        time = self.model.routes.loc[self.name, self.assigned_to]["time"]

      # if we arrive at event, update agents
      if self.model.time() >= self.dispatch_time + time: # TODO offset w.r.t event start
        e = self.__get_event_agent()
        # if arriving at event, find the associated event and update it
        self.deployed = True
        self.dest = None
        e.resources_present += PSU_OFFICERS
        if e.resources_required <= e.resources_present:
          self.model.log.append("%s event is 100%% resourced at t=%s" % (e.name, hmm(self.model.time())))
          e.hit100pct = self.model.time()
        elif e.resources_present - PSU_OFFICERS < e.resources_required * 0.6 and e.resources_required * 0.6 <= e.resources_present:
          self.model.log.append("%s event is 60%% resourced at t=%s" % (e.name, hmm(self.model.time())))
          e.hit60pct = self.model.time()
        elif e.resources_present - PSU_OFFICERS < e.resources_required * 0.4 and e.resources_required * 0.4 <= e.resources_present:
          self.model.log.append("%s event is 40%% resourced at t=%s" % (e.name, hmm(self.model.time())))
          e.hit40pct = self.model.time()
        elif e.resources_present - PSU_OFFICERS < e.resources_required * 0.1 and e.resources_required * 0.1 <= e.resources_present:
          self.model.log.append("%s event is 10%% resourced at t=%s" % (e.name, hmm(self.model.time())))
          e.hit10pct = self.model.time()
        self.shape = dest
      else:
        route = self.model.routes.loc[self.name, self.assigned_to]["geometry"]
        # move if event is not in home force area
        if time > 0.0:
          xy = route.xy
          timeline = np.linspace(self.dispatch_time, self.dispatch_time + time, len(xy[0])) # TODO offset w.r.t event start
          t = self.model.time()
          self.shape = Point(np.interp(t, timeline, xy[0]), np.interp(t, timeline, xy[1]))


    # case 3: assigned, dispatched and deployed at event...potentially falls though to case 4
    # handled by PublicOrderEventAgent.step()
    # if self.deployed:
    #   if e.time_to_end <= 0.0:
    #     self.assigned = False
    #     self.deployed = False
    #     self.dest = self.home

    # case 4: returning to base after event
    # otherwise, arriving home, find the associated force and make available again
    if not self.assigned and self.dispatched:

      if self.assigned_to == self.name:
        time = 0.0
        route = None
      else:
        time = self.model.routes.loc[self.assigned_to, self.name]["time"]
        route = self.model.routes.loc[self.assigned_to, self.name]["geometry"]
      e = self.__get_event_agent()

      if self.dispatched and time + e.time_to_end < 0:
        f = self.__get_force_agent()
        f.dispatched_psus -= 1
        f.available_psus += 1
        self.dispatched = False
        self.shape = dest
      else:
        if time > 0.0:
          xy = route.xy
          timeline = np.linspace(e.time_to_end, e.time_to_end + time, len(xy[0])) # TODO offset w.r.t event start
          t = 0 # relative to time_to_end
          self.shape = Point(np.interp(t, timeline, xy[0]), np.interp(t, timeline, xy[1]))


class PublicOrderEventAgent(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and track public order events within the force area """
  def __init__(self, unique_id, model, shape):
    super().__init__(unique_id, model, shape)

    self.active = True # TODO delayed start

    self.hit10pct = None
    self.hit40pct = None
    self.hit60pct = None
    self.hit100pct = None

  def step(self):
    # TODO remove event once ended
    self.time_to_start -= self.model.timestep
    self.time_to_end -= self.model.timestep

    if self.time_to_start <= 0 and self.time_to_start > -self.model.timestep:
      self.model.log.append("Event started in %s at t=%s" % (self.name, hmm(self.model.time())))

    if self.time_to_end <= 0 and self.time_to_end > -self.model.timestep:
      self.model.log.append("Event ended in %s at t=%s" % (self.name, hmm(self.model.time())))
      self.resources_required = 0
      self.resources_allocated = 0
      # deallocate agents
      psus = self.__get_psu_agents()
      for a in psus:
        self.resources_present -= PSU_OFFICERS
        a.assigned = False
        a.dest = a.name
        #a.assigned_to = None
        a.deployed = False

  def render(self):
    if self.time_to_end > 0:
      return { "radius": 8, "color": "Red" if self.resources_allocated < self.resources_required else "Black"}
    return { "radius": 8, "color": "Gray", "Layer": 0 }

  def __get_psu_agents(self):
    return [a for a in self.model.schedule.agents if isinstance(a, ForcePSUAgent) and a.assigned_to == self.name]

