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
  def __init__(self, unique_id, model, shape):

    super().__init__(unique_id, model, shape)

  def step(self):
    pass
