
_lookup = [ "#FFFFFF", "#00FFFF", "#0000FF", "#FF00FF", "#FF0000", "#FFFF00", "#00FF00", "#000000"]

def cellColour(i):
  return _lookup[min(i,7)]

def portray_cell(cell):
  """
  This function is registered with the visualization server to be called
  each tick to indicate how to draw the cell in its current state.
  :param cell:  the cell in the simulation
  :return: the portrayal dictionary.
  """

  assert cell is not None
  return {
    "Shape": "circle",
    "r": 1,
    "Filled": "true",
    "Layer": 0,
    "x": cell.x,
    "y": cell.y,
    "Color": cellColour(cell.age)
  }


def portray_map(force_agent):
  return { "color": "Blue" }
