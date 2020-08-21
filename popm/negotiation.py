
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

def mark_psu_dispatched(force_name, event_location, psu_agents):
  avail = [a for a in psu_agents if a.name == force_name and a.deployed == False]
  if len(avail) == 0:
    raise ValueError("no psu available for dispatch from %s to %s" % (force_name, event_location))
  avail[0].deployed = True
  avail[0].dispatched_to = event_location

def allocate(active, force_area_agents, force_centroid_agents, force_psu_agents, distances, event_duration, log):

  # ensure we allocate in-location first (to stop resources being taken by other areas)
  for a in active:
    # code below assumes force_area_agents and force_centroid_agents are ordered the same
    assert force_area_agents[a].name == force_centroid_agents[a].name

    # allocate self resources
    f = find_force(force_area_agents, force_centroid_agents[a].name)
    req = force_centroid_agents[a].event_resources_required

    allocated = 0
    while req > 0 and force_area_agents[a].available_psus > 0:
      mark_psu_dispatched(f.name, f.name, force_psu_agents)
      req -= PSU_OFFICERS
      force_centroid_agents[a].event_resources_allocated += PSU_OFFICERS
      # in-force are automatically present
      force_centroid_agents[a].event_resources_present += PSU_OFFICERS
      force_area_agents[a].available_psus -= 1
      force_area_agents[a].dispatched_psus += 1
      allocated += 1
    log.append("%d PSUs allocated from %s" % (allocated, force_area_agents[a].name))

  for a in active:
    # allocate self resources
    f = find_force(force_area_agents, force_centroid_agents[a].name)
    req = force_centroid_agents[a].event_resources_required - force_centroid_agents[a].event_resources_allocated

    # if not fully resourced, request from alliance member
    if req > 0:
      forces = find_other_forces(force_area_agents, force_centroid_agents[a].name, force_centroid_agents[a].Alliance)
      #print(force_centroid_agents[a].name, force_centroid_agents[a].Alliance, [f.name for f in forces])
      ranks = rank(forces, force_centroid_agents[a].name, distances, event_duration)
      for r in ranks:
        f = find_force(force_area_agents, r[0])
        allocated = 0
        while req > 0 and f.available_psus > 0:
          mark_psu_dispatched(f.name, force_centroid_agents[a].name, force_psu_agents)
          req -= PSU_OFFICERS
          force_centroid_agents[a].event_resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0: log.append("%d PSUs allocated from alliance %s to %s (rank=%f)" % (allocated, f.name, force_area_agents[a].name, r[1]))

    # if still not fully resourced, request other forces
    if req > 0:
      # allocations from further afield
      forces = find_other_forces(force_area_agents, force_centroid_agents[a].name, force_centroid_agents[a].Alliance, in_alliance=False)
      ranks = rank(forces, force_centroid_agents[a].name, distances, event_duration)
      for r in ranks:
        f = find_force(force_area_agents, r[0])
        allocated = 0
        while req > 0 and f.available_psus > 0:
          mark_psu_dispatched(f.name, force_centroid_agents[a].name, force_psu_agents)
          req -= PSU_OFFICERS
          force_centroid_agents[a].event_resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0: log.append("%d PSUs allocated from %s to %s (rank=%f)" % (allocated, f.name, force_area_agents[a].name, r[1]))
