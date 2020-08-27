from mesa_geo.geoagent import GeoAgent

from shapely.geometry import Point
import shapely.wkt

from math import atan2, sin, cos

from .initialisation import PSU_OFFICERS

class ForceAreaAgent(GeoAgent):

  """ Agent representing a police force area """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    #self.available_psus = 0

  def step(self):
    pass

  def render(self):
    if self.dispatched_psus == 0:
      return { "color": "#BFBFBF" }
    elif self.available_psus > 0:
      return { "color": "#9F9F9F" }
    else:
      return { "color": "#7F7F7F" }

class ForcePSUAgent(GeoAgent):

  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    # TODO use this not the string dispatched_to
    self.dest = None
    self.home = shape.wkt
    # TODO Can't use a ref to agents directly as its not JSON serialisable
    # self.event_id = None
    # self.force_id = None

  def step(self):

    # TODO define elswhere?
    # 50 km/h * delta_t
    delta = 50000 * self.model.timestep

    # if en route, move
    if self.dest is not None:
      self.shape = self.__move(delta) #self.shape, self.dest, ForcePSUAgent.SPEED)

    # TODO if event finished, start moving back

  def render(self):
    colour = "Blue"
    if self.assigned:
      colour = "Red" if self.dispatched_to is not None else "Orange"
    return { "color": colour, "radius": "1" }

  # TODO implement more efficiently?
  def __get_event_agent(self):
    for a in self.model.schedule.agents:
      if isinstance(a, PublicOrderEventAgent) and a.name == self.dispatched_to:
        return a
    raise ValueError("no event associated with PSU agent from %s assigned to %s" % (self.name, self.dispatched_to))

  def __get_force_agent(self):
    for a in self.model.schedule.agents:
      if isinstance(a, ForceAreaAgent) and a.name == self.name:
        return a
    raise ValueError("no force associated with PSU agent from %s" % self.name)

  def __move(self, delta):
    dest = shapely.wkt.loads(self.dest)
    dist2 = (self.shape.x - dest.x)**2 + (self.shape.y - dest.y)**2
    # >= 0.5 steps away
    if dist2 < delta*delta:
      # better displayed near rather than on?
      self.dest = None
      # if arriving at event, find the associated event and update it
      if self.dispatched_to is not None:
        self.deployed = True
        e = self.__get_event_agent()
        e.resources_present += PSU_OFFICERS
        if e.resources_required <= e.resources_present:
          self.model.log.append("%s event is fully resourced at t=%f" % (e.name, self.model.time()))
      # otherwise, arriving home, find the associated force and make available again
      else:
        f = self.__get_force_agent()
        f.dispatched_psus -= 1
        f.available_psus += 1
        self.deployed = False
        self.assigned = False
      return dest
    # avoids potential div0, but is there a more efficient approach
    angle = atan2(dest.y - self.shape.y, dest.x - self.shape.x)
    x = self.shape.x + delta * cos(angle)
    y = self.shape.y + delta * sin(angle)
    return Point([x, y])


class PublicOrderEventAgent(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and track public order events within the force area """
  def __init__(self, unique_id, model, shape):
    super().__init__(unique_id, model, shape)

    self.active = True # TODO delayed start

  def step(self):
    # TODO remove event once ended
    if self.duration > 0:
      self.duration -= self.model.timestep
      if self.duration <= 0:
        self.model.log.append("Event ended in %s" % self.name)
        self.resources_required = 0
        self.resources_allocated = 0
        # deallocate agents
        psus = self.__get_psu_agents()
        for a in psus:
          self.resources_present -= PSU_OFFICERS
          a.dest = a.home
          a.dispatched_to = None
          a.deployed = False

  def render(self):
    if self.duration > 0:
      return { "radius": 4, "color": "Red" if self.resources_allocated < self.resources_required else "Black"}
    return { "radius": 4, "color": "Gray" }

  def __get_psu_agents(self):
    return [a for a in self.model.schedule.agents if isinstance(a, ForcePSUAgent) and a.dispatched_to == self.name]

