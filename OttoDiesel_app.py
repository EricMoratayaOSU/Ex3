#region imports
from OttoDiesel_GUI import Ui_Form
from PyQt5 import uic
import sys
from PyQt5 import QtWidgets as qtw, QtCore
from Otto import ottoCycleController
from Diesel import dieselCycleController
from Dual import dualCycleController  
from Air import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
#endregion

class MainWindow(qtw.QWidget, Ui_Form):
    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here
        self.calculated = False

        # --- DYNAMIC GUI UPDATES FOR DUAL CYCLE (PART B) ---
        # 1. Add Dual Cycle to the combo box
        self.cmb_OttoDiesel.addItem("Dual cycle")

        # 2. Add the Pressure Ratio label and line edit (Places it in row 5)
        self.lbl_PRatio = qtw.QLabel("Pressure Ratio (P3/P2)")
        self.lbl_PRatio.setFont(self.lbl_CR.font())
        self.le_PRatio = qtw.QLineEdit("1.5")
        self.le_PRatio.setFont(self.le_CR.font())
        self.le_PRatio.setMaximumSize(QtCore.QSize(200, 16777215))
        
        self.gridLayout.addWidget(self.lbl_PRatio, 5, 0, 1, 1, QtCore.Qt.AlignRight)
        self.gridLayout.addWidget(self.le_PRatio, 5, 1, 1, 1)

        # 3. Hide them initially since Otto is the default cycle
        self.lbl_PRatio.setVisible(False)
        self.le_PRatio.setVisible(False)
        # --------------------------------------------------

        #creating a canvas to draw a figure for the cycle
        self.figure = Figure(figsize=(8,8), tight_layout=True, frameon=True, facecolor='none')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot()
        self.main_VerticalLayout.addWidget(self.canvas)

        #setting up some signals and slots
        self.rdo_Metric.toggled.connect(self.setUnits)
        self.btn_Calculate.clicked.connect(self.calcCycle)
        self.cmb_Abcissa.currentIndexChanged.connect(self.doPlot)
        self.cmb_Ordinate.currentIndexChanged.connect(self.doPlot)
        self.chk_LogAbcissa.stateChanged.connect(self.doPlot)
        self.chk_LogOrdinate.stateChanged.connect(self.doPlot)
        self.cmb_OttoDiesel.currentIndexChanged.connect(self.selectCycle)

        #create otto, diesel, and dual controller objects to work with later
        self.otto = ottoCycleController()
        self.diesel = dieselCycleController()
        self.dual = dualCycleController()
        
        self.controller = self.otto
        self.someWidgets = []

        self.someWidgets += [self.lbl_THigh, self.lbl_TLow, self.lbl_P0, self.lbl_V0, self.lbl_CR]
        self.someWidgets += [self.le_THigh, self.le_TLow, self.le_P0, self.le_V0, self.le_CR]
        self.someWidgets += [self.le_T1, self.le_T2, self.le_T3, self.le_T4]
        self.someWidgets += [self.lbl_T1Units, self.lbl_T2Units, self.lbl_T3Units, self.lbl_T4Units]
        self.someWidgets += [self.le_PowerStroke, self.le_CompressionStroke, self.le_HeatAdded, self.le_Efficiency]
        self.someWidgets += [self.lbl_PowerStrokeUnits, self.lbl_CompressionStrokeUnits, self.lbl_HeatInUnits]
        self.someWidgets += [self.rdo_Metric, self.cmb_Abcissa, self.cmb_Ordinate]
        self.someWidgets += [self.chk_LogAbcissa, self.chk_LogOrdinate, self.ax, self.canvas]
        
        #pass some widgets to the controller for both input and output
        self.otto.setWidgets(w=self.someWidgets)
        self.diesel.setWidgets(w=self.someWidgets)
        # Pass the extra PRatio widget ONLY to the dual controller
        self.dual.setWidgets(w=self.someWidgets + [self.le_PRatio])

        self.show()

    def clamp(self, val, low, high):
        if self.isfloat(val):
            val = float(val)
            if val > high:
                return float(high)
            if val < low:
                return float(low)
            return val
        return float(low)

    def isfloat(self, value):
        if value == 'NaN': return False
        try:
            float(value)
            return True
        except ValueError:
            return False

    def doPlot(self):
        self.controller.updateView()

    def selectCycle(self):
        cycle_idx = self.cmb_OttoDiesel.currentIndex()
        
        # Default: hide Dual specific fields
        self.lbl_PRatio.setVisible(False)
        self.le_PRatio.setVisible(False)
        
        if cycle_idx == 0:
            self.gb_Input.setTitle('Input for Air Standard Otto Cycle:')
            self.controller = self.otto
        elif cycle_idx == 1:
            self.gb_Input.setTitle('Input for Air Standard Diesel Cycle:')
            self.controller = self.diesel
        elif cycle_idx == 2:
            self.gb_Input.setTitle('Input for Air Standard Dual Cycle:')
            self.controller = self.dual
            # Show PRatio fields just for the Dual Cycle
            self.lbl_PRatio.setVisible(True)
            self.le_PRatio.setVisible(True)
            
        self.controller.updateView()

    def setUnits(self):
        self.controller.updateView()

    def calcCycle(self):
        #calculate the cycle efficiency (and states)
        self.controller.calc()

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle('Cycle Calculator')
    sys.exit(app.exec())