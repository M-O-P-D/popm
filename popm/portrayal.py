from .agents import ForceAreaAgent, ForceCentroidAgent

# Currently only color and radius properties are supported, see
# mesa-geo/mesa_geo/visualization/templates/js/LeafletMap.js

def portray_map(agent):
  if isinstance(agent, ForceAreaAgent):
    return { "color": "Blue" }
  elif isinstance(agent, ForceCentroidAgent):
    return { "radius": agent.size(), "color": agent.colour() }
  else:
    raise TypeError("don't know how to portray object of type %s" % type(agent))