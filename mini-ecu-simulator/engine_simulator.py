"""
Engine Simulator - Core Simulation Logic

This module contains the EngineSimulator class that models advanced engine behavior
including RPM, throttle, Air-Fuel Ratio (AFR), torque, and Stage 1 tuning effects.

Key Concepts for ECU Tuning:
- RPM (Revolutions Per Minute): Engine crankshaft speed
- Throttle Position: How much the throttle valve is open (0-100%)
- AFR (Air-Fuel Ratio): Ratio of air to fuel in the combustion mixture
  - 14.7:1 = Stoichiometric (theoretical perfect ratio)
  - Lower values (e.g., 12.0-12.5) = Rich mixture (more fuel) = More power
  - Higher values (e.g., 15.0+) = Lean mixture (less fuel) = Better fuel economy
- Torque: Rotational force produced by the engine (measured in Newton-meters, Nm)
- Stage 1 Tuning: ECU remap that increases power/torque (typically 10-20% gain)
"""


class EngineSimulator:
    """
    Simulates an engine's behavior with advanced ECU tuning parameters.
    
    This class models how an Engine Control Unit (ECU) manages engine performance
    based on throttle input, RPM, and tuning modifications. The ECU adjusts air-fuel
    ratio and power output to optimize performance while maintaining engine safety.
    """
    
    def __init__(self):
        """
        Initialize the engine simulator with default values.
        
        Attributes:
            rpm (int): Engine revolutions per minute
                - Starts at 800 RPM (typical idle speed)
            throttle (float): Throttle position percentage (0-100)
                - 0% = throttle closed (idle)
                - 100% = throttle fully open (maximum power)
            afr (float): Air-Fuel Ratio
                - 14.7 = Stoichiometric (ideal for normal driving)
                - 12.0-12.5 = Rich (used for maximum power)
            torque (float): Engine torque output in Newton-meters (Nm)
                - Higher torque = more pulling power
            is_stage1_tuned (bool): Whether Stage 1 ECU tuning is active
                - False = stock ECU calibration
                - True = tuned ECU with power/torque increase
        """
        self.rpm = 800  # Idle RPM - minimum speed to keep engine running
        self.throttle = 0  # 0-100%, where 0 is throttle closed
        self.afr = 14.7  # Stoichiometric air-fuel ratio (14.7:1 air to fuel)
        self.torque = 0  # Torque output in Newton-meters (Nm)
        self.is_stage1_tuned = False  # Whether Stage 1 tuning is active
    
    def toggle_tune(self):
        """
        Toggle Stage 1 ECU tuning on or off.
        
        Stage 1 tuning is a common ECU remap that:
        - Increases torque and power (typically 10-20% gain)
        - Adjusts air-fuel ratio for performance
        - Does not require hardware modifications
        - Is reversible (can be toggled back to stock)
        
        In real cars, this would be a permanent ECU flash, but in our simulator
        we allow toggling to compare tuned vs. stock performance in real-time.
        """
        self.is_stage1_tuned = not self.is_stage1_tuned
    
    def set_throttle(self, throttle_value):
        """
        Set the throttle position.
        
        Args:
            throttle_value (float): Throttle position percentage (0-100)
                - 0: Throttle closed, engine at idle
                - 50: Half throttle, moderate acceleration
                - 100: Full throttle (WOT - Wide Open Throttle)
        
        In real cars, the throttle is controlled by the accelerator pedal.
        The ECU reads throttle position and adjusts fuel injection, ignition timing,
        and other parameters accordingly.
        """
        # Clamp throttle to valid range (0-100%)
        if throttle_value < 0:
            self.throttle = 0
        elif throttle_value > 100:
            self.throttle = 100
        else:
            self.throttle = throttle_value
    
    def update(self):
        """
        Update the engine state for one simulation tick.
        
        This method simulates one "update cycle" of the ECU. In real cars,
        ECUs update thousands of times per second. This method:
        1. Calculates RPM based on throttle input
        2. Calculates torque based on RPM, throttle, and tuning status
        3. Adjusts Air-Fuel Ratio based on load and tuning status
        
        Called repeatedly in a loop (every 50ms) to create real-time simulation.
        """
        # ===== RPM LOGIC =====
        # When throttle is open, RPM increases
        # More throttle = faster RPM increase
        if self.throttle > 0:
            # Formula: RPM increases proportional to throttle position
            # throttle * 2 gives a smooth, realistic RPM response
            # In real engines, RPM response depends on engine size, turbo, etc.
            self.rpm += self.throttle * 2
            
            # Redline protection: Cap RPM at 7000
            # Exceeding redline can cause engine damage
            # Real redlines vary: 6000-8000+ RPM depending on engine type
            if self.rpm > 7000:
                self.rpm = 7000
        else:
            # When throttle is closed, RPM decays back to idle
            # This simulates engine braking and natural friction
            if self.rpm > 800:
                # Decay rate: decrease by 150 RPM each update
                # In reality, this depends on engine friction and load
                self.rpm -= 150
                if self.rpm < 800:
                    self.rpm = 800  # Don't go below idle
        
        # ===== TORQUE LOGIC =====
        # Torque is the rotational force the engine produces
        # Higher torque = better acceleration and pulling power
        
        # Base torque calculation:
        # Formula: base_torque = (RPM / 100) * (throttle / 100)
        # - RPM/100 scales RPM to a reasonable range
        # - throttle/100 scales throttle percentage to 0-1
        # - Multiplying gives us torque that increases with both RPM and throttle
        # 
        # In real engines, torque curves are more complex and vary by:
        # - Engine displacement (size)
        # - Turbo/supercharger boost
        # - Cam timing
        # - Intake/exhaust design
        base_torque = (self.rpm / 100) * (self.throttle / 100)
        
        # Stage 1 Tuning Effect:
        # When tuned, multiply torque by 1.15 (15% increase)
        # This is typical for Stage 1 ECU remaps on many turbocharged engines
        # The ECU remap adjusts:
        # - Ignition timing (spark advance)
        # - Boost pressure (if turbocharged)
        # - Fuel delivery
        # - Air-fuel ratio optimization
        if self.is_stage1_tuned:
            # 15% torque increase is a realistic Stage 1 gain
            # Some Stage 1 tunes can achieve 20-30% on certain engines
            self.torque = base_torque * 1.15
        else:
            # Stock (untuned) torque
            self.torque = base_torque
        
        # ===== AIR-FUEL RATIO (AFR) LOGIC =====
        # AFR determines the mixture of air to fuel entering the engine
        
        if self.throttle < 80:
            # Normal driving (throttle < 80%):
            # Use stoichiometric ratio (14.7:1)
            # This provides a good balance of power and efficiency
            # Most modern engines run at or near 14.7:1 for emissions and economy
            self.afr = 14.7
        else:
            # High load / full throttle (throttle >= 80%):
            # Use richer mixture (12.5:1)
            # Richer = more fuel relative to air
            # This prevents detonation (knock) and provides more power
            # Also helps cool the combustion chamber under high load
            self.afr = 12.5
        
        # Stage 1 Tuning AFR Adjustment:
        # When tuned AND at high throttle, run even richer (12.0:1)
        # This provides extra fuel for the increased power demand
        # Helps protect the engine from knock at higher boost/power levels
        if self.is_stage1_tuned and self.throttle >= 80:
            # Slightly richer mixture for tuned high-load operation
            # This is common in performance ECU maps
            self.afr = 12.0

