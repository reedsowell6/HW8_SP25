# region imorts
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import PyQt5.QtWidgets as qtw

# importing from previous work on least squares fit
from LeastSquares import LeastSquaresFit_Class


# endregion

# region class definitions
class Pump_Model():
    """
    This is the pump model.  It just stores data.
    """

    def __init__(self):  # pump class constructor
        # create some class variables for storing information
        self.PumpName = ""
        self.FlowUnits = ""
        self.HeadUnits = ""

        # place to store data from file
        self.FlowData = np.array([])
        self.HeadData = np.array([])
        self.EffData = np.array([])

        # place to store coefficients for cubic fits
        self.HeadCoefficients = np.array([])
        self.EfficiencyCoefficients = np.array([])

        # create two instances (objects) of least squares class
        self.LSFitHead = LeastSquaresFit_Class()
        self.LSFitEff = LeastSquaresFit_Class()


class Pump_Controller():
    def __init__(self):
        self.Model = Pump_Model()
        self.View = Pump_View()

    # region functions to modify data of the model
    def ImportFromFile(self, data):
        """
        This processes the list of strings in data to build the pump model
        :param data:  list of lines read from the file
        """
        # JES Missing Code: read PumpName from line 0
        self.Model.PumpName = data[0].strip()

        # data[1] is presumably some extra info (hp, rpm) you can ignore or parse if you want
        # data[2] is the units line
        L = data[2].split()
        # JES Missing Code: store flow and head units from line 2
        self.Model.FlowUnits = L[0]
        self.Model.HeadUnits = L[1]

        # extracts flow, head and efficiency data from lines 3 onward
        self.SetData(data[3:])
        self.updateView()

    def SetData(self, data):
        '''
        Expects three columns of data in an array of strings with space delimiter
        Parse line and build arrays.
        :param data: lines of text with "flow head efficiency"
        '''
        # erase existing data
        self.Model.FlowData = np.array([])
        self.Model.HeadData = np.array([])
        self.Model.EffData = np.array([])

        # parse new data
        for line in data:
            # JES Missing Code: parse the line into an array of strings
            Cells = line.split()
            # remove any spaces and convert string to float
            self.Model.FlowData = np.append(self.Model.FlowData, float(Cells[0]))
            self.Model.HeadData = np.append(self.Model.HeadData, float(Cells[1]))
            self.Model.EffData = np.append(self.Model.EffData, float(Cells[2]))

        # call least square fit for head and efficiency
        self.LSFit()

    def LSFit(self):
        '''Fit polynomials using Least Squares. (Head is typically quadratic or cubic,
           but your instructions say cubic for both. Adjust if needed.)'''
        # Head
        self.Model.LSFitHead.x = self.Model.FlowData
        self.Model.LSFitHead.y = self.Model.HeadData
        self.Model.LSFitHead.LeastSquares(2)  # If you truly want "quadric" for Head, use power=2
        # Or if the instructions say "cubic for head" as well, use 3:
        # self.Model.LSFitHead.LeastSquares(3)

        # Efficiency
        self.Model.LSFitEff.x = self.Model.FlowData
        self.Model.LSFitEff.y = self.Model.EffData
        self.Model.LSFitEff.LeastSquares(3)  # instructions specify cubic for efficiency

    # endregion

    # region functions interacting with view
    def setViewWidgets(self, w):
        self.View.setViewWidgets(w)

    def updateView(self):
        self.View.updateView(self.Model)
    # endregion


class Pump_View():
    def __init__(self):
        """
        In this constructor, I create some QWidgets as placeholders until they get defined later.
        """
        self.LE_PumpName = qtw.QLineEdit()
        self.LE_FlowUnits = qtw.QLineEdit()
        self.LE_HeadUnits = qtw.QLineEdit()
        self.LE_HeadCoefs = qtw.QLineEdit()
        self.LE_EffCoefs = qtw.QLineEdit()
        self.ax = None
        self.canvas = None

    def updateView(self, Model):
        """
        Put model parameters in the widgets.
        :param Model:
        :return:
        """
        self.LE_PumpName.setText(Model.PumpName)
        self.LE_FlowUnits.setText(Model.FlowUnits)
        self.LE_HeadUnits.setText(Model.HeadUnits)
        self.LE_HeadCoefs.setText(Model.LSFitHead.GetCoeffsString())
        self.LE_EffCoefs.setText(Model.LSFitEff.GetCoeffsString())
        self.DoPlot(Model)

    def DoPlot(self, Model):
        """
        Create the plot of Head and Efficiency vs Flow, along with polynomial fits.
        """
        # Get smooth x,y arrays and R^2 for the fits
        # If you used power=2 above for Head, be consistent here:
        headx, heady, headRSq = Model.LSFitHead.GetPlotInfo(2, npoints=200)
        effx, effy, effRSq = Model.LSFitEff.GetPlotInfo(3, npoints=200)

        axes = self.ax
        axes.clear()  # Clear old plot
        axes2 = axes.twinx()  # Second y-axis for efficiency

        # Plot raw data
        axes.plot(Model.FlowData, Model.HeadData, 'k^', label=f"Head Data (R²={headRSq:.3f})")
        axes2.plot(Model.FlowData, Model.EffData, 'ko', fillstyle='none', label=f"Eff Data (R²={effRSq:.3f})")

        # Plot fitted curves
        axes.plot(headx, heady, 'k--', label="Head Fit")
        axes2.plot(effx, effy, 'k:', label="Eff Fit")

        # Labels and title
        axes.set_xlabel(f"Flow Rate ({Model.FlowUnits})")
        axes.set_ylabel(f"Head ({Model.HeadUnits})")
        axes2.set_ylabel("Efficiency (%)")
        axes.set_title(Model.PumpName)

        # Combine legends from both axes
        lines1, labels1 = axes.get_legend_handles_labels()
        lines2, labels2 = axes2.get_legend_handles_labels()
        axes2.legend(lines1 + lines2, labels1 + labels2, loc='best')

        # Finally draw on the canvas
        self.canvas.draw()

    def setViewWidgets(self, w):
        """
        Called by the controller so we know which actual widgets to manipulate.
        """
        (
            self.LE_PumpName,
            self.LE_FlowUnits,
            self.LE_HeadUnits,
            self.LE_HeadCoefs,
            self.LE_EffCoefs,
            self.ax,
            self.canvas
        ) = w
# endregion