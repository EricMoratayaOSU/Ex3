#region imports
from Truss_GUI import Ui_TrussStructuralDesign
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from Truss_Classes import TrussController
import sys
#endregion

# ChatGPT helped write this script, specifically fixing the MVC 
# violations by routing view/scene calls through the controller.

#region class definitions
class MainWindow(Ui_TrussStructuralDesign,qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_Open.clicked.connect(self.OpenFile)
        self.spnd_Zoom.valueChanged.connect(self.setZoom)

        self.controller=TrussController()
        self.controller.setDisplayWidgets((self.te_DesignReport, self.le_LinkName, self.le_Node1Name,
                                           self.le_Node2Name, self.le_LinkLength, self.gv_Main))

        # MVC FIX: Call controller directly instead of view.scene
        self.controller.installSceneEventFilter(self) 
        self.gv_Main.setMouseTracking(True)

        self.show()

    def setZoom(self):
        self.gv_Main.resetTransform()
        self.gv_Main.scale(self.spnd_Zoom.value(), self.spnd_Zoom.value())

    def eventFilter(self, obj, event):
        # MVC FIX: Check if object is scene via controller
        if self.controller.isScene(obj):
            et = event.type()
            if et == qtc.QEvent.GraphicsSceneMouseMove:
                scenePos = event.scenePos()
                strScene = "Mouse Position:  x = {}, y = {}".format(round(scenePos.x(), 2), round(-scenePos.y(), 2))
                
                # MVC FIX: Get items via controller
                s = self.controller.getItemAt(scenePos, self.gv_Main.transform())
                if s is not None and s.data(0) is not None:
                    strScene += ' (' + s.data(0) + ')'
                
                items = self.controller.getItemsAt(event.scenePos())

                item_names = [item.name if hasattr(item, 'name') else None for item in items]
                for i in item_names:
                    strScene += ', '+(i if i is not None else 'none')
                self.lbl_MousePos.setText(strScene) 
                
            if event.type() == qtc.QEvent.GraphicsSceneWheel:  
                if event.delta() > 0:
                    self.spnd_Zoom.stepUp()
                else:
                    self.spnd_Zoom.stepDown()
            if event.type() == qtc.QEvent.ToolTip:
                pass

        return super(MainWindow, self).eventFilter(obj, event)

    def OpenFile(self):
        filename = qtw.QFileDialog.getOpenFileName()[0]
        if len(filename) == 0:  
            return
        self.te_Path.setText(filename)
        file = open(filename, 'r')  
        data = file.readlines()  
        self.controller.ImportFromFile(data)  
#endregion

def Main():
    app=qtw.QApplication(sys.argv)
    mw=MainWindow()
    sys.exit(app.exec())

if __name__=="__main__":
    Main()