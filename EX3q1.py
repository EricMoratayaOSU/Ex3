import sys
import numpy as np
from scipy.integrate import quad
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

#region Model
class TakeoffModel:
    """
    The Model class handles all thermodynamic and aerodynamic calculations.
    It stores the constants and performs the integration to find the take-off distance.
    """
    def __init__(self):
        # Constants from the assignment prompt
        self.g_c = 32.2         # (lbm ft)/(lbf s^2)
        self.S = 1000           # Wing area
        self.C_Lmax = 2.4       # Max lift coefficient
        self.rho = 0.002377     # Air density
        self.C_D = 0.0279       # Drag coefficient
        
    def calculate_sto(self, thrust, weight):
        """
        Calculates the take-off distance (S_TO) for a given thrust and weight.
        
        Args:
            thrust (float): Engine thrust in lbf.
            weight (float): Airplane weight in lb.
            
        Returns:
            float: S_TO, the take-off distance in feet.
        """
        # 1. Calculate Stall Velocity
        V_stall = np.sqrt(weight / (0.5 * self.rho * self.S * self.C_Lmax))
        
        # 2. Calculate Take-off Velocity
        V_TO = 1.2 * V_stall
        
        # 3. Calculate A parameter
        A = self.g_c * (thrust / weight)
        
        # 4. Calculate B parameter
        B = (self.g_c / weight) * (0.5 * self.rho * self.S * self.C_D)
        
        # 5. Define the integrand and perform integration from 0 to V_TO
        def integrand(V):
            return V / (A - B * (V**2))
            
        sto, _ = quad(integrand, 0, V_TO)
        return sto

    def get_plot_data(self, target_weight):
        """
        Calculates S_TO across a range of thrusts for three weight categories.
        
        Args:
            target_weight (float): The base weight specified by the user.
            
        Returns:
            tuple: Contains the numpy array of thrusts and a dictionary with 
                   lists of calculated S_TO values keyed by their respective weight.
        """
        # The assignment requests three lines: W, W - 10000, and W + 10000
        weights = [target_weight, target_weight - 10000, target_weight + 10000]
        
        # X-axis range (estimated from the provided graph)
        thrusts = np.linspace(5000, 30000, 100) 
        
        data_dict = {}
        for w in weights:
            data_dict[w] = [self.calculate_sto(t, w) for t in thrusts]
            
        return thrusts, data_dict
#endregion

#region View
class TakeoffView(QWidget):
    """
    The View class handles the PyQt5 user interface, including input fields,
    buttons, and the embedded Matplotlib canvas for plotting.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Take-off Distance Calculator")
        self.resize(800, 600)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Input Form Layout
        input_layout = QHBoxLayout()
        
        input_layout.addWidget(QLabel("Weight (lb):"))
        self.weight_input = QLineEdit("56000") # Default value from prompt
        input_layout.addWidget(self.weight_input)
        
        input_layout.addWidget(QLabel("Thrust (lb):"))
        self.thrust_input = QLineEdit("13000") # Default value from prompt
        input_layout.addWidget(self.thrust_input)
        
        self.calc_button = QPushButton("Calculate S_TO")
        input_layout.addWidget(self.calc_button)
        
        layout.addLayout(input_layout)
        
        # Matplotlib Canvas setup
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)

    def plot_data(self, thrusts, data_dict, target_thrust, target_weight, target_sto):
        """
        Updates the Matplotlib canvas with the calculated lines and the target S_TO point.
        """
        self.ax.clear()
        
        # Plot the three weight lines
        for w, distances in data_dict.items():
            self.ax.plot(thrusts, distances, label=f"Weight: {w} lb")
            
        # Place a circle on the graph indicating STO at the specified thrust and weight
        self.ax.plot(target_thrust, target_sto, 'ro', markersize=8, 
                     label=f"Target $S_{{TO}}$ ({target_thrust} lb, {target_weight} lb): {target_sto:.0f} ft")
        
        self.ax.set_xlabel("Thrust (lb)")
        self.ax.set_ylabel("Take-off Distance (ft)")
        self.ax.set_title("Take-off Distance vs. Engine Thrust")
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()
        
    def show_error(self, message):
        """Displays an error dialog to the user."""
        QMessageBox.critical(self, "Input Error", message)
#endregion

#region Controller
class TakeoffController:
    """
    The Controller class connects the View and the Model, handling user events 
    and routing data between the interface and the math logic.
    """
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # Connect the calculate button to the handler function
        self.view.calc_button.clicked.connect(self.handle_calculate)
        
        # Trigger an initial calculation so the graph isn't empty upon load
        self.handle_calculate()
        
    def handle_calculate(self):
        """
        Reads GUI inputs, invokes the Model to perform calculations, 
        and sends the formatted data back to the View for plotting.
        """
        try:
            # Retrieve and convert input from the View
            weight = float(self.view.weight_input.text())
            thrust = float(self.view.thrust_input.text())
        except ValueError:
            self.view.show_error("Please enter valid numeric values for Weight and Thrust.")
            return
            
        # Compute the specific STO point for the marker
        target_sto = self.model.calculate_sto(thrust, weight)
        
        # Gather data for the 3 trend lines
        thrust_arr, data_dict = self.model.get_plot_data(weight)
        
        # Tell the View to update the plot
        self.view.plot_data(thrust_arr, data_dict, thrust, weight, target_sto)
#endregion

#region Main Application
def main():
    """
    Initializes the PyQt5 application and wires the MVC components together.
    """
    app = QApplication(sys.argv)
    
    # Instantiate MVC components
    model = TakeoffModel()
    view = TakeoffView()
    controller = TakeoffController(model, view)
    
    view.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
#endregion