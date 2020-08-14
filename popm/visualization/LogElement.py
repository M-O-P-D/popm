from mesa.visualization.modules.TextVisualization import TextElement

class LogElement(TextElement):
  def __init__(self):

    """ Create a new text logger element """
    pass

  def render(self, model):

    """ log must be a string list """
    return "<pre>" + "\n".join(model.log) + "</pre>"