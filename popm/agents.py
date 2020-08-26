from mesa_geo.geoagent import GeoAgent

from shapely.geometry import Point
import shapely.wkt

from math import atan2, sin, cos

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

  def step(self):

    # TODO define elswhere?
    speed = 50000 # m/timestep

    # if en route, move
    if self.dispatched_to != "" and not self.deployed:
      self.shape = self.__move_towards(speed) #self.shape, self.dest, ForcePSUAgent.SPEED)

    # if event finished, move back

  def render(self):
    colour = "Blue"
    if self.dispatched_to != "":
      if self.deployed:
        colour = "Red"
      else:
        colour = "Orange"
    return { "color": colour, "radius": "1" }


  def __move_towards(self, speed):
    dest = shapely.wkt.loads(self.dest)
    dist2 = (self.shape.x - dest.x)**2 + (self.shape.y - dest.y)**2
    # >= 0.5 steps away
    if dist2 < speed*speed:
      # better displayed near rather than on?
      self.deployed = True
      # CRS problem means this is offset
      self.shape = dest
    # avoids potential div0, but is there a more efficient approach
    angle = atan2(dest.y - self.shape.y, dest.x - self.shape.x)
    x = self.shape.x + speed * cos(angle)
    y = self.shape.y + speed * sin(angle)
    return Point([x, y])


class PublicOrderEventAgent(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and track public order events within the force area """
  def __init__(self, unique_id, model, shape):
    super().__init__(unique_id, model, shape)

    self.active = True # TODO delayed start

  def step(self):
    self.duration -= 1
    if self.duration < 1:
      self.model.log.append("Event ended in %s" % self.name)

  def render(self):
    if self.duration > 0:
      return { "radius": 4, "color": "Red" if self.resources_allocated < self.resources_required else "Black"}
    return {}

