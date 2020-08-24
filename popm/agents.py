from mesa_geo.geoagent import GeoAgent

from shapely.geometry import Point

from math import atan2, sin, cos

def _move_towards(pos, dest, speed):
  dist2 = (pos.x - dest[0])**2 + (pos.y - dest[1])**2
  # >= 1 steps away
  if dist2 < speed*speed:
    # better displayed near rather than on?
    #return pos
    return Point([dest[0], dest[1]])
  # avoids potential div0, but is there a more efficient approach
  angle = atan2(dest[1] - pos.y, dest[0] - pos.x)
  x = pos.x + speed * cos(angle)
  y = pos.y + speed * sin(angle)
  return Point([x, y])

class ForceAreaAgent(GeoAgent):

  """ Agent representing a police force area """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    #self.available_psus = 0

  def step(self):
    pass


  def render(self):
    if self.available_psus > 0:
      return { }
    else:
      return { "color": "Gray" }


class ForcePSUAgent(GeoAgent):

  # TODO define elswhere?
  SPEED = 50000 # m/timestep

  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

    # TODO use this not the string dispatched_to
    self.dest = None

  def step(self):
    # if en route, move
    if self.dispatched_to != "" and not self.deployed:
      self.shape = _move_towards(self.shape, self.dest, ForcePSUAgent.SPEED)

    # if event finished, move back

  def render(self):
    colour = "Blue"
    if self.dispatched_to != "":
      if self.deployed:
        colour = "Red"
      else:
        colour = "Orange"
    return { "color": colour, "radius": "1" }



class ForceCentroidAgent(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and track public order events within the force area """
  def __init__(self, unique_id, model, shape): #, public_order_events, event_resources, event_duration):
    # staff_absence is a global setting really, but I've inserted it here more as a how-to than a necessity

    super().__init__(unique_id, model, shape)

    self.public_order_events = 0 # TODO just use duration?
    self.event_resources_required = 0
    self.event_resources_allocated = 0
    self.event_resources_present = 0
    self.event_duration = 0

  def step(self):
    if self.public_order_events > 0:
      self.event_duration -= 1
      if self.event_duration == 0:
        self.public_order_events -= 1
        self.model.log.append("Event ended in %s" % self.name)

  def render(self):
    if self.public_order_events > 0:
      return { "radius": 3 + self.public_order_events, "color": "Red" if self.event_resources_allocated < self.event_resources_required else "Black"}
    return {}


# class PublicOrderEvent(GeoAgent):

#   """ Agent representing a public order event """
#   def __init__(self, unique_id, model):

#     super().__init__(unique_id, model)

#   def step(self):
#     pass
