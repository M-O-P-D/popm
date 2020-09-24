from mesa_geo.visualization.ModularVisualization import ModularServer
#from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter

from mesa_geo.visualization.MapModule import MapModule
from .visualization.LogElement import LogElement
from .visualization.CustomChartVisualization import CustomChartModule

from .portrayal import portray_map
from .model import PublicOrderPolicing
from .routemodel import RouteModel

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
    "No. of officers required at each event",
    1000,
    0,
    5000,
    10,
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
  "timestep": UserSettableParameter(
    "slider",
    "Timestep (minutes)",
    15,
    5,
    120,
    5,
    description="The timestep length in minutes"
  )
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

map_element = MapModule(portray_map, [52.9, -1.8], 6, 600, 600)
console = LogElement()

server = ModularServer(PublicOrderPolicing, [map_element, chart_element, console], "Public Order Policing Model", model_params)

# test model with agents on road network
#server = ModularServer(RouteModel, [map_element, console], "Police car test", model_params)
