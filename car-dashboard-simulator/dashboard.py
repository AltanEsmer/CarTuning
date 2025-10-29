"""
Car Dashboard GUI

This module creates a graphical user interface (GUI) using tkinter to display
real-time car simulation data. The dashboard shows RPM, temperature, and throttle,
and allows you to control the throttle using a slider.
"""

import tkinter as tk
from car_simulator import CarSimulator


def update_dashboard():
    """
    Update the dashboard display with current simulator values.
    
    This function runs in a loop (every 50 milliseconds) to create a real-time
    effect. It:
    1. Reads the current throttle value from the slider
    2. Updates the simulator state
    3. Displays the new values on screen
    
    The after() method schedules this function to run again, creating a
    continuous update loop without blocking the GUI.
    """
    # Get the current throttle position from the slider
    throttle_value = throttle_scale.get()
    
    # Update the simulator with the new throttle position
    simulator.set_throttle(int(throttle_value))
    
    # Update the simulator state (calculate new RPM, temperature, etc.)
    simulator.update()
    
    # Update the displayed values on the GUI
    # Format RPM with comma separator for readability
    rpm_var.set(f"{int(simulator.rpm):,} RPM")
    
    # Format temperature with Celsius symbol
    temp_var.set(f"{simulator.temperature:.1f}°C")
    
    # Format throttle as percentage
    throttle_var.set(f"{simulator.throttle_position}%")
    
    # Schedule this function to run again in 50 milliseconds
    # This creates a smooth real-time update effect
    # 50ms = 20 updates per second = smooth animation
    window.after(50, update_dashboard)


# Create the main application window
window = tk.Tk()
window.title("Car Dashboard Simulator")
window.geometry("400x300")
window.resizable(False, False)

# Create an instance of the car simulator
# This holds all the car's state (RPM, temperature, throttle)
simulator = CarSimulator()

# Create StringVar objects to hold display values
# StringVar is a special tkinter variable that automatically updates
# the GUI when its value changes
rpm_var = tk.StringVar(value="800 RPM")
temp_var = tk.StringVar(value="60.0°C")
throttle_var = tk.StringVar(value="0%")

# Create and arrange the dashboard layout using grid
# Grid divides the window into rows and columns for organized layout

# Row 0: RPM Display
rpm_label = tk.Label(window, text="RPM:", font=("Arial", 12, "bold"))
rpm_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

rpm_display = tk.Label(window, textvariable=rpm_var, font=("Arial", 14), 
                       bg="lightgray", width=15, anchor="w")
rpm_display.grid(row=0, column=1, padx=20, pady=10, sticky="w")

# Row 1: Temperature Display
temp_label = tk.Label(window, text="Temperature:", font=("Arial", 12, "bold"))
temp_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

temp_display = tk.Label(window, textvariable=temp_var, font=("Arial", 14),
                        bg="lightblue", width=15, anchor="w")
temp_display.grid(row=1, column=1, padx=20, pady=10, sticky="w")

# Row 2: Throttle Display
throttle_label = tk.Label(window, text="Throttle:", font=("Arial", 12, "bold"))
throttle_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

throttle_display = tk.Label(window, textvariable=throttle_var, font=("Arial", 14),
                            bg="lightgreen", width=15, anchor="w")
throttle_display.grid(row=2, column=1, padx=20, pady=10, sticky="w")

# Row 3: Throttle Control Slider
throttle_scale_label = tk.Label(window, text="Throttle Control:", 
                                font=("Arial", 12, "bold"))
throttle_scale_label.grid(row=3, column=0, padx=20, pady=20, sticky="w")

# Scale widget (slider) to control throttle from 0 to 100
# orient="horizontal" makes it a horizontal slider
# from_=0, to=100 sets the range
throttle_scale = tk.Scale(window, from_=0, to=100, orient="horizontal",
                          length=200, tickinterval=25)
throttle_scale.grid(row=3, column=1, padx=20, pady=20, sticky="w")

# Start the update loop
# This schedules the first update_dashboard() call
update_dashboard()

# Start the tkinter main event loop
# This keeps the window open and responds to user interactions
window.mainloop()

