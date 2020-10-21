
from itertools import combinations, islice
import math
import numpy as np
import pandas as pd
import pyproj
from shapely.geometry import shape
from shapely.ops import transform
import shapely.wkt
import humanleague as hl


_bng_proj = pyproj.Proj(init='epsg:27700')
_lonlat_proj = pyproj.Proj(init='epsg:4326')
_proj_bng2lonlat = pyproj.Transformer.from_proj(_bng_proj, _lonlat_proj)
_proj_lonlat2bng = pyproj.Transformer.from_proj(_lonlat_proj, _bng_proj)

# def serialise_geometry(geom):
#   return geom.wkt

# def deserialise_geometry(wkt):
#   return shapely.wkt.loads(wkt)

def bng2lonlat(shape):
  return transform(_proj_bng2lonlat.transform, shape)

def lonlat2bng(shape):
  return transform(_proj_lonlat2bng.transform, shape)

def hmm(t):
  h = int(t)
  m = int((t - h) * 60)
  return "%dh%02dm" % (h, m)

# use the MPI rank and size to offset the samples
def run_context():
  try:
    from mpi4py import MPI
    return MPI.COMM_WORLD.rank, MPI.COMM_WORLD.size
  except Exception:
    # no MPI is not an error
    return 0,1

def collate_and_write_results(config, location_lookup, deployments, allocations, resources):

  rank, size = run_context()

  if size == 1:
    # single-process case
    location_lookup.to_csv(config.replace(".json", "_locations.csv")) # index is run id
    deployments.to_csv(config.replace(".json", ".csv"), index=False)
    allocations.to_csv(config.replace(".json", "_allocations.csv"), index=False)
    resources.to_csv(config.replace(".json", "_resources.csv"), index=False)
  else:
    # root process gets data from all the others and writes it
    from mpi4py import MPI
    comm = MPI.COMM_WORLD

    all_location_lookup = comm.gather(location_lookup, root=0)
    all_deployments = comm.gather(deployments, root=0)
    all_allocations = comm.gather(allocations, root=0)
    all_resources = comm.gather(resources, root=0)
    if rank == 0:
      pd.concat(all_location_lookup).to_csv(config.replace(".json", "_locations.csv")) # index is run id
      pd.concat(all_deployments).to_csv(config.replace(".json", ".csv"), index=False)
      pd.concat(all_allocations).to_csv(config.replace(".json", "_allocations.csv"), index=False)
      pd.concat(all_resources).to_csv(config.replace(".json", "_resources.csv"), index=False)


# this will not perform well for n_events > 4
def sample_locations_randomly(n_locations, n_events, max_samples):

  locations = list(combinations(range(n_locations), n_events))
  if max_samples is not None:
    return npgen.choice(locations, max_samples, replace=False)
  return locations

# samples
def sample_all_locations(n_locations, n_events):
  n_combs = math.comb(n_locations, n_events)
  offset, step = run_context()
  combs = combinations(range(n_locations), n_events)
  return list(islice(combs, offset, n_combs, step))

def sample_locations_quasi(n_locations, n_events, max_samples):

  n_combs = math.comb(n_locations, n_events)
  rank, size = run_context()
  if max_samples is None:
    max_samples = n_combs
  if max_samples > n_combs:
    raise ValueError("Cannot oversample combination space using quasirandom sampling, use pseudorandom instead")
  # split samples as evenly as possible over processes
  max_samples = hl.prob2IntFreq(np.full(size, 1/size), max_samples)["freq"][rank]

  if max_samples == 0:
    return []

  # workaround for issue with skipping being truncated to a power of two is to sample all the numbers in every process,
  # then take a unique chunk to ensure we get different parts of the sequence in each process
  seq = np.sort((hl.sobolSequence(1, max_samples*size, 0)[max_samples*rank:max_samples*(rank+1),0] * n_combs).astype(int))

  # need to work in order, with relative offsets with generator
  seq = np.diff(seq, prepend=0)

  combs = combinations(range(n_locations), n_events)
  locations = [next(islice(combs, s-1, None)) for s in seq]
  return locations

# seed generator differently for each process
npbitgen = np.random.MT19937(19937 + run_context()[0])
npgen = np.random.Generator(npbitgen)

