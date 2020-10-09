
from itertools import combinations, islice
import math
import numpy as np
import pyproj
from shapely.geometry import shape
from shapely.ops import transform
import shapely.wkt
import humanleague as hl


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

# use the MPI rank to offset the samples
def get_offset():
  try:
    import mpi4py.MPI as mpi
    return mpi.COMM_WORLD.rank
  except Exception:
    # no MPI is not an error
    return 0

# this will not perform well for n_events > 4
def sample_locations_randomly(n_locations, n_events, max_samples):

  npgen = np.random.Generator(np.random.MT19937(19937))
  locations = list(combinations(range(n_locations), n_events))
  if max_samples is not None:
    return npgen.choice(locations, max_samples, replace=False)
  return locations

# samples
def sample_locations(n_locations, n_events, max_samples):
  n_combs = math.comb(n_locations, n_events)
  step = n_combs // max_samples
  combs = combinations(range(n_locations), n_events)
  if max_samples is not None:
    return list(islice(combs, get_offset(), n_combs, step))
  return list(combs)


def sample_locations_quasi(n_locations, n_events, max_samples):

  if max_samples is None:
    return list(combinations(range(n_locations), n_events))

  locations = []
  offsets = np.full(n_events, get_offset()) # offset vector to avoid duplicating values in parallel runs

  # need to reject results containing duplicated locations, so oversample
  skips = max_samples*2
  while len(locations) < max_samples:
    seq = (hl.sobolSequence(n_events, max_samples*2, skips) * n_locations).astype(int)
    skips *= 2
    locations.extend([(s+offsets)%n_locations for s in seq if len(set(s)) == n_events])

  return locations[:max_samples]

