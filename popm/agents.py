from mesa_geo.geoagent import GeoAgent

from shapely.geometry import Point

from math import atan2, sin, cos, sqrt

from .initialisation import PSU_OFFICERS
from .utils import serialise_geometry, deserialise_geometry

class ForceAreaAgent(GeoAgent):

  """ Agent representing a police force area """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    #self.available_psus = 0

  def step(self):
    pass

  def render(self):
    if self.dispatched_psus == 0:
      colour = "#BFBFBF"
    elif self.available_psus > 0:
      colour = "#9F9F9F"
    else:
      colour = "#7F7F7F"
    return { "color": colour, "Layer": 0 }

class ForcePSUAgent(GeoAgent):

  MOBILISATION_TIME = 1.0 # hours

  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    self.assigned = False
    self.dispatched = False
    self.deployed = False
    self.dest = None
    self.home = serialise_geometry(self.shape)
    self.speed = 0.0

    # TODO Can't use a ref to agents directly as its not JSON serialisable
    # self.event_id = None
    # self.force_id = None

  def step(self):

    self.__move() #self.shape, self.dest, ForcePSUAgent.SPEED)

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

  def __move(self):

    if self.model.time() < ForcePSUAgent.MOBILISATION_TIME:
      return

    # max distance in a single timestep (in metres)
    delta = self.speed * 1000 * self.model.timestep

    # case 0: not assigned and at base
    if (not self.assigned and not self.dispatched) or self.dest is None:
      return

    dest = deserialise_geometry(self.dest)
    euclidean_dist = sqrt((self.shape.x - dest.x)**2 + (self.shape.y - dest.y)**2)

    # case 1: assigned but not yet dispatched...potentially falls though to case 2
    if self.assigned and not self.dispatched:
      e = self.__get_event_agent()
      travel_time = euclidean_dist / self.speed / 1000.0
      if travel_time > e.time_to_start - self.model.timestep:
        self.dispatched = True

    # case 2: assigned and dispatched, i.e. en route to event
    if self.assigned and self.dispatched and not self.deployed:
      # if we arrive at event, update agents
      if euclidean_dist < delta:
        e = self.__get_event_agent()
        # if arriving at event, find the associated event and update it
        self.deployed = True
        self.dest = None
        e.resources_present += PSU_OFFICERS
        if e.resources_required <= e.resources_present:
          self.model.log.append("%s event is fully resourced at t=%f" % (e.name, self.model.time()))
        self.shape = dest
      else:
        # avoids potential div0, but is there a more efficient approach
        angle = atan2(dest.y - self.shape.y, dest.x - self.shape.x)
        x = self.shape.x + delta * cos(angle)
        y = self.shape.y + delta * sin(angle)
        self.shape = Point([x, y])

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
      if euclidean_dist < delta:
        f = self.__get_force_agent()
        f.dispatched_psus -= 1
        f.available_psus += 1
        self.dispatched = False
        self.shape = dest
      else:
        angle = atan2(dest.y - self.shape.y, dest.x - self.shape.x)
        x = self.shape.x + delta * cos(angle)
        y = self.shape.y + delta * sin(angle)
        self.shape = Point([x, y])


class PublicOrderEventAgent(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and track public order events within the force area """
  def __init__(self, unique_id, model, shape):
    super().__init__(unique_id, model, shape)

    self.active = True # TODO delayed start

  def step(self):
    # TODO remove event once ended
    self.time_to_start -= self.model.timestep
    self.time_to_end -= self.model.timestep

    if self.time_to_start <= 0 and self.time_to_start > -self.model.timestep:
      self.model.log.append("Event started in %s" % self.name)

    if self.time_to_end <= 0 and self.time_to_end > -self.model.timestep:
      self.model.log.append("Event ended in %s" % self.name)
      self.resources_required = 0
      self.resources_allocated = 0
      # deallocate agents
      psus = self.__get_psu_agents()
      for a in psus:
        self.resources_present -= PSU_OFFICERS
        a.assigned = False
        a.dest = a.home
        a.assigned_to = None
        a.deployed = False

  def render(self):
    if self.time_to_end > 0:
      return { "radius": 4, "color": "Red" if self.resources_allocated < self.resources_required else "Black"}
    return { "radius": 4, "color": "Gray", "Layer": 0 }

  def __get_psu_agents(self):
    return [a for a in self.model.schedule.agents if isinstance(a, ForcePSUAgent) and a.assigned_to == self.name]

