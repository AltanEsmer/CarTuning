"""
Mini ECU Simulator GUI

This module creates a graphical user interface using tkinter (with ttk widgets)
and matplotlib to display real-time engine simulation data.

The GUI demonstrates:
- Real-time engine parameter monitoring (RPM, Torque, AFR)
- Interactive throttle control via slider
- Stage 1 tuning toggle button
- Live torque graph visualization using matplotlib
"""

import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from engine_simulator import EngineSimulator


class ECUSimulatorApp:
    """
    Main application class for the Mini ECU Simulator.
    
    This class manages the entire GUI, including:
    - Window layout and widgets (controls and readouts)
    - Real-time data updates
    - Matplotlib plot for torque visualization
    - Connection between GUI controls and engine simulation
    """
    
    def __init__(self, master):
        """
        Initialize the ECU Simulator application.
        
        Args:
            master: The tkinter root window (Tk instance)
        
        Sets up:
        - Window properties (title, size)
        - Engine simulator instance
        - GUI layout (controls and readouts frames)
        - Matplotlib plot for real-time torque display
        - Starts the update loop
        """
        self.master = master
        self.master.title("Mini ECU Simulator")
        self.master.geometry("800x600")
        
        # Initialize the engine simulator
        # This object holds all the engine state (RPM, torque, AFR, etc.)
        self.engine = EngineSimulator()
        
        # Data storage for the torque plot
        # We keep the last 50 torque values to create a scrolling graph
        self.torque_data = [0] * 50
        
        # ===== CREATE LAYOUT STRUCTURE =====
        # We use ttk.Frame containers to organize our widgets into logical sections
        # This makes the GUI cleaner and easier to maintain
        
        # Left frame: Controls (throttle slider, tune button)
        self.controls_frame = ttk.Frame(self.master, padding="10")
        self.controls_frame.pack(side='left', fill='both', expand=False, padx=10, pady=10)
        
        # Right frame: Readouts (data displays and plot)
        self.readouts_frame = ttk.Frame(self.master, padding="10")
        self.readouts_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        # ===== CONTROLS FRAME SETUP (Left Side) =====
        self._setup_controls_frame()
        
        # ===== READOUTS FRAME SETUP (Right Side) =====
        self._setup_readouts_frame()
        
        # Start the real-time update loop
        # This will continuously update the simulation and display
        self.update_simulation()
    
    def _setup_controls_frame(self):
        """
        Set up the controls frame with throttle slider and tuning button.
        
        The controls frame is on the left side and contains:
        - Title label
        - Vertical throttle slider (0-100%)
        - Stage 1 tuning toggle button
        """
        # Section title
        controls_title = ttk.Label(
            self.controls_frame,
            text="--- Controls ---",
            font=("Arial", 12, "bold")
        )
        controls_title.pack(pady=10)
        
        # Visual separator
        ttk.Separator(self.controls_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Throttle slider label
        throttle_label = ttk.Label(
            self.controls_frame,
            text="Throttle Position:",
            font=("Arial", 10)
        )
        throttle_label.pack(pady=5)
        
        # Vertical throttle slider
        # This simulates the accelerator pedal
        # orient='vertical' makes it go up/down
        # from_=0, to=100 sets the range (0-100%)
        # length=200 sets the slider height in pixels
        self.throttle_scale = ttk.Scale(
            self.controls_frame,
            from_=0,
            to=100,
            orient='vertical',
            length=300,
            command=self._on_throttle_change  # Called when slider moves
        )
        self.throttle_scale.pack(pady=10)
        
        # Throttle value display below slider
        self.throttle_display_var = tk.StringVar(value="0%")
        throttle_display = ttk.Label(
            self.controls_frame,
            textvariable=self.throttle_display_var,
            font=("Arial", 10, "bold")
        )
        throttle_display.pack(pady=5)
        
        # Visual separator
        ttk.Separator(self.controls_frame, orient='horizontal').pack(fill='x', pady=20)
        
        # Stage 1 Tune toggle button
        # This button toggles the Stage 1 tuning on/off
        # In real cars, this would be a permanent ECU flash, but here we can toggle
        # to compare tuned vs. stock performance in real-time
        self.tune_button = ttk.Button(
            self.controls_frame,
            text="Toggle Stage 1 Tune",
            command=self.engine.toggle_tune  # Connect directly to engine method
        )
        self.tune_button.pack(pady=20)
        
        # Tune status indicator
        self.tune_status_button_var = tk.StringVar(value="Status: Inactive")
        tune_status_display = ttk.Label(
            self.controls_frame,
            textvariable=self.tune_status_button_var,
            font=("Arial", 9),
            foreground="gray"
        )
        tune_status_display.pack(pady=5)
    
    def _setup_readouts_frame(self):
        """
        Set up the readouts frame with engine data displays and torque plot.
        
        The readouts frame is on the right side and contains:
        - Engine data labels (RPM, Torque, AFR, Tune Status)
        - Matplotlib plot showing real-time torque graph
        """
        # Section title
        readouts_title = ttk.Label(
            self.readouts_frame,
            text="--- Engine Data ---",
            font=("Arial", 12, "bold")
        )
        readouts_title.pack(pady=10)
        
        # Visual separator
        ttk.Separator(self.readouts_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # ===== ENGINE DATA DISPLAYS =====
        # We use StringVar objects for the displayed values
        # StringVar automatically updates the GUI label when the value changes
        
        # RPM Display
        self.rpm_var = tk.StringVar(value="800 RPM")
        rpm_label = ttk.Label(
            self.readouts_frame,
            text="RPM:",
            font=("Arial", 10, "bold")
        )
        rpm_label.pack(anchor='w', pady=5)
        rpm_display = ttk.Label(
            self.readouts_frame,
            textvariable=self.rpm_var,
            font=("Arial", 11),
            background="lightgray",
            width=20
        )
        rpm_display.pack(anchor='w', pady=2)
        
        # Torque Display
        self.torque_var = tk.StringVar(value="0.0 Nm")
        torque_label = ttk.Label(
            self.readouts_frame,
            text="Torque:",
            font=("Arial", 10, "bold")
        )
        torque_label.pack(anchor='w', pady=5)
        torque_display = ttk.Label(
            self.readouts_frame,
            textvariable=self.torque_var,
            font=("Arial", 11),
            background="lightblue",
            width=20
        )
        torque_display.pack(anchor='w', pady=2)
        
        # AFR Display
        self.afr_var = tk.StringVar(value="14.7")
        afr_label = ttk.Label(
            self.readouts_frame,
            text="Air-Fuel Ratio:",
            font=("Arial", 10, "bold")
        )
        afr_label.pack(anchor='w', pady=5)
        afr_display = ttk.Label(
            self.readouts_frame,
            textvariable=self.afr_var,
            font=("Arial", 11),
            background="lightgreen",
            width=20
        )
        afr_display.pack(anchor='w', pady=2)
        
        # Tune Status Display
        self.tune_status_var = tk.StringVar(value="Inactive")
        tune_label = ttk.Label(
            self.readouts_frame,
            text="Tune Status:",
            font=("Arial", 10, "bold")
        )
        tune_label.pack(anchor='w', pady=5)
        tune_display = ttk.Label(
            self.readouts_frame,
            textvariable=self.tune_status_var,
            font=("Arial", 11),
            background="lightyellow",
            width=20
        )
        tune_display.pack(anchor='w', pady=2)
        
        # Visual separator before plot
        ttk.Separator(self.readouts_frame, orient='horizontal').pack(fill='x', pady=20)
        
        # ===== MATPLOTLIB PLOT SETUP =====
        # This is the advanced part: embedding a matplotlib graph in tkinter
        # We'll display a real-time scrolling graph of torque over time
        
        # Create the matplotlib Figure
        # figsize=(5, 3) sets the size in inches
        # dpi=100 sets the resolution (dots per inch)
        self.fig = Figure(figsize=(5, 3), dpi=100)
        
        # Add a subplot (the actual graph)
        # 111 means: 1 row, 1 column, plot 1 (only plot)
        self.ax = self.fig.add_subplot(111)
        
        # Configure the graph labels
        self.ax.set_title('Real-Time Torque', fontsize=10, fontweight='bold')
        self.ax.set_xlabel('Time (Updates)', fontsize=9)
        self.ax.set_ylabel('Torque (Nm)', fontsize=9)
        
        # Set Y-axis limits
        # This keeps the graph scale consistent
        # 0 to 500 Nm covers the typical torque range for this simulation
        self.ax.set_ylim(0, 500)
        
        # Create the plot line
        # We'll update this line's data in real-time
        # The comma after self.torque_line is important - it unpacks the tuple
        # returned by plot() to get just the Line2D object
        self.torque_line, = self.ax.plot(self.torque_data)
        
        # Set X-axis to show 0-50 (our data buffer size)
        self.ax.set_xlim(0, 50)
        
        # Create the "bridge" between matplotlib and tkinter
        # FigureCanvasTkAgg embeds the matplotlib figure into our tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, self.readouts_frame)
        
        # Draw the canvas and pack it into the readouts frame
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True, pady=10)
    
    def _on_throttle_change(self, value):
        """
        Callback function when throttle slider is moved.
        
        Args:
            value: The new throttle value from the slider (as string)
        
        This updates the throttle display immediately when the slider moves,
        providing instant visual feedback to the user.
        """
        throttle_val = float(value)
        self.throttle_display_var.set(f"{int(throttle_val)}%")
    
    def update_simulation(self):
        """
        Main update loop - called every 50 milliseconds.
        
        This method:
        1. Reads throttle input from slider
        2. Updates the engine simulation
        3. Updates all GUI displays
        4. Updates the matplotlib plot
        5. Schedules itself to run again in 50ms
        
        This creates a smooth real-time simulation at 20 updates per second.
        """
        # ===== UPDATE ENGINE STATE =====
        # Get current throttle value from the slider
        throttle_value = self.throttle_scale.get()
        
        # Update the engine with new throttle position
        self.engine.set_throttle(throttle_value)
        
        # Run one simulation tick
        # This calculates new RPM, torque, and AFR based on current state
        self.engine.update()
        
        # ===== UPDATE GUI DISPLAYS =====
        # Format and display RPM with comma separator (e.g., "3,500 RPM")
        self.rpm_var.set(f"{int(self.engine.rpm):,} RPM")
        
        # Format torque with one decimal place and unit (e.g., "245.5 Nm")
        self.torque_var.set(f"{self.engine.torque:.1f} Nm")
        
        # Format AFR with one decimal place (e.g., "14.7")
        self.afr_var.set(f"{self.engine.afr:.1f}")
        
        # Display tune status
        if self.engine.is_stage1_tuned:
            self.tune_status_var.set("Active")
            self.tune_status_button_var.set("Status: Active")
        else:
            self.tune_status_var.set("Inactive")
            self.tune_status_button_var.set("Status: Inactive")
        
        # ===== UPDATE PLOT DATA =====
        # This creates a scrolling graph effect
        # We maintain a buffer of the last 50 torque values
        
        # Remove the oldest value (first element)
        self.torque_data.pop(0)
        
        # Add the newest torque value (at the end)
        self.torque_data.append(self.engine.torque)
        
        # Update the plot line with new data
        # set_ydata() updates just the Y values (torque)
        # The X values remain 0-49 (our 50 data points)
        self.torque_line.set_ydata(self.torque_data)
        
        # Redraw the canvas
        # draw_idle() is efficient - it only redraws when the GUI is ready
        # This prevents excessive redraws and keeps the GUI responsive
        self.canvas.draw_idle()
        
        # Schedule this function to run again in 50 milliseconds
        # after() is non-blocking - it schedules the function but doesn't wait
        # This creates a continuous update loop without freezing the GUI
        # 50ms = 20 updates per second = smooth real-time animation
        self.master.after(50, self.update_simulation)


def main():
    """
    Main entry point for the application.
    
    Creates the tkinter root window, initializes the ECU Simulator app,
    and starts the main event loop.
    """
    # Create the tkinter root window
    root = tk.Tk()
    
    # Create and initialize the application
    app = ECUSimulatorApp(root)
    
    # Start the tkinter main event loop
    # This keeps the window open and processes user interactions
    # The loop continues until the window is closed
    root.mainloop()


if __name__ == "__main__":
    main()

