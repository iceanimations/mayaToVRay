import site
site.addsitedir(r"R:\Pipe_Repo\Users\Qurban\utilities")
from uiContainer import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

site.addsitedir(r"R:\Pipe_Repo\Users\Hussain\packages")
import qtify_maya_window as qtfy

import os.path as osp
import sys
import pymel.core as pc


Form, Base = uic.loadUiType(r'%s\ui\window.ui'%osp.dirname(osp.dirname(osp.dirname(__file__))))

class Window(Form, Base):
    def __init__(self, parent = qtfy.getMayaWindow()):
        super(Window, self).__init__(parent)
        self.setupUi(self)
        self.closeButton.clicked.connect(self.close)
        self.convertButton.clicked.connect(self.convert)
        
        self.goodMaterials = [pc.nt.Lambert, pc.nt.Blinn, pc.nt.Phong, pc.nt.PhongE]
        
        # update the database, how many times this app is used
        site.addsitedir(r'r:/pipe_repo/users/qurban')
        import appUsageApp
        appUsageApp.updateDatabase('MayaToArnold')
        
        
    def materials(self):
        materials = []
        if self.materialButton.isChecked():
            materials[:] = pc.ls(sl = True)
        elif self.meshButton.isChecked():
            meshes = pc.ls(sl = True, type = 'mesh', dag = True)
            for mesh in meshes:
                for sg in pc.listConnections(mesh, type = 'shadingEngine'):
                    try:
                        mtrl = sg.surfaceShader.inputs()[0]
                    except:
                        continue
                    if hasattr(mtrl, 'outColor'):
                        materials.append(mtrl)
        else:
            for mtl in pc.ls(type = ['phong', 'phongE', 'blinn', 'lambert']):
                materials.append(mtl)
        if not materials:
            pc.warning('No selection or no Material found in the selection')
        return list(set(materials))
    
    def filterMaterials(self, mtls = []):
        try:
            mtls.remove("lambert1")
        except ValueError:
            pass
        if not self.lambertButton.isChecked():
            for mtl in mtls:
                if type(mtl) == pc.nt.Lambert:
                    mtls.remove(mtl)
        if not self.blinnButton.isChecked():
            for mtl in mtls:
                if type(mtl) == pc.nt.Blinn:
                    mtls.remove(mtl)
        if not self.phongButton.isChecked():
            for mtl in mtls:
                if type(mtl) == pc.nt.Phong:
                    mtls.remove(mtl)
        if not self.phongEButton.isChecked():
            for mtl in mtls:
                if type(mtl) == pc.nt.PhongE:
                    mtls.remove(mtl)
        for mtl in mtls:
            if type(mtl) not in self.goodMaterials:
                mtls.remove(mtl)
        return mtls
    
    def convert(self):
        for node in self.filterMaterials(self.materials()):
            aicmd = 'createRenderNodeCB -asShader "surfaceShader" aiStandard ""'
            arnold = pc.PyNode(pc.Mel.eval(aicmd))
            for shEng in pc.listConnections(node, type = 'shadingEngine'):
                shEng.surfaceShader.disconnect()
                arnold.outColor.connect(shEng.surfaceShader)
            name = str(node)
            pc.rename(node, "this_is_temp_node")
            if self.renameButton.isChecked():
                if "phongE" in name:
                    name = name.replace("phongE", "phonge")
            newName = name.replace((type(node).__name__).lower(), "aiStandard")
            pc.rename(arnold, newName)
            arnold.KsColor.set(node.specularColor.get())
            arnold.KrColor.set(node.reflectedColor.get())
            attr = None
            try:
                attr = node.color.inputs(plugs = True)[0]
            except:
                arnold.color.set(node.color.get())
            if attr:
                attr.disconnect()
                attr.connect(arnold.color)
            if self.removeButton.isChecked():
                pc.delete(node)