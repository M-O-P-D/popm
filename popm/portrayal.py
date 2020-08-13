from .agents import *

# Currently only color and radius properties are supported, see
# mesa-geo/mesa_geo/visualization/templates/js/LeafletMap.js 

def portray_map(agent):
  if isinstance(agent, ForceAreaAgent):
    return { "color": "Blue" }
  elif isinstance(agent, ForceCentroidAgent):
    return { "radius": "2", "color": "Red" }
  else:
    raise TypeError("don't know how to portray object of type %s" % type(agent))