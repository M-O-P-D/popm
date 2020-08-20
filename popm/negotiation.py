
def find_force(forces, name):
  for force in forces:
    if force.name == name: return force
  raise ValueError("Force %s not found" % name)

def find_other_forces(forces, name, alliance, in_alliance=True):
  # TODO need to ignore forces that have ongoing public order events
  other = []
  for f in forces:
    if f.name != name and (f.Alliance == alliance) == in_alliance:
      other.append(f)
  return other

def mark_psu_dispatched(force_name, event_location, psu_agents):
  avail = [a for a in psu_agents if a.name == force_name and a.deployed == False]
  if len(avail) == 0:
    raise ValueError("no psu available for dispatch from %s to %s" % (force_name, event_location))
  avail[0].deployed = True
  avail[0].dispatched_to = event_location

def allocate(active, force_area_agents, force_centroid_agents, force_psu_agents):
  for a in active:
    # code below assumes force_area_agents and force_centroid_agents are ordered the same
    assert force_area_agents[a].name == force_centroid_agents[a].name

    # allocate self resources
    f = find_force(force_area_agents, force_centroid_agents[a].name)
    req = force_centroid_agents[a].event_resources_required

    while req > 0 and force_area_agents[a].available_psus > 0:
      mark_psu_dispatched(f.name, f.name, force_psu_agents)
      req -= 25
      force_centroid_agents[a].event_resources_allocated += 25
      force_area_agents[a].available_psus -= 1
      force_area_agents[a].dispatched_psus += 1

    # if not fully resourced, request from alliance member
    if req > 0:
      # allocations from alliance
      for a in active:
        #print(force_centroid_agents[a].name, force_centroid_agents[a].Alliance)
        forces = find_other_forces(force_area_agents, force_centroid_agents[a].name, force_centroid_agents[a].Alliance)
        print(force_centroid_agents[a].name, force_centroid_agents[a].Alliance, [f.name for f in forces])

    # allocations from further afield
    forces = find_other_forces(force_area_agents, force_centroid_agents[a].name, force_centroid_agents[a].Alliance, in_alliance=False)
    #print(force_centroid_agents[a].name, force_centroid_agents[a].Alliance, [f.name for f in forces])
