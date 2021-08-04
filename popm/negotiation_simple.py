"""
This is a reimplementation of the negotiation algorithm for the simple_model version
It's functionally identical to the original but operates on different data structures
"""

from .initialisation import PSU_OFFICERS
import numpy as np

# NOTE: flake8 complains about (psus.assigned == False)
# BUT it is NOT the same as (~psus.assigned) nor (psus.assigned is False)


def rank_forces_by_deployment_time(force_names, event_location, psus, routes, event_end, include_reserved=False):
  """
  Ranks according to deployment time (mobilisation + travel) and supply
  include_reserved=True can be set to allow forces to use reserved PSUs of other forces in their alliance
  In practice this means City of London can access to the Met's reserved PSUs (no other force currently has any reserved PSUs)
  """
  # TODO for now ranking is based on average mobilisation time
  ranks = []
  for f in force_names:
    # print(f)
    if f != event_location:
      # print(routes)
      travel_time = routes.loc[(f, event_location)]["time"]
      if travel_time < event_end:
        if include_reserved:
          mob_times = psus[(psus.name == f) & (~psus.assigned)]["mobilisation"].values
        else:
          mob_times = psus[(psus.name == f) & (~psus.reserved) & (~psus.assigned)]["mobilisation"].values
          psus.reserved = psus.reserved.astype(bool)
        # note that if mob_times is empty this still works (you get a rank of 0)
        ranks.append((f, np.sum(1.0 / (mob_times + travel_time))))
  return sorted(ranks, key=lambda t: -t[1])


def rank_forces(force_names, event_location, psus, routes, event_end, include_reserved=False):
  """
  Ranks according to distance/cost and supply (not taking mobilisation time into account)
  include_reserved=True cab be set to allow forces to use reserved PSUs of other forces in their alliance
  In practice this means City of London can access to the Met's reserved PSUs (no other force currently has any reserved PSUs)
  """
  assert False, "use rank_forces_by_deployment_time"
  # TODO for now ranking is based on average mobilisation time
  ranks = []
  for f in force_names:
    # print(f)
    if f != event_location:
      # print(routes)
      travel_time = routes.loc[(f, event_location)]["time"]
      if travel_time < event_end:
        if include_reserved:
          avail = len(psus[(psus.name == f) & (~psus.assigned)])
        else:
          avail = len(psus[(psus.name == f) & (~psus.reserved) & (~psus.assigned)])
        ranks.append((f, avail / travel_time))
  return sorted(ranks, key=lambda t: -t[1])


def allocate(events, forces, psus, routes):

  # ensure we allocate in-location first (to stop resources being taken by other areas)
  for i, r in events.iterrows():
    # allocate self resources
    req = r["resources_required"] // PSU_OFFICERS

    # this will get up to req values
    avail = psus.loc[(psus.name == r["name"]) & (~psus.assigned)].index[:req]
    n_avail = len(avail)
    print(f"{r['name']} supplies {n_avail} PSUs to self")

    psus.loc[avail, "assigned"] = True
    psus.loc[avail, "assigned_to"] = r["name"]
    psus.loc[avail, "travel"] = 0.0

    events.loc[i, "resources_allocated"] += n_avail * PSU_OFFICERS

  # TODO: note - met non reserved PSUS are the slow to mobilise ones, is this realistic

  # now from alliance
  for i, r in events.iterrows():

    req = (r["resources_required"] - r["resources_allocated"]) // PSU_OFFICERS

    if req > 0:
      f = psus[psus.Alliance == r["Alliance"]]["name"].unique()
      ranks = rank_forces_by_deployment_time(f, r["name"], psus, routes, r["time_to_end"], include_reserved=True)

      for rank in ranks:
        avail = psus.loc[(psus.name == rank[0]) & (~psus.assigned)].index[:req]
        n_avail = len(avail)

        print(f"{rank[0]} (alliance, rank={rank[1]:.2f}) supplies {n_avail} PSUs to {r['name']}")

        psus.loc[avail, "assigned"] = True
        psus.loc[avail, "assigned_to"] = r["name"]
        psus.loc[avail, "travel"] = routes.loc[(rank[0], r["name"])]["time"]

        events.loc[i, "resources_allocated"] += n_avail * PSU_OFFICERS
        req -= n_avail
        if req <= 0:
          break

  # finally from outside alliance
  for i, r in events.iterrows():

    req = (r["resources_required"] - r["resources_allocated"]) // PSU_OFFICERS

    if req > 0:
      f = psus[psus.Alliance != r["Alliance"]]["name"].unique()
      ranks = rank_forces_by_deployment_time(f, r["name"], psus, routes, r["time_to_end"])

      for rank in ranks:
        avail = psus.loc[(psus.name == rank[0]) & (~psus.reserved) & (~psus.assigned)].index[:req]

        assert len(avail) <= req
        n_avail = len(avail)

        print(f"{rank[0]} (rank={rank[1]:.2f}) supplies {n_avail} PSUs to {r['name']}")

        psus.loc[avail, "assigned"] = True
        psus.loc[avail, "assigned_to"] = r["name"]
        psus.loc[avail, "travel"] = routes.loc[(rank[0], r["name"])]["time"]

        events.loc[i, "resources_allocated"] += n_avail * PSU_OFFICERS
        req -= n_avail
        if req <= 0:
          break

  # psus.to_csv("./psus.csv")
  # print(events)
