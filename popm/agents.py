from mesa_geo.geoagent import GeoAgent

import random

class ForceAreaAgent(GeoAgent):

  """ Agent representing a police force area """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

  def step(self):
    pass

class ForceCentroidAgent(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and track public order events within the force area """
  def __init__(self, unique_id, model, shape): #, public_order_events, event_resources, event_duration):
    # staff_absence is a global setting really, but I've inserted it here more as a how-to than a necessity

    super().__init__(unique_id, model, shape)

    self.public_order_events = 0 # TODO just use duration?
    self.event_resources = 0
    self.event_duration = 0

  def step(self):
    if self.public_order_events > 0:
      self.event_duration -= 1
      if self.event_duration == 0:
        self.public_order_events -= 1
        self.model.log.append("Event ended in %s" % self.name)

  def colour(self):
    if self.public_order_events == 0:
      return "Green"
    return "Red"

  def size(self):
    return str(1+self.public_order_events)

# class PublicOrderEvent(GeoAgent):

#   """ Agent representing a public order event """
#   def __init__(self, unique_id, model):

#     super().__init__(unique_id, model)

#   def step(self):
#     pass
