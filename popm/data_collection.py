""" data collection module """

from .agents import PublicOrderEventAgent

def get_num_assigned(model):
  assigned = 0
  for a in model.schedule.agents:
    if isinstance(a, PublicOrderEventAgent):
      assigned += a.resources_allocated
  return assigned

def get_deployed_per_agent(model):
  deployed = {}
  for a in model.schedule.agents:
    if isinstance(a, PublicOrderEventAgent):
      deployed[a.name] = a.resources_present
  return deployed

def get_num_deployed(model):
  deployed = 0
  for a in model.schedule.agents:
    if isinstance(a, PublicOrderEventAgent):
      deployed += a.resources_present
  return deployed

# NB this is required less *assigned* (not deployed)
def get_num_deficit(model):
  deficit = 0
  for a in model.schedule.agents:
    if isinstance(a, PublicOrderEventAgent):
      deficit += a.resources_required - a.resources_allocated
  return max(deficit, 0)

# NB this is required less *deployed* (not assigned)
def get_num_shortfall(model):
  shortfall = 0
  for a in model.schedule.agents:
    if isinstance(a, PublicOrderEventAgent):
      shortfall += a.resources_required - a.resources_present
  return max(shortfall, 0)


