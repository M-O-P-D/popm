

import pyproj
from shapely.geometry import shape
from shapely.ops import transform
import shapely.wkt

_bng_proj = pyproj.Proj(init='epsg:27700')
_lonlat_proj = pyproj.Proj(init='epsg:4326')
_proj_bng2lonlat = pyproj.Transformer.from_proj(_bng_proj, _lonlat_proj)
_proj_lonlat2bng = pyproj.Transformer.from_proj(_lonlat_proj, _bng_proj)

def serialise_geometry(geom):
  return geom.wkt

def deserialise_geometry(wkt):
  return shapely.wkt.loads(wkt)

def bng2lonlat(shape):
  return transform(_proj_bng2lonlat.transform, shape)

def lonlat2bng(shape):
  return transform(_proj_lonlat2bng.transform, shape)

def hmm(t):
  h = int(t)
  m = int((t - h) * 60)
  return "%dh%02dm" % (h, m) 

