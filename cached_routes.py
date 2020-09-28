# %%

import geopandas as gpd
import pandas as pd

df = pd.read_csv("data/force_centroid_routes.zip")


from shapely import wkt
df["geometry"] = df["geometry"].apply(wkt.loads)

# add to self entries with t=0 and no geom
# f = df["origin"].unique()
# df2 = pd.DataFrame({"origin": f, "destination": f, "geometry": [LineString()]*len(f), "time": 0.0})
# df = df.append(df2)
# df.to_csv("data/force_centroid_routes2.zip", index=False)

gdf = gpd.GeoDataFrame(df).set_index(["origin", "destination"])

gdf.head()

# %%

print(gdf.loc["Sussex"])

# %%

g = gdf.geometry[0]

print(g.xy[0])
print(g.xy[1])

# %%

d = "Thames Valley"
o = "Sussex"

print(gdf.loc[o, d])
print(gdf.loc[o, o])
# %%
import numpy as np
from shapely.geometry import Point


l1 = gdf.loc[o, d]["geometry"]
t1 = gdf.loc[o, d]["time"]

dt = 300 # 5 mins


xy = l1.xy
ts = np.linspace(0, t1, len(xy[0]))


ti = np.arange(0.0, t1, dt)
if ti[-1] < t1:
  ti = np.append(ti, t1)

for t in ti:
  print(t, Point(np.interp(t, ts, xy[0]), np.interp(t, ts, xy[1])))

s = gpd.GeoSeries([Point(np.interp(t, ts, xy[0]), 
                         np.interp(t, ts, xy[1])) for t in ti])

# %%
