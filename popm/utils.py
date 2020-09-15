
import json
from shapely.geometry import mapping, shape

def serialise_geometry(geom):
  return json.dumps(mapping(geom))

def deserialise_geometry(json_str):
  return shape(json.loads(json_str))



