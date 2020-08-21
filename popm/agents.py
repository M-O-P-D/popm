from mesa_geo.geoagent import GeoAgent

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
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

  def step(self):
    # TODO update position
    pass

  def render(self):
    return { "color": "Orange" if self.deployed else "Blue", "radius": "1" }



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
