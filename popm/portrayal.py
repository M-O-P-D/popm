#from .agents import ForceAreaAgent, ForceCentroidAgent, ForcePSUAgent

# Currently only color and radius properties are supported, see
# mesa-geo/mesa_geo/visualization/templates/js/LeafletMap.js

def portray_map(agent):
  # defer to agents
  return agent.render()
