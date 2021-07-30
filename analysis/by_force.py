import geopandas as gpd
import sys
import matplotlib.pyplot as plt

from popm.initialisation import load_force_data

# NOTE: all postprocessing of simple_model output is now in analysis/by_time.py
# this file now just tests plotting force and alliance boundaries

# forces = ['Avon and Somerset', 'Beds Cambs Herts', 'Cheshire',
#        'City of London', 'Cleveland', 'Cumbria', 'Derbyshire',
#        'Devon and Cornwall', 'Dorset', 'Durham', 'Dyfed-Powys', 'Essex',
#        'Gloucestershire', 'Greater Manchester', 'Gwent', 'Hampshire',
#        'Humberside', 'Kent', 'Lancashire', 'Leicestershire',
#        'Lincolnshire', 'Merseyside', 'Metropolitan Police', 'Norfolk',
#        'North Wales', 'North Yorkshire', 'Northamptonshire',
#        'Northumbria', 'Nottinghamshire', 'South Wales', 'South Yorkshire',
#        'Staffordshire', 'Suffolk', 'Surrey', 'Sussex', 'Thames Valley',
#        'Warwickshire', 'West Mercia', 'West Midlands', 'West Yorkshire',
#        'Wiltshire']

def visualise():

  force_data, _ = load_force_data()
  force_data = force_data[["name", "geometry"]]#.set_index("name", drop=True)

  alliances = gpd.read_file("./data/alliances.geojson")

  print(alliances)

  force_data["label_anchor"] = force_data["geometry"].apply(lambda g: str(g.representative_point())) #.coords[:][0])

  print(force_data)

  ax = force_data.plot(figsize=(10,10))
  alliances.plot(ax=ax, facecolor='none', edgecolor="black")

  plt.show()


if __name__ == "__main__":
  assert len(sys.argv) == 1
  visualise()
