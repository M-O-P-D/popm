from .agents import *

def portray_map(agent):
  if isinstance(agent, ForceAreaAgent):
    return { "color": "Blue" }
  elif isinstance(agent, ForceCentroidAgent):
    return { "radius": "2", "color": "Red" }
  else:
    return {}