import geopandas as gpd
import pandas as pd
from shapely import wkt

# suppress deprecation warning we can't do anything about
import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

from mesa_geo.visualization.ModularVisualization import ModularServer
#from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter

from mesa_geo.visualization.MapModule import MapModule
from .visualization.LogElement import LogElement
from .visualization.CustomChartVisualization import CustomChartModule

from .portrayal import portray_map
from .mesa_model import PublicOrderPolicing
from .initialisation import load_force_data


# load this data once only (its a bottleneck and its constant anyway)
df = pd.read_csv("./data/force_centroid_routes.zip")
df["geometry"] = df["geometry"].apply(wkt.loads)
df["time"] = df["time"] / 3600.0 # convert travel time seconds to hours

unadjusted_force_data, centroids = load_force_data()

model_params = {
  "no_of_events": UserSettableParameter(
    "slider",
    "No. of public order events",
    3,
    1,
    40,
    1,
    description="The number of initial public order events"
  ),
  "event_locations": UserSettableParameter(
    "choice",
    "Event Locations", value="Fixed",
    choices=["Fixed", "Random", "Breaking Point"]
  ),
  "event_resources": UserSettableParameter(
    "slider",
    "No. of officers required at each event", # Small=15 PSUs, Medium=35 PSUs, Large=99 PSUs
    99*25,
    15*25,
    99*25,
    25,
    description="No. of officers required at each event"
  ),
  "event_start": UserSettableParameter(
    "slider",
    "Start time of event (hours)",
    2,
    0,
    24,
    1,
    description="Start time of event, sooner events require faster responses"
  ),
  "event_duration": UserSettableParameter(
    "slider",
    "Duration of event (hours)",
    8,
    1,
    24,
    1,
    description="Duration of event, shorter events require faster responses"
  ),
  "staff_absence": UserSettableParameter(
    "slider",
    "Staff absence rate (%)",
    0,
    0,
    100,
    1,
    description="The current staff absence rate in percent"
  ),
  "duty_ratio": UserSettableParameter(
    "slider",
    "Staff on duty (%)",
    100,
    33,
    100,
    1,
    description="The proportion of officers on duty at any given time"
  ),
  "timestep": UserSettableParameter(
    "slider",
    "Timestep (minutes)",
    15,
    5,
    120,
    5,
    description="The timestep length in minutes"
  ),
  "routes": gpd.GeoDataFrame(df).set_index(["origin", "destination"]),
  "unadjusted_force_data": unadjusted_force_data,
  "centroids": centroids
}

chart_element = CustomChartModule(
  "Event Resourcing",
  "Timestep",
  "Deployed (%)",
  model_params["timestep"].value / 60.0, # if this changes, the value doesnt get updated in the CustomChartModule, sadly
  40,
  400,
  600
)


map_element = MapModule(portray_map, [52.9, -1.8], 7, 920, 840)
console = LogElement()

server = ModularServer(PublicOrderPolicing, [map_element, chart_element, console], "Public Order Policing Model", model_params)

# test model with agents on road network
#server = ModularServer(RouteModel, [map_element, console], "Police car test", model_params)
