from .utils import serialise_geometry
from .initialisation import PSU_OFFICERS
from .agents import ForcePSUAgent

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

def rank(forces, name, routes, event_end_minus1):
  """
  Ranks according to distance/cost and supply
  """
  # TODO should we increase ranking for PSUs that can get there by *start* of event?
  ranks = []
  for f in forces:
    despatch_time = ForcePSUAgent.MOBILISATION_TIME
    if f.name != name:
      despatch_time += routes.loc[f.name, name]["time"]
    if despatch_time < event_end_minus1:
      ranks.append((f.name, f.available_psus / despatch_time))
  return sorted(ranks, key=lambda t: -t[1])

def mark_psu_assigned(force_area, event_agent, psu_agents, include_reserved=False):
  avail = [a for a in psu_agents if a.name == force_area.name and not a.assigned and (include_reserved or not a.reserved)]
  if len(avail) == 0:
    return #raise ValueError("no psu available for dispatch from %s to %s" % (force_name, event_location))
  avail[0].assigned = True
  avail[0].dispatched = False
  avail[0].deployed = False
  avail[0].assigned_to = event_agent.name #event_location
  # text serialise to avoid TypeError: Object of type Point is not JSON serializable
  avail[0].dest = serialise_geometry(event_agent.shape)
  avail[0].dest_id = event_agent.unique_id

  # agents move as-the-crow-flies on the map, but use road travel times to determine when to move
  # thus we need to compute an equivalent straight-line speed that results in arrival at destination at same time as if on the road network
  # unless in same force area in which case we get a div by zero so default to 50km/h
  # t = travel_times.at[avail[0].name, event_agent.name]
  # euclidean_dist = sqrt((avail[0].shape.x - event_agent.shape.x)**2 + (avail[0].shape.y - event_agent.shape.y)**2) / 1000.0
  # avail[0].speed = euclidean_dist / t if t != 0.0 else 50.0

def allocate(event_agents, force_agents, psu_agents, routes, log):

  # set up interpolatable routes for active PSUs
  #active_routes = {}

  # ensure we allocate in-location first (to stop resources being taken by other areas)
  for a in event_agents:
    # allocate self resources
    f = find_force(force_agents, a.name)
    req = a.resources_required

    allocated = 0
    while req > 0 and f.available_psus > 0:
      #print(a.shape)
      mark_psu_assigned(f, a, psu_agents, include_reserved=True)
      req -= PSU_OFFICERS
      a.resources_allocated += PSU_OFFICERS
      # in-force are automatically present
      #a.resources_present += PSU_OFFICERS
      f.available_psus -= 1
      f.dispatched_psus += 1
      allocated += 1
    log.append("%d PSUs allocated from %s" % (allocated, f.name))

    #active_routes[(f.unique_id, a.unique_id)] = None # TODO do we need empty arrays?

  for a in event_agents:
    # allocate self resources
    f = find_force(force_agents, a.name)
    req = a.resources_required - a.resources_allocated

    # if not fully resourced, request from alliance member
    if req > 0:
      forces = find_other_forces(force_agents, a.name, a.Alliance)
      ranks = rank(forces, a.name, routes, a.time_to_end)

      for r in ranks:
        f = find_force(force_agents, r[0])
        allocated = 0
        while req > 0 and f.available_psus > 0:
          mark_psu_assigned(f, a, psu_agents)
          req -= PSU_OFFICERS
          a.resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0:
          log.append("%d PSUs allocated from alliance %s to %s (rank=%f)" % (allocated, f.name, a.name, r[1]))
          # TODO cache route interps
          # active_routes[(f.unique_id, a.unique_id)] = { "out": linestr_out.xy, "ret": linestr_ret.xy }

    # if still not fully resourced, request other forces
    if req > 0:
      # allocations from further afield
      forces = find_other_forces(force_agents, a.name, a.Alliance, in_alliance=False)
      ranks = rank(forces, a.name, routes, a.time_to_end)
      for r in ranks:
        f = find_force(force_agents, r[0])
        allocated = 0
        while req > 0 and f.available_psus > 0:
          mark_psu_assigned(f, a, psu_agents)
          req -= PSU_OFFICERS
          a.resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0:
          log.append("%d PSUs allocated from %s to %s (rank=%f)" % (allocated, f.name, a.name, r[1]))
          #linestr_out = routes.loc[f.name, a.name]["geometry"]
          #linestr_ret = routes.loc[a.name, f.name]["geometry"]
          #active_routes[(f.unique_id, a.unique_id)] = { "out": linestr_out.xy, "ret": linestr_ret.xy }

    # if still not fully resourced, print a message
    if req > 0:
      log.append("** %s event cannot be fully resource allocated **" % a.name)

  #return active_routes