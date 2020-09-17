from mesa_geo.visualization.ModularVisualization import ModularServer
#from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter

from mesa_geo.visualization.MapModule import MapModule
from .visualization.LogElement import LogElement
from .visualization.CustomChartVisualization import CustomChartModule

from .portrayal import portray_map
from .model import PublicOrderPolicing

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
  [
    {"Label": "Avon and Somerset", "Color": "Black" },
    {"Label": "Bedfordshire", "Color": "Black" },
    {"Label": "Cheshire", "Color": "Black" },
    {"Label": "City of London", "Color": "Black" },
    {"Label": "Cleveland", "Color": "Black" },
    {"Label": "Cumbria", "Color": "Black" },
    {"Label": "Derbyshire", "Color": "Black" },
    {"Label": "Devon and Cornwall", "Color": "Black" },
    {"Label": "Dorset", "Color": "Black" },
    {"Label": "Durham", "Color": "Black" },
    {"Label": "Dyfed-Powys", "Color": "Black" },
    {"Label": "Essex", "Color": "Black" },
    {"Label": "Gloucestershire", "Color": "Black" },
    {"Label": "Greater Manchester", "Color": "Black" },
    {"Label": "Gwent", "Color": "Black" },
    {"Label": "Kent", "Color": "Black" },
    {"Label": "Hampshire", "Color": "Black" },
    {"Label": "Humberside", "Color": "Black" },
    {"Label": "Lancashire", "Color": "Black" },
    {"Label": "Leicestershire", "Color": "Black" },
    {"Label": "Lincolnshire", "Color": "Black" },
    {"Label": "Merseyside", "Color": "Black" },
    {"Label": "Metropolitan", "Color": "Black" },
    {"Label": "Norfolk", "Color": "Black" },
    {"Label": "North Wales", "Color": "Black" },
    {"Label": "North Yorkshire", "Color": "Black" },
    {"Label": "Northamptonshire", "Color": "Black" },
    {"Label": "Northumbria", "Color": "Black" },
    {"Label": "Nottinghamshire", "Color": "Black" },
    {"Label": "South Wales", "Color": "Black" },
    {"Label": "Suffolk", "Color": "Black" },
    {"Label": "Surrey", "Color": "Black" },
    {"Label": "Sussex", "Color": "Black" },
    {"Label": "South Yorkshire", "Color": "Black" },
    {"Label": "Staffordshire", "Color": "Black" },
    {"Label": "Thames Valley", "Color": "Black" },
    {"Label": "Warwickshire", "Color": "Black" },
    {"Label": "West Midlands", "Color": "Black" },
    {"Label": "West Yorkshire", "Color": "Black" },
    {"Label": "Wiltshire", "Color": "Black" },
  ],
  400
)

map_element = MapModule(portray_map, [52.9, -1.8], 6, 600, 600)
console = LogElement()

server = ModularServer(PublicOrderPolicing, [map_element, chart_element, console], "Public Order Policing Model", model_params)
