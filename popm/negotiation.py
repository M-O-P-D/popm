
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

def allocate(active, force_area_agents, force_centroid_agents):
  for a in active:
    # allocate self resources
    f = find_force(force_area_agents, force_centroid_agents[a].name)

    req = force_centroid_agents[a].event_resources_required

    while req > 0 and force_area_agents[a].available_psus > 0:
      req -= 25
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
