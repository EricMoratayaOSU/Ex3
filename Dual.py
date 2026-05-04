#region imports
from Air import *
from matplotlib import pyplot as plt
from PyQt5 import QtWidgets as qtw
import sys
import numpy as np
from copy import deepcopy as dc
#endregion

#region class definitions
class dualCycleModel():
    def __init__(self, p_initial=1E5, v_cylinder=3E-3, t_initial=300, cutoff=1.2, p_ratio=1.5, ratio=18.0, name='Air Standard Dual Cycle'):
        self.units = units()
        self.units.SI = False
        self.air = air()
        self.air.set(P=p_initial, T=t_initial)
        self.p_initial = p_initial
        self.T_initial = t_initial
        self.Ratio = ratio          # compression ratio (v1/v2)
        self.Cutoff = cutoff        # cutoff ratio (v4/v3)
        self.PRatio = p_ratio       # pressure ratio (P3/P2)
        self.V_Cylinder = v_cylinder
        self.air.n = self.V_Cylinder / self.air.State.v
        self.air.m = self.air.n * self.air.MW

        # Process 1 -> 2: Isentropic compression
        self.State1 = self.air.set(P=self.p_initial, T=self.T_initial)
        self.State2 = self.air.set(v=self.State1.v/self.Ratio, s=self.State1.s)
        
        # Process 2 -> 3: Constant volume heat addition
        self.State3 = self.air.set(v=self.State2.v, P=self.State2.P * self.PRatio)
        
        # Process 3 -> 4: Constant pressure heat addition
        self.State4 = self.air.set(P=self.State3.P, v=self.State3.v * self.Cutoff)
        
        # Process 4 -> 5: Isentropic expansion
        self.State5 = self.air.set(v=self.State1.v, s=self.State4.s)
        
        # Energy calculations
        self.W_Compression = self.air.n * (self.State2.u - self.State1.u)
        self.W_Power = self.air.n * ((self.State4.u - self.State5.u) + self.State3.P * (self.State4.v - self.State3.v))
        self.Q_In = self.air.n * ((self.State3.u - self.State2.u) + (self.State4.h - self.State3.h))
        self.Q_Out = self.air.n * (self.State5.u - self.State1.u)
        
        self.W_Cycle = self.W_Power - self.W_Compression
        self.Eff = 100.0 * self.W_Cycle / self.Q_In if self.Q_In > 0 else 0

        self.upperCurve = StateDataForPlotting()
        self.lowerCurve = StateDataForPlotting()
        self.calculated = False
        self.cycleType = 'dual'

    def getSI(self):
        return self.units.SI
    
class dualCycleController():
    def __init__(self, model=None, ax=None):
        self.model = dualCycleModel() if model is None else model
        self.view = dualCycleView()
        self.view.ax = ax

    def calc(self):
        T0 = float(self.view.le_TLow.text())
        P0 = float(self.view.le_P0.text())
        V0 = float(self.view.le_V0.text())
        cutoff = float(self.view.le_THigh.text()) 
        pratio = float(self.view.le_PRatio.text())
        CR = float(self.view.le_CR.text())
        metric = self.view.rdo_Metric.isChecked()
        self.set(T_0=T0, P_0=P0, V_0=V0, cutoff=cutoff, p_ratio=pratio, ratio=CR, SI=metric)

    def set(self, T_0=25.0, P_0=100.0, V_0=1.0, cutoff=1.2, p_ratio=1.5, ratio=18.0, SI=True):
        self.model.units.set(SI=SI)
        self.model.T_initial = T_0 if SI else T_0/self.model.units.CF_T
        self.model.p_initial = P_0 if SI else P_0/self.model.units.CF_P
        self.model.Cutoff = cutoff
        self.model.PRatio = p_ratio
        self.model.V_Cylinder = V_0 if SI else V_0/self.model.units.CF_V
        self.model.Ratio = ratio

        self.model.State1 = self.model.air.set(P=self.model.p_initial, T=self.model.T_initial, name='State 1 - BDC')
        self.model.State2 = self.model.air.set(v=self.model.State1.v/self.model.Ratio, s=self.model.State1.s, name='State 2 - TDC')
        self.model.State3 = self.model.air.set(v=self.model.State2.v, P=self.model.State2.P * self.model.PRatio, name='State 3 - TDC')
        self.model.State4 = self.model.air.set(P=self.model.State3.P, v=self.model.State3.v * self.model.Cutoff, name='State 4 - State 4')
        self.model.State5 = self.model.air.set(v=self.model.State1.v, s=self.model.State4.s, name='State 5 - BDC')

        self.model.air.n = self.model.V_Cylinder/self.model.air.State.v
        self.model.air.m = self.model.air.n*self.model.air.MW

        self.model.W_Compression = self.model.State2.u - self.model.State1.u
        self.model.W_Power = (self.model.State4.u - self.model.State5.u) + self.model.State3.P*(self.model.State4.v - self.model.State3.v)
        self.model.Q_In = (self.model.State3.u - self.model.State2.u) + (self.model.State4.h - self.model.State3.h)
        self.model.Q_Out = self.model.State5.u - self.model.State1.u

        self.model.W_Cycle = self.model.W_Power - self.model.W_Compression
        self.model.Eff = 100.0 * self.model.W_Cycle / self.model.Q_In if self.model.Q_In > 0 else 0
        self.model.calculated = True

        self.buildDataForPlotting()
        self.updateView()

    def buildDataForPlotting(self):
        self.model.upperCurve.clear()
        self.model.lowerCurve.clear()
        a = air()
        
        # upperCurve: 2-3, 3-4, 4-5, 5-1
        DeltaT = np.linspace(self.model.State2.T, self.model.State3.T, 15)
        for T in DeltaT:
            state = a.set(T=T, v=self.model.State2.v)
            self.model.upperCurve.add((state.T, state.P, state.u, state.h, state.s, state.v))
            
        DeltaT = np.linspace(self.model.State3.T, self.model.State4.T, 15)
        for T in DeltaT:
            state = a.set(T=T, P=self.model.State3.P)
            self.model.upperCurve.add((state.T, state.P, state.u, state.h, state.s, state.v))
            
        DeltaV = np.linspace(self.model.State4.v, self.model.State5.v, 30)
        for v in DeltaV:
            state = a.set(v=v, s=self.model.State4.s)
            self.model.upperCurve.add((state.T, state.P, state.u, state.h, state.s, state.v))
            
        DeltaT = np.linspace(self.model.State5.T, self.model.State1.T, 30)
        for T in DeltaT:
            state = a.set(T=T, v=self.model.State5.v)
            self.model.upperCurve.add((state.T, state.P, state.u, state.h, state.s, state.v))

        # lowerCurve: 1-2 (s=const)
        DeltaV = np.linspace(self.model.State1.v, self.model.State2.v, 30)
        for v in DeltaV:
            state = a.set(v=v, s=self.model.State1.s)
            self.model.lowerCurve.add((state.T, state.P, state.u, state.h, state.s, state.v))

    def plot_cycle_XY(self, X='s', Y='T', logx=False, logy=False, mass=False, total=False):
        self.view.plot_cycle_XY(self.model, X=X, Y=Y, logx=logx,logy=logy, mass=mass, total=total)

    def setWidgets(self, w=None):
        [self.view.lbl_THigh, self.view.lbl_TLow, self.view.lbl_P0, self.view.lbl_V0, self.view.lbl_CR,
        self.view.le_THigh, self.view.le_TLow, self.view.le_P0, self.view.le_V0, self.view.le_CR,
        self.view.le_T1, self.view.le_T2, self.view.le_T3, self.view.le_T4,
        self.view.lbl_T1Units, self.view.lbl_T2Units, self.view.lbl_T3Units, self.view.lbl_T4Units,
        self.view.le_PowerStroke, self.view.le_CompressionStroke, self.view.le_HeatAdded, self.view.le_Efficiency,
        self.view.lbl_PowerStrokeUnits, self.view.lbl_CompressionStrokeUnits, self.view.lbl_HeatInUnits,
        self.view.rdo_Metric, self.view.cmb_Abcissa, self.view.cmb_Ordinate,
        self.view.chk_LogAbcissa, self.view.chk_LogOrdinate, self.view.ax, self.view.canvas,
        self.view.le_PRatio] = w 

    def updateView(self):
        self.view.updateView(cycle=self.model)

class dualCycleView():
    def __init__(self):
        self.lbl_THigh = qtw.QLabel()
        self.lbl_TLow = qtw.QLabel() 
        self.lbl_P0 = qtw.QLabel() 
        self.lbl_V0 = qtw.QLabel() 
        self.lbl_CR = qtw.QLabel()
        self.le_THigh = qtw.QLineEdit() 
        self.le_TLow = qtw.QLineEdit() 
        self.le_P0 = qtw.QLineEdit() 
        self.le_V0 = qtw.QLineEdit() 
        self.le_CR = qtw.QLineEdit()
        self.le_PRatio = qtw.QLineEdit() 
        
        self.le_T1 = qtw.QLineEdit() 
        self.le_T2 = qtw.QLineEdit() 
        self.le_T3 = qtw.QLineEdit() 
        self.le_T4 = qtw.QLineEdit()
        self.lbl_T1Units = qtw.QLabel() 
        self.lbl_T2Units = qtw.QLabel() 
        self.lbl_T3Units = qtw.QLabel() 
        self.lbl_T4Units = qtw.QLabel()
        
        self.le_Efficiency = qtw.QLineEdit() 
        self.le_PowerStroke = qtw.QLineEdit()
        self.le_CompressionStroke=qtw.QLineEdit()
        self.le_HeatAdded = qtw.QLineEdit()
        self.lbl_PowerStrokeUnits=qtw.QLabel()
        self.lbl_CompressionStrokeUnits=qtw.QLabel()
        self.lbl_HeatInUnits = qtw.QLabel()
        
        self.rdo_Metric = qtw.QRadioButton()
        self.cmb_Abcissa = qtw.QComboBox()
        self.cmb_Ordinate = qtw.QComboBox()
        self.chk_LogAbcissa = qtw.QCheckBox()
        self.chk_LogOrdinate = qtw.QCheckBox()
        self.canvas=None
        self.ax=None

    def updateView(self, cycle):
        cycle.units.set(SI=self.rdo_Metric.isChecked())
        logx=self.chk_LogAbcissa.isChecked()
        logy=self.chk_LogOrdinate.isChecked()
        xvar=self.cmb_Abcissa.currentText()
        yvar=self.cmb_Ordinate.currentText()
        if cycle.calculated:
            self.plot_cycle_XY(cycle, X=xvar, Y=yvar, logx=logx, logy=logy, mass=False, total=True)
        self.updateDisplayWidgets(Model=cycle)

    def convertDataCol(self, cycle, data=None, colName='T', mass=False, total=False):
        UC = cycle.units
        n = cycle.air.n
        MW = cycle.air.MW
        TCF = 1.0 if UC.SI else UC.CF_T
        PCF = 1.0 if UC.SI else UC.CF_P
        hCF = 1.0 if UC.SI else UC.CF_e
        uCF = 1.0 if UC.SI else UC.CF_e
        sCF = 1.0 if UC.SI else UC.CF_s
        vCF = 1.0 if UC.SI else UC.CF_v
        nCF = 1.0 if UC.SI else UC.CF_n
        if mass:
            hCF /= MW
            uCF /= MW
            sCF /= MW
            vCF /= MW
        elif total:
            hCF *= n * nCF
            uCF *= n * nCF
            sCF *= n * nCF
            vCF *= n * nCF
        w = colName.lower()
        if w=='t': return [T*TCF for T in data]
        if w=='h': return [h*hCF for h in data]
        if w=='u': return [u*uCF for u in data]
        if w=='s': return [s*sCF for s in data]
        if w=='v': return [v*vCF for v in data]
        if w=='p': return [P*PCF for P in data]

    def plot_cycle_XY(self, cycle, X='s', Y='T',logx=False, logy=False, mass=False, total=False):
        if X==Y: return
        QTPlotting = True
        if self.ax == None:
            self.ax = plt.subplot()
            QTPlotting = False

        ax = self.ax
        ax.clear()
        ax.set_xscale('log' if logx else 'linear')
        ax.set_yscale('log' if logy else 'linear')

        XdataLC = self.convertDataCol(cycle, colName=X, data=cycle.lowerCurve.getDataCol(X), mass=mass, total=total)
        YdataLC = self.convertDataCol(cycle, colName=Y, data=cycle.lowerCurve.getDataCol(Y), mass=mass, total=total)
        XdataUC = self.convertDataCol(cycle, colName=X, data=cycle.upperCurve.getDataCol(X), mass=mass, total=total)
        YdataUC = self.convertDataCol(cycle, colName=Y, data=cycle.upperCurve.getDataCol(Y), mass=mass, total=total)
        ax.plot(XdataLC, YdataLC, color='k')
        ax.plot(XdataUC, YdataUC, color='g')

        cycle.units.setPlotUnits(SI=cycle.units.SI, mass=mass, total=total)
        ax.set_ylabel(cycle.lowerCurve.getAxisLabel(Y, Units=cycle.units), fontsize='large')
        ax.set_xlabel(cycle.lowerCurve.getAxisLabel(X, Units=cycle.units), fontsize='large')
        ax.set_title('Dual Cycle', fontsize='large')
        ax.tick_params(axis='both', which='both', direction='in', top=True, right=True, labelsize='large')

        states = [dc(cycle.State1), dc(cycle.State2), dc(cycle.State3), dc(cycle.State4), dc(cycle.State5)]
        for s in states:
            s.ConvertStateData(SI=cycle.getSI(), Units=cycle.units, n=cycle.air.n, MW=cycle.air.MW, mass=mass, total=total)
            ax.plot(s.getVal(X), s.getVal(Y), marker='o', markerfacecolor='w', markeredgecolor='k')

        if not QTPlotting:
            plt.show()
        else:
            self.canvas.draw()

    def updateDisplayWidgets(self, Model=None):
        U = Model.units
        SI = U.SI

        self.lbl_THigh.setText('Cutoff rc:  ')
        self.lbl_TLow.setText('T Low ({})'.format(Model.units.TUnits))
        self.lbl_P0.setText('P0 ({})'.format(Model.units.PUnits))
        self.lbl_V0.setText('V0 ({})'.format(Model.units.VUnits))

        if Model.units.changed or Model.calculated:
            if Model.calculated:
                CFE = 1.0 if SI else U.CF_E
                CFP = 1.0 if SI else U.CF_P
                CFV = 1.0 if SI else U.CF_V
                self.le_THigh.setText('{:0.2f}'.format(Model.Cutoff))
                self.le_TLow.setText(('{:0.2f}'.format(Model.T_initial if SI else U.T_KtoR(Model.T_initial))))
                self.le_P0.setText('{:0.2f}'.format(Model.p_initial * CFP))
                self.le_V0.setText('{:0.4f}'.format(Model.V_Cylinder*CFV))
                self.le_PRatio.setText('{:0.2f}'.format(Model.PRatio))

                self.le_T1.setText('{:0.2f}'.format(Model.State1.T if SI else U.T_KtoR(Model.State1.T)))
                self.le_T2.setText('{:0.2f}'.format(Model.State2.T if SI else U.T_KtoR(Model.State2.T)))
                self.le_T3.setText('{:0.2f}'.format(Model.State3.T if SI else U.T_KtoR(Model.State3.T)))
                self.le_T4.setText('{:0.2f}'.format(Model.State4.T if SI else U.T_KtoR(Model.State4.T)))

                self.le_Efficiency.setText('{:0.3f}'.format(Model.Eff))
                self.le_PowerStroke.setText('{:0.3f}'.format(Model.air.n*Model.W_Power*CFE))
                self.le_CompressionStroke.setText('{:0.3f}'.format(Model.air.n*Model.W_Compression*CFE))
                self.le_HeatAdded.setText('{:0.3f}'.format(Model.air.n*Model.Q_In*CFE))
            else:
                CFP = 1/U.CF_P if SI else U.CF_P
                CFV = 1/U.CF_V if SI else U.CF_V
                t_initial = float(self.le_TLow.text())
                p_initial = float(self.le_P0.text())
                v_initial = float(self.le_V0.text())
                self.le_THigh.setText('1.2')
                self.le_PRatio.setText('1.5')
                self.le_TLow.setText(('{:0.2f}'.format(U.T_RtoK(t_initial) if SI else U.T_KtoR(t_initial))))
                self.le_P0.setText('{:0.2f}'.format(p_initial * CFP))
                self.le_V0.setText('{:0.4f}'.format(v_initial * CFV))
            Model.units.changed = False
#endregion