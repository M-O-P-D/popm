from math import ceil
import re # numpy as np
from .initialisation import PSU_OFFICERS


def rank_forces(force_names, event_location, psus, routes, event_end_minus1):
  """
  Ranks according to distance/cost and supply
  """
  # TODO for now ranking is based on average mobilisation time
  ranks = []
  for f in force_names:
    #print(f)
    if f != event_location:
      #print(routes)
      despatch_time = routes.loc[(f, event_location)]["time"]
      if despatch_time < event_end_minus1:
        avail = len(psus[(psus.name == f) & (psus.reserved == False) & (psus.assigned == False)])
        ranks.append((f, avail / despatch_time))
  return sorted(ranks, key=lambda t: -t[1])

# def mark_psu_assigned(force_area, event_agent, psu_agents, include_reserved=False):
#   avail = [a for a in psu_agents if a.name == force_area.name and not a.assigned and (include_reserved or not a.reserved)]

#   if len(avail) == 0:
#     return #raise ValueError("no psu available for dispatch from %s to %s" % (force_name, event_location))
#   avail[0].assigned = True
#   avail[0].dispatched = False
#   avail[0].dispatch_time = None # computed later to meet guidelines - see allocate
#   avail[0].deployed = False
#   avail[0].assigned_to = event_agent.name #event_location
#   avail[0].dest = event_agent.name
#   avail[0].dest_id = event_agent.unique_id

def allocate(events, forces, psus, routes):

  # ensure we allocate in-location first (to stop resources being taken by other areas)
  for i, r in events.iterrows():
    # allocate self resources
    req = r["resources_required"] // PSU_OFFICERS

    # this will get up to req values
    avail = psus.loc[(psus.name == r["name"]) & (~psus.assigned)].index[:req]
    n_avail = len(avail)
    print(f"{r['name']} supplies {n_avail} PSUs to {r['name']}")

    psus.loc[avail, "assigned"] = True
    psus.loc[avail, "assigned_to"] = r["name"]
    psus.loc[avail, "deployment"] = 0.0

    events.loc[i, "resources_allocated"] += n_avail * PSU_OFFICERS

  #print(events)
  # now from alliance
  for i, r in events.iterrows():

    req = (r["resources_required"] - r["resources_allocated"]) // PSU_OFFICERS

    if req > 0:
      f = psus[psus.Alliance == r["Alliance"]]["name"].unique()
      ranks = rank_forces(f, r["name"], psus, routes, r["time_to_end"])

      for rank in ranks:
        avail = psus.loc[(psus.name == rank[0]) & (psus.reserved == False) & (psus.assigned == False)].index[:req]
        n_avail = len(avail)

        print(f"{rank[0]} supplies {n_avail} PSUs to {r['name']}")
        
        psus.loc[avail, "assigned"] = True
        psus.loc[avail, "assigned_to"] = r["name"]
        psus.loc[avail, "deployment"] = routes.loc[(rank[0], r["name"])]["time"]

        events.loc[i, "resources_allocated"] += n_avail * PSU_OFFICERS
        req -= n_avail
        if req <= 0: break
  #print(events)

  # finally from outside alliance
  for i, r in events.iterrows():

    req = (r["resources_required"] - r["resources_allocated"]) // PSU_OFFICERS

    if req > 0:
      f = psus[psus.Alliance != r["Alliance"]]["name"].unique()
      ranks = rank_forces(f, r["name"], psus, routes, r["time_to_end"])

      for rank in ranks:
        avail = psus.loc[(psus.name == rank[0]) & (psus.reserved == False) & (psus.assigned == False)].index[:req]

        assert len(avail) <= req
        n_avail = len(avail)
        
        print(f"{rank[0]} supplies {n_avail} PSUs to {r['name']}")

        psus.loc[avail, "assigned"] = True
        psus.loc[avail, "assigned_to"] = r["name"]
        psus.loc[avail, "deployment"] = routes.loc[(rank[0], r["name"])]["time"]

        events.loc[i, "resources_allocated"] += n_avail * PSU_OFFICERS
        req -= n_avail
        if req <= 0: break

  #psus.to_csv("./psus.csv")
  #print(events)
  
