
from .initialisation import PSU_OFFICERS

def find_force(forces, name):
  for force in forces:
    if force.name == name: return force
  raise ValueError("Force %s not found" % name)

def find_other_forces(forces, name, alliance, in_alliance=True):
  # TODO need to ignore forces that have ongoing public order events?
  other = []
  for f in forces:
    if f.name != name and (f.Alliance == alliance) == in_alliance:
      other.append(f)
  return other

def rank(forces, name, distances, event_duration):
  """
  Ranks according to distance/cost and supply
  """
  # TODO make a property of the force
  mobilisation_time = 1
  # assuming duration in hours, this corresponds to 50km/h
  mobilisation_speed = 50

  ranks = []
  for f in forces:
    despatch_time = mobilisation_time + distances.at[f.name, name] / mobilisation_speed
    if despatch_time < event_duration:
      ranks.append((f.name, f.available_psus / despatch_time))
  return sorted(ranks, key=lambda t: -t[1])

# TODO deploy_immediately no longer required
def mark_psu_assigned(force_name, event_agent, psu_agents, include_reserved=False):
  avail = [a for a in psu_agents if a.name == force_name and not a.assigned and (include_reserved or not a.reserved)]
  if len(avail) == 0:
    return #raise ValueError("no psu available for dispatch from %s to %s" % (force_name, event_location))
  avail[0].assigned = True
  avail[0].dispatched = False
  avail[0].deployed = False
  avail[0].assigned_to = event_agent.name #event_location
  # use wkt string to avoid TypeError: Object of type Point is not JSON serializable
  avail[0].dest = event_agent.shape.wkt
  #avail[0].event = event_agent

def allocate(event_agents, force_agents, psu_agents, distances, log):
  # ensure we allocate in-location first (to stop resources being taken by other areas)
  for a in event_agents:
    # allocate self resources
    f = find_force(force_agents, a.name)
    req = a.resources_required

    allocated = 0
    while req > 0 and f.available_psus > 0:
      #print(a.shape)
      mark_psu_assigned(f.name, a, psu_agents, include_reserved=True)
      req -= PSU_OFFICERS
      a.resources_allocated += PSU_OFFICERS
      # in-force are automatically present
      #a.resources_present += PSU_OFFICERS
      f.available_psus -= 1
      f.dispatched_psus += 1
      allocated += 1
    log.append("%d PSUs allocated from %s" % (allocated, f.name))

  for a in event_agents:
    # allocate self resources
    f = find_force(force_agents, a.name)
    req = a.resources_required - a.resources_allocated

    # if not fully resourced, request from alliance member
    if req > 0:
      forces = find_other_forces(force_agents, a.name, a.Alliance)
      ranks = rank(forces, a.name, distances, a.time_to_start) # TODO confirm if should be start, end or both
      for r in ranks:
        f = find_force(force_agents, r[0])
        allocated = 0
        while req > 0 and f.available_psus > 0:
          mark_psu_assigned(f.name, a, psu_agents)
          req -= PSU_OFFICERS
          a.resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0: log.append("%d PSUs allocated from alliance %s to %s (rank=%f)" % (allocated, f.name, a.name, r[1]))

    # if still not fully resourced, request other forces
    if req > 0:
      # allocations from further afield
      forces = find_other_forces(force_agents, a.name, a.Alliance, in_alliance=False)
      ranks = rank(forces, a.name, distances, a.time_to_start) # TODO confirm if should be start, end or both
      for r in ranks:
        f = find_force(force_agents, r[0])
        allocated = 0
        while req > 0 and f.available_psus > 0:
          mark_psu_assigned(f.name, a, psu_agents)
          req -= PSU_OFFICERS
          a.resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0: log.append("%d PSUs allocated from %s to %s (rank=%f)" % (allocated, f.name, a.name, r[1]))

    # if still not fully resourced, print a message
    if req > 0:
      log.append("** %s event cannot be fully resource allocated **" % a.name)