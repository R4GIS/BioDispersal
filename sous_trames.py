from PyQt5.QtCore import QVariant, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt5.QtGui import QIcon
#from .abstract_model import AbstractGroupModel, AbstractGroupItem, DictItem, DictModel, AbstractConnector
#from .utils import *
import params
import abstract_model
import utils
import os

st_fields = ["name","descr"]
stModel = None
         
def getSTByName(st_name):
    for st in stModel.items:
        if st.name == st_name:
            return st
    return None
         
def getSTList():
    return [st.dict["name"] for st in stModel.items]
         
class STItem(abstract_model.DictItem):

    def __init__(self,st,descr):
        dict = {"name" : st,
                "descr" : descr}
        self.name = st
        #assert(st_fields == dict.keys())
        super().__init__(dict)
        
    def checkItem(self):
        pass
        
    def equals(self,other):
        return (self.dict["name"] == other.dict["name"])
        
    def getSTPath(self):
        params.checkWorkspaceInit()
        all_st_path = os.path.join(params.params.workspace,"SousTrames")
        if not os.path.isdir(all_st_path):
            utils.info("Creating ST directory '" + all_st_path + "'")
            os.makedirs(all_st_path)
        st_path = os.path.join(all_st_path,self.name)
        if not os.path.isdir(st_path):
            utils.info("Creating ST directory '" + st_path + "'")
            os.makedirs(st_path)
        return st_path
        
    def getMergedPath(self):
        basename = self.name + "_merged.tif"
        st_path = self.getSTPath()
        return os.path.join(st_path,basename)
        
    def getRulesPath(self):
        basename = self.name + "_rules.txt"
        st_path = self.getSTPath()
        return os.path.join(st_path,basename)
        
    def getFrictionPath(self):
        basename = self.name + "_friction.tif"
        st_path = self.getSTPath()
        return os.path.join(st_path,basename)
        
    def getDispersionPath(self,cost):
        basename = self.name + "_dispersion_" + str(cost) + ".tif"
        st_path = self.getSTPath()
        return os.path.join(st_path,basename)
        
    def getDispersionTmpPath(self,cost):
        basename = self.name + "_dispersion_" + str(cost) + "_tmp.tif"
        st_path = self.getSTPath()
        return os.path.join(st_path,basename)
        
    def getStartLayerPath(self):
        basename = self.name + "_start.tif"
        st_path = self.getSTPath()
        return os.path.join(st_path,basename)
        
        
        
class STModel(abstract_model.DictModel):

    stAdded = pyqtSignal('PyQt_PyObject')
    stRemoved = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__(self,st_fields)
        
    @staticmethod
    def mkItemFromDict(dict):
        utils.checkFields(st_fields,dict.keys())
        item = STItem(dict["name"],dict["descr"])
        return item
        
    def addItem(self,item):
        super().addItem(item)
        self.stAdded.emit(item)
        
    def addItem(self,item):
        super().addItem(item)
        self.stAdded.emit(item)
        
    def removeItems(self,indexes):
        names = [self.items[idx.row()].dict["name"] for idx in indexes]
        utils.debug("names " + str(names))
        super().removeItems(indexes)
        for n in names:
            utils.debug("stRemoved " + str(n))
            self.stRemoved.emit(n)
        
class STConnector(abstract_model.AbstractConnector):

    def __init__(self,dlg):
        self.dlg = dlg
        self.stModel = STModel()
        super().__init__(self.stModel,self.dlg.stView,
                         self.dlg.stAdd,self.dlg.stRemove)
        
    def initGui(self):
        add = QIcon(':plugins/eco_cont/icons/add.svg')
        minus = QIcon(':plugins/eco_cont/icons/minus.svg')
        self.dlg.stAdd.setIcon(add)
        self.dlg.stAdd.setToolTip("Ajouter sous-trame")
        self.dlg.stRemove.setIcon(minus)
        self.dlg.stRemove.setToolTip("Supprimer les sous-trames sélectionnées")
        #self.dlg.stView.setColumnWidth(0,25)
        #self.dlg.stView.setColumnWidth(1,50)
        #self.dlg.stView.setColumnWidth(2,100)
        
    def connectComponents(self):
        super().connectComponents()

    def mkItem(self):
        name = self.dlg.stName.text()
        descr = self.dlg.stDescr.text()
        stItem = STItem(name,descr)
        return stItem