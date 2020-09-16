

import pyproj
from shapely.geometry import mapping, shape
from shapely.ops import transform
import shapely.wkt

def serialise_geometry(geom):
  return geom.wkt

def deserialise_geometry(wkt):
  return shapely.wkt.loads(wkt)

def bng2lonlat(shape):
  project = pyproj.Transformer.from_proj(
      pyproj.Proj(init='epsg:27700'), # source coordinate system
      pyproj.Proj(init='epsg:4326')) # destination coordinate system

  return transform(project.transform, shape)  # apply projection


