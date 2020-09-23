# %%

import geopandas as gpd
import pandas as pd

df = pd.read_csv("data/force_centroid_routes.zip") 

print(df.head())
print(df.tail())
# %%
from shapely import wkt
df["geometry"] = df["geometry"].apply(wkt.loads)

print(df.head())
print(df.tail())

# %%
gdf = gpd.GeoDataFrame(df)

gdf.head()
# %%
gdf.plot()
# %%
