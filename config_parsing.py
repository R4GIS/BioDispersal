
from .abstract_model import *
from .metagroups import *
from .groups import *
from .selection import *
from .buffers import *
from .rasterization import *

from .utils import *

import xml.etree.ElementTree as ET

# init_model = {
    # "MetagroupModel" : MetagroupModel.__init__,
    # "GroupModel" : GroupModel.__init__,
    # "SelectionModel" : SelectionModel.__init__,
    # "BufferModel" : BufferModel.__init__,
    # "RasterModel" : RasterModel.__init__
# }

# add_item = {
    # "MetagroupModel" : MetagroupModel.addItem,
    # "GroupModel" : GroupModel.__init__,
    # "SelectionModel" : SelectionModel.__init__,
    # "BufferModel" : BufferModel.__init__,
    # "RasterModel" : RasterModel.__init__
# }

mk_item = {
    "MetagroupModel" : MetagroupModel.mkItemFromDict,
    "GroupModel" : GroupModel.mkItemFromDict,
    "SelectionModel" : SelectionModel.mkItemFromDict,
    "BufferModel" : BufferModel.mkItemFromDict,
    "RasterModel" : RasterModel.mkItemFromDict
}

config_models = None

def setConfigModels(model_dict):
    global config_models
    config_models = model_dict

def parseConfig(config_file):
    tree = ET.parse(config_file)
    root = tree.getroot()
    for model in root:
        parseModel(model)

def parseModel(model_root):
    global config_models, mk_item
    model_tag = model_root.tag
    if model_tag not in config_models:
        user_error("Unknown Model '" + model_tag + "'")
    model = config_models[model_tag]
    for item in model_root:
        dict = item.attrib
        fields = dict.keys()
        item = mk_item[model_tag](dict)
        model.addItem(item)
        