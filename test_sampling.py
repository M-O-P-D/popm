# suppress deprecation warning we can't do anything about
import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

from popm.utils import sample_locations_randomly, sample_all_locations, sample_locations_quasi

locs = 10
events = 3

# l = sample_locations_quasi(locs, events, 4)

# print(l)

l = sample_all_locations(locs, events)

print(l)