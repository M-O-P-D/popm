from mesa_geo.visualization.ModularVisualization import ModularServer
#from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter

from mesa_geo.visualization.MapModule import MapModule
from .visualization.LogElement import LogElement

from .portrayal import portray_map
from .model import PublicOrderPolicing

model_params = {
  "no_of_events": UserSettableParameter(
    "slider",
    "No. of public order events",
    3,
    0,
    50,
    1,
    description="The number of initial public order events"
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
  "event_duration": UserSettableParameter(
    "slider",
    "Duration for which officers required at each event",
    8,
    0,
    20,
    10,
    description="Duration for which officers required at each event"
  ),
  "staff_absence": UserSettableParameter(
    "slider",
    "Staff absence rate (%)",
    0,
    0,
    100,
    1,
    description="The current staff absence rate in percent"
  )
}

# Make a world that is 50x50, on a 250x250 display.
#canvas_element = CanvasGrid(portray_cell, NX, NY, SIZE * NX, SIZE * NY)

# chart_element = ChartModule(
#   [
#     {"Label": "1st Gen", "Color": cellColour(1)},
#     {"Label": "2nd Gen", "Color": cellColour(2)},
#     {"Label": "3rd Gen", "Color": cellColour(3)},
#     {"Label": "4th Gen", "Color": cellColour(4)},
#     {"Label": "5th Gen", "Color": cellColour(5)},
#     {"Label": "6th Gen", "Color": cellColour(6)},
#     {"Label": "7th+ Gen", "Color": cellColour(7)}
#   ]
# )

map_element = MapModule(portray_map, [52.9, -1.8], 6, 640, 640)
console = LogElement()

server = ModularServer(PublicOrderPolicing, [map_element, console], "Public Order Policing Model", model_params)
