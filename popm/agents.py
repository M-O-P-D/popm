from mesa_geo.geoagent import GeoAgent

import random

class ForceAreaAgent(GeoAgent):

  """ Agent representing a police force area """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

  def step(self):
    pass

class ForceCentroidAgent(GeoAgent):

  """ Agent representing a reference point in the force area to compute costs (distances) and count public order events within the force area """
  def __init__(self, unique_id, model, shape, staff_attrition):
    # staff_attrition is a global setting really, but I've inserted it here more as a how-to than a necessity

    super().__init__(unique_id, model, shape)
    self.staff_attrition = staff_attrition

    self.public_order_events = 0

  def step(self):
    # riot start probability inversely proportional to cop density
    p_activation = 0.00001 / self.cops_per_pop 
    # riot end probability proportional to cop density
    p_deactivation = 1.3 * self.cops_per_pop
    # note start and end events are independent
    if random.random() < p_activation:
      self.public_order_events = self.public_order_events + 1
      self.model.log.append("Riot started in %s" % self.name)
    if random.random() < p_deactivation and self.public_order_events > 0:
      self.public_order_events = self.public_order_events - 1
      self.model.log.append("Riot ended in %s" % self.name)

  def colour(self):
    if self.public_order_events == 0:
      return "Green"
    return "Red"    
    

# class PublicOrderEvent(GeoAgent):

#   """ Agent representing a public order event """
#   def __init__(self, unique_id, model):

#     super().__init__(unique_id, model)

#   def step(self):
#     pass
