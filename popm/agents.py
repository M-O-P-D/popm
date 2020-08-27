from mesa_geo.geoagent import GeoAgent

from shapely.geometry import Point
import shapely.wkt

from math import atan2, sin, cos, sqrt

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
    delta = 50000 * self.model.timestep / 60

    # if en route, move
    if self.dest is not None and not self.deployed:
      self.shape = self.__move_towards(delta) #self.shape, self.dest, ForcePSUAgent.SPEED)

    # TODO if event finished, start moving back

  def render(self):
    colour = "Blue"
    if self.dest is not None:
      if self.deployed:
        colour = "Red"
      else:
        colour = "Orange"
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

  def __move_towards(self, delta):
    dest = shapely.wkt.loads(self.dest)
    dist2 = (self.shape.x - dest.x)**2 + (self.shape.y - dest.y)**2
    # >= 0.5 steps away
    if dist2 < delta*delta:
      # better displayed near rather than on?
      self.deployed = True
      # find the associated event and update it
      self.__get_event_agent().resources_present += PSU_OFFICERS
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
    self.duration -= self.model.timestep / 60
    if self.duration == 0:
      self.model.log.append("Event ended in %s" % self.name)
      self.resources_required = 0

  def render(self):
    if self.duration > 0:
      return { "radius": 4, "color": "Red" if self.resources_allocated < self.resources_required else "Black"}
    return { "radius": 4, "color": "Gray" }

