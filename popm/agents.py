from mesa_geo.geoagent import GeoAgent

class ForceAreaAgent(GeoAgent):
  """
  Agent representing a police force area
  """
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

  def step(self):
    pass

class ForceCentroidAgent(GeoAgent):
  """
  Agent representing a reference point in the force area to compute costs (distances) 
  """
  # staff_attrition is a global setting really, but I've inserted it here more as a how-to than a necessity
  def __init__(self, unique_id, model, shape, staff_attrition):

    super().__init__(unique_id, model, shape)
    self.staff_attrition = staff_attrition

  def step(self):
    pass
