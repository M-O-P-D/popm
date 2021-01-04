from math import ceil # numpy as np
from .initialisation import PSU_OFFICERS

MIN_MOBILISATION_TIME = 1 # hour

def find_other_forces(forces, name, alliance, in_alliance=True):
  if in_alliance:
    return forces[(forces.index != name) & (forces.Alliance == alliance)]
  else:
    return forces[forces.Alliance != alliance]

def rank(forces, name, routes, event_end_minus1):
  """
  Ranks according to distance/cost and supply
  """
  # TODO for now ranking is based on average mobilisation time
  ranks = []
  for i, f in forces.iterrows():
    despatch_time = MIN_MOBILISATION_TIME
    if i != name:
      despatch_time += routes.loc[i, name]["time"]
    if despatch_time < event_end_minus1:
      ranks.append((i, (f.available_psus - f.reserved_psus) / despatch_time))
  return sorted(ranks, key=lambda t: -t[1])

def allocate(events, forces, psus, routes, logger):

  # ensure we allocate in-location first (to stop resources being taken by other areas)
  for i, r in events.iterrows():
    # allocate self resources
    req = r.resources_required / PSU_OFFICERS # no. of PSUs
    avail = len(psus[(psus.name == i) & (~psus.assigned)])
    assigned = min(req, avail)

    psus.loc[(psus.name == i) & (psus.assigned_to.isnull()), "assigned_to"] = [i] * assigned + [None] * (avail - assigned)
    psus.loc[(psus.name == i) & (~psus.assigned), "assigned"] = [True] * assigned + [False] * (avail - assigned)

    events.loc[i, "resources_allocated"] += assigned * PSU_OFFICERS # no. of officers
    logger("%d PSUs allocated from %s" % (assigned, i))

  # now allocate from alliance forces
  for i, r in events.iterrows():
    req = (r.resources_required - r.resources_allocated) // PSU_OFFICERS

    # if not fully resourced, request from alliance member
    if req > 0:
      other_forces = find_other_forces(forces, i, r.Alliance)
      ranks = rank(other_forces, i, routes, r.time_to_end)

      for k in ranks:
        avail = len(psus[(psus.name == k[0]) & (~psus.reserved) & (~psus.assigned)])
        if avail == 0: continue

        assigned = min(req, avail)
        psus.loc[(psus.name == k[0]) & (~psus.reserved) & (psus.assigned_to.isnull()), "assigned_to"] = [i] * assigned + [None] * (avail - assigned)
        psus.loc[(psus.name == k[0]) & (~psus.reserved) & (~psus.assigned), "assigned"] = [True] * assigned + [False] * (avail - assigned)

        req -= assigned
        events.loc[i, "resources_allocated"] += assigned * PSU_OFFICERS # no. of officers
        logger("%d PSUs allocated from alliance %s" % (assigned, k[0]))
        if req <= 0: break

  # now allocate from non-alliance forces
  for i, r in events.iterrows():
    req = (r.resources_required - r.resources_allocated) // PSU_OFFICERS

    # if not fully resourced, request from alliance member
    if req > 0:
      other_forces = find_other_forces(forces, i, r.Alliance, in_alliance=False)
      ranks = rank(other_forces, i, routes, r.time_to_end)

      for k in ranks:
        print(k[0], i)
        avail = len(psus[(psus.name == k[0]) & (~psus.reserved) & (~psus.assigned)])
        if avail == 0: continue

        assigned = min(req, avail)

        print(len(psus.loc[(psus.name == k[0]) & (~psus.reserved) & (psus.assigned_to.isnull()), "assigned_to"]), avail)
        if len(psus.loc[(psus.name == k[0]) & (~psus.reserved) & (psus.assigned_to.isnull())]) == 0:
          psus.to_csv("psu_data.csv")
        psus.loc[(psus.name == k[0]) & (~psus.reserved) & (psus.assigned_to.isnull()), "assigned_to"] = [i] * assigned + [""] * (avail - assigned)
        psus.loc[(psus.name == k[0]) & (~psus.reserved) & (~psus.assigned), "assigned"] = [True] * assigned + [False] * (avail - assigned)

        req -= assigned
        events.loc[i, "resources_allocated"] += assigned * PSU_OFFICERS # no. of officers
        logger("%d PSUs allocated from other %s" % (assigned, k[0]))
        if req <= 0: break

  return psus


