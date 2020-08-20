from mesa.visualization.modules.TextVisualization import TextElement

class LogElement(TextElement):
  def __init__(self):

    """ Create a new text logger element """

  @classmethod
  def render(_, model):
    """ log must be a string list """
    return "<pre>" + "\n".join(model.log[-3:]) + "</pre>"