from math import ceil # numpy as np
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
  # TODO for now ranking is based on average mobilisation time
  ranks = []
  for f in forces:
    despatch_time = ForcePSUAgent.MIN_MOBILISATION_TIME
    if f.name != name:
      despatch_time += routes.loc[f.name, name]["time"]
    if despatch_time < event_end_minus1:
      ranks.append((f.name, (f.available_psus - f.reserved_psus) / despatch_time))
  return sorted(ranks, key=lambda t: -t[1])

def mark_psu_assigned(force_area, event_agent, psu_agents, include_reserved=False):
  avail = [a for a in psu_agents if a.name == force_area.name and not a.assigned and (include_reserved or not a.reserved)]

  if len(avail) == 0:
    return #raise ValueError("no psu available for dispatch from %s to %s" % (force_name, event_location))
  avail[0].assigned = True
  avail[0].dispatched = False
  avail[0].dispatch_time = None # computed later to meet guidelines - see allocate
  avail[0].deployed = False
  avail[0].assigned_to = event_agent.name #event_location
  avail[0].dest = event_agent.name
  avail[0].dest_id = event_agent.unique_id

def allocate(event_agents, force_agents, psu_agents, routes, log):

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
        while req > 0 and (f.available_psus - f.reserved_psus) > 0:
          mark_psu_assigned(f, a, psu_agents)
          req -= PSU_OFFICERS
          a.resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0:
          log.append("%d PSUs allocated from alliance %s to %s (rank=%f)" % (allocated, f.name, a.name, r[1]))

  for a in event_agents:
    # allocate self resources
    f = find_force(force_agents, a.name)
    req = a.resources_required - a.resources_allocated

    # if still not fully resourced, request other forces
    if req > 0:
      # allocations from further afield
      forces = find_other_forces(force_agents, a.name, a.Alliance, in_alliance=False)
      ranks = rank(forces, a.name, routes, a.time_to_end)
      for r in ranks:
        f = find_force(force_agents, r[0])
        allocated = 0
        while req > 0 and f.available_psus - f.reserved_psus > 0:
          mark_psu_assigned(f, a, psu_agents)
          req -= PSU_OFFICERS
          a.resources_allocated += PSU_OFFICERS
          f.available_psus -= 1
          f.dispatched_psus += 1
          allocated += 1
        if allocated > 0:
          log.append("%d PSUs allocated from %s to %s (rank=%f)" % (allocated, f.name, a.name, r[1]))

    # if still not fully resourced, print a message
    if req > 0:
      log.append("** %s event cannot be fully resource allocated **" % a.name)

  for e in event_agents:
    for f in force_agents:
      # first count PSUs
      psus = [psu for psu in psu_agents if e.name == psu.dest and f.name == psu.name]
      alloc = len(psus)
      if alloc:
        # create correcly sized and proportioned array of mobilisation times
        mob = [1] * int(ceil(ForcePSUAgent.MOBILISATION_TIMES[1] * alloc))
        mob.extend([4] * (int(ceil(ForcePSUAgent.MOBILISATION_TIMES[4] * alloc)) - len(mob)))
        mob.extend([8] * (int(ceil(ForcePSUAgent.MOBILISATION_TIMES[8] * alloc)) - len(mob)))
        mob.extend([16] * (alloc - len(mob)))

        assert len(mob) == alloc

        for i, psu in enumerate(psus):
          psu.dispatch_time = mob[i]

      # # round up fractions to ensure always meet the target
      #   print("CHECK: %d allocated from %s to %s %s %d" % (alloc, f.name, e.name, mob, len(mob)))

