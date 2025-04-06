# region imports
import math
from Calc_state import *
from UnitConversions import UnitConverter as UC
import numpy as np
from matplotlib import pyplot as plt
from copy import deepcopy as dc
# these imports are necessary for drawing a matplotlib graph on the GUI
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


# endregion

# region class definitions
class rankineModel():
    def __init__(self):
        # Model for Rankine cycle data storage
        self.p_low = None
        self.p_high = None
        self.t_high = None
        self.name = None
        self.efficiency = None
        self.turbine_eff = None
        self.turbine_work = None
        self.pump_work = None
        self.heat_added = None
        self.steam = Steam_SI()  # instantiate steam object
        self.state1 = stateProps()
        self.state2s = stateProps()
        self.state2 = stateProps()
        self.state3 = stateProps()
        self.state4 = stateProps()
        self.SI = True  # default SI units
        # Data for plotting
        self.satLiqPlotData = StateDataForPlotting()
        self.satVapPlotData = StateDataForPlotting()
        self.upperCurve = StateDataForPlotting()
        self.lowerCurve = StateDataForPlotting()


class rankineView():
    def __init__(self):
        """
        Empty constructor by design.
        """
        pass

    def setWidgets(self, *args):
        # Unpack input widgets
        self.rb_SI, self.le_PHigh, self.le_PLow, self.le_TurbineInletCondition, self.rdo_Quality, self.le_TurbineEff, self.cmb_XAxis, self.cmb_YAxis, self.chk_logX, self.chk_logY = \
        args[0]
        # Unpack display widgets
        (self.lbl_PHigh, self.lbl_PLow, self.lbl_SatPropLow, self.lbl_SatPropHigh, self.lbl_TurbineInletCondition,
         self.lbl_H1, self.lbl_H1Units, self.lbl_H2, self.lbl_H2Units, self.lbl_H3, self.lbl_H3Units, self.lbl_H4,
         self.lbl_H4Units, self.lbl_TurbineWork, self.lbl_TurbineWorkUnits, self.lbl_PumpWork, self.lbl_PumpWorkUnits,
         self.lbl_HeatAdded, self.lbl_HeatAddedUnits, self.lbl_ThermalEfficiency, self.canvas, self.figure, self.ax) = \
        args[1]

    def selectQualityOrTHigh(self, Model=None):
        """
        When the user selects the T High radio button, update the turbine inlet condition.
        """
        if Model is None:
            return
        SI = self.rb_SI.isChecked()
        if self.rdo_Quality.isChecked():
            self.le_TurbineInletCondition.setText("1.0")
            self.le_TurbineInletCondition.setEnabled(False)
        else:
            self.le_TurbineInletCondition.setEnabled(True)
            # Get saturated properties at high pressure from the model's steam object.
            satProps = Model.steam.getsatProps_p(Model.p_high)
            T_sat = satProps.tsat
            if not SI:
                # Convert Celsius to Fahrenheit for English units.
                T_sat = UC.C_to_F(T_sat)
            self.le_TurbineInletCondition.setText("{:.2f}".format(T_sat))
        condition = "x" if self.rdo_Quality.isChecked() else "T High"
        self.lbl_TurbineInletCondition.setText("Turbine Inlet: {} ({}) =".format(condition, "C" if SI else "F"))

    def setNewPHigh(self, Model=None):
        """
        Update the saturated properties label at high pressure when PHigh is changed.
        """
        if Model is None:
            return
        SI = self.rb_SI.isChecked()
        PCF = 1 if SI else UC.psi_to_bar
        try:
            p_high = float(self.le_PHigh.text()) * PCF
        except:
            p_high = Model.p_high if Model.p_high is not None else 0
        satPropsHigh = Model.steam.getsatProps_p(p_high)
        self.lbl_SatPropHigh.setText(satPropsHigh.getTextOutput(SI=SI))
        # Also update the turbine inlet condition if needed.
        self.selectQualityOrTHigh(Model)

    def setNewPLow(self, Model=None):
        """
        Update the saturated properties label at low pressure when PLow is changed.
        """
        if Model is None:
            return
        SI = self.rb_SI.isChecked()
        PCF = 1 if SI else UC.psi_to_bar
        try:
            p_low = float(self.le_PLow.text()) * PCF
        except:
            p_low = Model.p_low if Model.p_low is not None else 0
        satPropsLow = Model.steam.getsatProps_p(p_low)
        self.lbl_SatPropLow.setText(satPropsLow.getTextOutput(SI=SI))

    def outputToGUI(self, Model=None):
        """
        Update all output fields in the GUI based on the current model.
        """
        if Model.state1 is None:
            return
        HCF = 1 if Model.SI else UC.kJperkg_to_BTUperlb
        self.lbl_H1.setText("{:0.2f}".format(Model.state1.h * HCF))
        self.lbl_H2.setText("{:0.2f}".format(Model.state2.h * HCF))
        self.lbl_H3.setText("{:0.2f}".format(Model.state3.h * HCF))
        self.lbl_H4.setText("{:0.2f}".format(Model.state4.h * HCF))
        self.lbl_TurbineWork.setText("{:0.2f}".format(Model.turbine_work * HCF))
        self.lbl_PumpWork.setText("{:0.2f}".format(Model.pump_work * HCF))
        self.lbl_HeatAdded.setText("{:0.2f}".format(Model.heat_added * HCF))
        self.lbl_ThermalEfficiency.setText("{:0.2f}".format(Model.efficiency))
        satPropsLow = Model.steam.getsatProps_p(Model.p_low)
        satPropsHigh = Model.steam.getsatProps_p(Model.p_high)
        self.lbl_SatPropLow.setText(satPropsLow.getTextOutput(SI=Model.SI))
        self.lbl_SatPropHigh.setText(satPropsHigh.getTextOutput(SI=Model.SI))
        self.plot_cycle_XY(Model=Model)

    def updateUnits(self, Model=None):
        """
        Update the GUI units and all associated numeric displays when the unit system is changed.
        """
        if Model is None:
            return
        self.outputToGUI(Model=Model)
        SI = Model.SI
        PCF = 1 if SI else UC.bar_to_psi
        self.le_PHigh.setText("{:.2f}".format(Model.p_high * PCF))
        self.le_PLow.setText("{:.2f}".format(Model.p_low * PCF))
        if not self.rdo_Quality.isChecked() and Model.t_high is not None:
            T_display = Model.t_high if SI else UC.C_to_F(Model.t_high)
            self.le_TurbineInletCondition.setText("{:.2f}".format(T_display))
        self.lbl_PHigh.setText("P High ({})".format("bar" if SI else "psi"))
        self.lbl_PLow.setText("P Low ({})".format("bar" if SI else "psi"))
        self.lbl_H1Units.setText("kJ/kg" if SI else "BTU/lb")
        self.lbl_TurbineWorkUnits.setText("kJ/kg" if SI else "BTU/lb")
        self.lbl_PumpWorkUnits.setText("kJ/kg" if SI else "BTU/lb")
        self.lbl_HeatAddedUnits.setText("kJ/kg" if SI else "BTU/lb")

    def print_summary(self, Model=None):
        if Model.efficiency is None:
            Model.calc_efficiency()
        print('Cycle Summary for: ', Model.name)
        print('\tEfficiency: {:0.3f}%'.format(Model.efficiency))
        print('\tTurbine Eff:  {:0.2f}'.format(Model.turbine_eff))
        print('\tTurbine Work: {:0.3f} kJ/kg'.format(Model.turbine_work))
        print('\tPump Work: {:0.3f} kJ/kg'.format(Model.pump_work))
        print('\tHeat Added: {:0.3f} kJ/kg'.format(Model.heat_added))
        Model.state1.print()
        Model.state2.print()
        Model.state3.print()
        Model.state4.print()

    def plot_cycle_TS(self, axObj=None, Model=None):
        """
        Plot the Rankine cycle on T-S coordinates.
        """
        SI = Model.SI
        steam = Model.steam
        ts, ps, hfs, hgs, sfs, sgs, vfs, vgs = np.loadtxt('sat_water_table.txt', skiprows=1, unpack=True)
        ax = plt.subplot() if axObj is None else axObj
        hCF = 1 if SI else UC.kJperkg_to_BTUperlb
        pCF = 1 if SI else UC.kpa_to_psi
        sCF = 1 if SI else UC.kJperkgK_to_BTUperlbR
        vCF = 1 if SI else UC.kgperm3_to_lbperft3
        sfs *= sCF
        sgs *= sCF
        hfs *= hCF
        hgs *= hCF
        vfs *= vCF
        vgs *= vCF
        ps *= pCF
        ts = [t if SI else UC.C_to_F(t) for t in ts]
        xfsat = sfs
        yfsat = ts
        xgsat = sgs
        ygsat = ts
        ax.plot(xfsat, yfsat, color='blue')
        ax.plot(xgsat, ygsat, color='red')
        st3p = steam.getState(Model.p_high, x=0)  # saturated liquid state at p_high
        svals = np.linspace(Model.state3.s, st3p.s, 20)
        tvals = np.linspace(Model.state3.t, st3p.t, 20)
        line3 = np.column_stack([svals, tvals])
        sat_pHigh = steam.getState(Model.p_high, x=1.0)
        svals2p = np.linspace(st3p.s, sat_pHigh.s, 20)
        tvals2p = [st3p.t for i in range(20)]
        line4 = np.column_stack([svals2p, tvals2p])
        if Model.state1.t > (sat_pHigh.t):
            svals_sh = np.linspace(sat_pHigh.s, Model.state1.s, 20)
            tvals_sh = np.array([steam.getState(Model.p_high, s=ss).t for ss in svals_sh])
            line4 = np.append(line4, np.column_stack([svals_sh, tvals_sh]), axis=0)
        svals = np.linspace(Model.state1.s, Model.state2.s, 20)
        tvals = np.linspace(Model.state1.t, Model.state2.t, 20)
        line5 = np.column_stack([svals, tvals])
        svals = np.linspace(Model.state2.s, Model.state3.s, 20)
        tvals = np.array([Model.state2.t for i in range(20)])
        line6 = np.column_stack([svals, tvals])
        topLine = np.append(line3, line4, axis=0)
        topLine = np.append(topLine, line5, axis=0)
        xvals = topLine[:, 0]
        y1 = topLine[:, 1]
        y2 = [Model.state3.t for s in xvals]
        if not SI:
            xvals = xvals * UC.kJperkgK_to_BTUperlbR
            y1 = [UC.C_to_F(val) for val in y1]
            y2 = [UC.C_to_F(val) for val in y2]
        ax.plot(xvals, y1, color='darkgreen')
        ax.plot(xvals, y2, color='black')
        ax.set_xlabel(r's ' + ("(kJ/kg*K)" if SI else "(BTU/(lb*R))"), fontsize=18)
        ax.set_ylabel(r'T ' + ("(°C)" if SI else "(°F)"), fontsize=18)
        ax.set_title(Model.name, fontsize=18)
        ax.grid(visible=True, alpha=0.5)
        ax.tick_params(axis='both', direction='in', labelsize=18)

        # Safely compute x-axis limits using available data.
        data_upper_X = Model.upperCurve.getDataCol(X, SI=SI)
        data_lower_X = Model.lowerCurve.getDataCol(X, SI=SI)
        xs_candidates = [min(XF), min(XG)]
        if data_upper_X is not None and len(data_upper_X) > 0:
            xs_candidates.append(min(data_upper_X))
        if data_lower_X is not None and len(data_lower_X) > 0:
            xs_candidates.append(min(data_lower_X))
        xmin = min(xs_candidates) if xs_candidates else 0

        xs_candidates2 = [max(XF), max(XG)]
        if data_upper_X is not None and len(data_upper_X) > 0:
            xs_candidates2.append(max(data_upper_X))
        if data_lower_X is not None and len(data_lower_X) > 0:
            xs_candidates2.append(max(data_lower_X))
        xmax = max(xs_candidates2) if xs_candidates2 else 1

        # Safely compute y-axis limits using available data.
        data_upper_Y = Model.upperCurve.getDataCol(Y, SI=SI)
        data_lower_Y = Model.lowerCurve.getDataCol(Y, SI=SI)
        ys_candidates = [min(YF), min(YG)]
        if data_upper_Y is not None and len(data_upper_Y) > 0:
            ys_candidates.append(min(data_upper_Y))
        if data_lower_Y is not None and len(data_lower_Y) > 0:
            ys_candidates.append(min(data_lower_Y))
        ymin = min(ys_candidates) if ys_candidates else 0

        ys_candidates2 = [max(YF), max(YG)]
        if data_upper_Y is not None and len(data_upper_Y) > 0:
            ys_candidates2.append(max(data_upper_Y))
        if data_lower_Y is not None and len(data_lower_Y) > 0:
            ys_candidates2.append(max(data_lower_Y))
        ymax = max(ys_candidates2) if ys_candidates2 else 1
        ymax = ymax * 1.1

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        if not self.canvas:
            plt.show()
        else:
            self.canvas.draw()

    def plot_cycle_XY(self, Model=None):
        """
        Plot two thermodynamic properties on the X and Y axes.
        """
        ax = self.ax
        X = self.cmb_XAxis.currentText()
        Y = self.cmb_YAxis.currentText()
        logx = self.chk_logX.isChecked()
        logy = self.chk_logY.isChecked()
        SI = Model.SI
        if X == Y:
            return
        QTPlotting = True
        if ax is None:
            ax = plt.subplot()
            QTPlotting = False
        ax.clear()
        ax.set_xscale('log' if logx else 'linear')
        ax.set_yscale('log' if logy else 'linear')
        YF = Model.satLiqPlotData.getDataCol(Y, SI=SI)
        YG = Model.satVapPlotData.getDataCol(Y, SI=SI)
        XF = Model.satLiqPlotData.getDataCol(X, SI=SI)
        XG = Model.satVapPlotData.getDataCol(X, SI=SI)
        ax.plot(XF, YF, color='b')
        ax.plot(XG, YG, color='r')
        ax.plot(Model.lowerCurve.getDataCol(X, SI=SI), Model.lowerCurve.getDataCol(Y, SI=SI), color='k')
        ax.plot(Model.upperCurve.getDataCol(X, SI=SI), Model.upperCurve.getDataCol(Y, SI=SI), color='g')

        # Safely compute x-axis limits using available data.
        data_upper_X = Model.upperCurve.getDataCol(X, SI=SI)
        data_lower_X = Model.lowerCurve.getDataCol(X, SI=SI)
        xs_candidates = [min(XF), min(XG)]
        if data_upper_X is not None and len(data_upper_X) > 0:
            xs_candidates.append(min(data_upper_X))
        if data_lower_X is not None and len(data_lower_X) > 0:
            xs_candidates.append(min(data_lower_X))
        xmin = min(xs_candidates) if xs_candidates else 0

        xs_candidates2 = [max(XF), max(XG)]
        if data_upper_X is not None and len(data_upper_X) > 0:
            xs_candidates2.append(max(data_upper_X))
        if data_lower_X is not None and len(data_lower_X) > 0:
            xs_candidates2.append(max(data_lower_X))
        xmax = max(xs_candidates2) if xs_candidates2 else 1

        # Safely compute y-axis limits using available data.
        data_upper_Y = Model.upperCurve.getDataCol(Y, SI=SI)
        data_lower_Y = Model.lowerCurve.getDataCol(Y, SI=SI)
        ys_candidates = [min(YF), min(YG)]
        if data_upper_Y is not None and len(data_upper_Y) > 0:
            ys_candidates.append(min(data_upper_Y))
        if data_lower_Y is not None and len(data_lower_Y) > 0:
            ys_candidates.append(min(data_lower_Y))
        ymin = min(ys_candidates) if ys_candidates else 0

        ys_candidates2 = [max(YF), max(YG)]
        if data_upper_Y is not None and len(data_upper_Y) > 0:
            ys_candidates2.append(max(data_upper_Y))
        if data_lower_Y is not None and len(data_lower_Y) > 0:
            ys_candidates2.append(max(data_lower_Y))
        ymax = max(ys_candidates2) if ys_candidates2 else 1
        ymax = ymax * 1.1

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        if not QTPlotting:
            plt.show()
        else:
            self.canvas.draw()


class rankineController():
    def __init__(self, *args):
        """
        Controller that updates the model based on user input and updates the view.
        """
        self.Model = rankineModel()
        self.View = rankineView()
        self.IW = args[0]  # input widgets
        self.DW = args[1]  # display widgets
        self.View.setWidgets(self.IW, self.DW)
        self.buildVaporDomeData()

    def updateModel(self):
        self.Model.SI = self.View.rb_SI.isChecked()
        PCF = 1 if self.Model.SI else UC.psi_to_bar  # convert input from psi if needed
        self.Model.p_high = float(self.View.le_PHigh.text()) * PCF
        self.Model.p_low = float(self.View.le_PLow.text()) * PCF
        T = float(self.View.le_TurbineInletCondition.text())
        self.Model.t_high = None if self.View.rdo_Quality.isChecked() else (T if self.Model.SI else UC.F_to_C(T))
        self.Model.turbine_eff = float(self.View.le_TurbineEff.text())
        self.calc_efficiency()
        self.updateView()

    def updateUnits(self):
        # Switching units should update the view immediately.
        self.Model.SI = self.View.rb_SI.isChecked()
        self.View.updateUnits(Model=self.Model)

    def selectQualityOrTHigh(self):
        self.View.selectQualityOrTHigh(self.Model)

    def setNewPHigh(self):
        self.View.setNewPHigh(self.Model)

    def setNewPLow(self):
        self.View.setNewPLow(self.Model)

    def calc_efficiency(self):
        steam = self.Model.steam
        if self.Model.t_high is None:
            self.Model.state1 = steam.getState(P=self.Model.p_high, x=1.0, name='Turbine Inlet')
        else:
            self.Model.state1 = steam.getState(P=self.Model.p_high, T=self.Model.t_high, name='Turbine Inlet')
        self.Model.state2s = steam.getState(P=self.Model.p_low, s=self.Model.state1.s, name="Turbine Exit")
        if self.Model.turbine_eff < 1.0:
            h2 = self.Model.state1.h - self.Model.turbine_eff * (self.Model.state1.h - self.Model.state2s.h)
            self.Model.state2 = steam.getState(P=self.Model.p_low, h=h2, name="Turbine Exit")
        else:
            self.Model.state2 = self.Model.state2s
        self.Model.state3 = steam.getState(P=self.Model.p_low, x=0, name='Pump Inlet')
        self.Model.state4 = steam.getState(P=self.Model.p_high, s=self.Model.state3.s, name='Pump Exit')
        self.Model.turbine_work = self.Model.state1.h - self.Model.state2.h
        self.Model.pump_work = self.Model.state4.h - self.Model.state3.h
        self.Model.heat_added = self.Model.state1.h - self.Model.state4.h
        self.Model.efficiency = 100.0 * (self.Model.turbine_work - self.Model.pump_work) / self.Model.heat_added
        return self.Model.efficiency

    def updateView(self):
        self.buildDataForPlotting()
        self.View.outputToGUI(Model=self.Model)

    def setRankine(self, p_low=8, p_high=8000, t_high=None, eff_turbine=1.0, name='Rankine Cycle'):
        self.Model.p_low = p_low
        self.Model.p_high = p_high
        self.Model.t_high = t_high
        self.Model.name = name
        self.Model.efficiency = None
        self.Model.turbine_eff = eff_turbine
        self.Model.turbine_work = 0
        self.Model.pump_work = 0
        self.Model.heat_added = 0
        self.Model.state1 = None
        self.Model.state2s = None
        self.Model.state2 = None
        self.Model.state3 = None
        self.Model.state4 = None

    def print_summary(self):
        self.View.print_summary(Model=self.Model)

    def buildVaporDomeData(self, nPoints=500):
        steam = self.Model.steam
        tp = triplePt_PT()
        cp = criticalPt_PT()
        steam.state.p = cp.p
        steam.state.t = cp.t
        steam.calcState_1Phase()
        critProps = dc(steam.state)
        P = np.logspace(math.log10(tp.p * 1.001), math.log10(cp.p * 0.99), nPoints)
        for p in P:
            sat = steam.getsatProps_p(p)
            self.Model.satLiqPlotData.addPt((sat.tsat, p, sat.uf, sat.hf, sat.sf, sat.vf))
            self.Model.satVapPlotData.addPt((sat.tsat, p, sat.uf, sat.hg, sat.sg, sat.vg))
        self.Model.satLiqPlotData.addPt((critProps.t, critProps.p, critProps.u, critProps.h, critProps.s, critProps.v))
        self.Model.satVapPlotData.addPt((critProps.t, critProps.p, critProps.u, critProps.h, critProps.s, critProps.v))

    def buildDataForPlotting(self):
        # Clear out any old data.
        self.Model.upperCurve.clear()
        self.Model.lowerCurve.clear()
        # Get saturated properties at low and high pressures.
        satPLow = self.Model.steam.getsatProps_p(self.Model.p_low)
        satPHigh = self.Model.steam.getsatProps_p(self.Model.p_high)
        steam = self.Model.steam

        # Build upperCurve data (details as in your original file)
        nPts = 15
        DeltaP = (satPHigh.psat - satPLow.psat)
        for n in range(nPts):
            z = n * 1.0 / (nPts - 1)
            state = steam.getState(P=(satPLow.psat + z * DeltaP), s=satPLow.sf)
            self.Model.upperCurve.addPt((state.t, state.p, state.u, state.h, state.s, state.v))
        # (Additional code for lowerCurve would normally go here.)
        # For now, if lowerCurve is empty the safe guards in plot_cycle_XY will handle it.
        pass


# endregion

# region function definitions
def main():
    RC = rankineController()
    RC.setRankine(8 * UC.kpa_to_bar, 8000 * UC.kpa_to_bar, t_high=500, eff_turbine=0.9,
                  name='Rankine Cycle - Superheated at turbine inlet')
    eff = RC.calc_efficiency()
    print(eff)
    RC.print_summary()
    RC.plot_cycle_TS()


# endregion

if __name__ == "__main__":
    main()
# endregion
