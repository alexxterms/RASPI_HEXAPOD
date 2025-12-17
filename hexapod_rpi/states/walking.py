"""
Walking/Car State - Complete gait implementation
Includes all 6 gaits: TRI, RIPPLE, WAVE, QUAD, BI, HOP
Port from Car_State.ino
"""

import math
from utils.vectors import Vector2, Vector3
from utils.helpers import lerp, get_point_on_bezier_curve, map_float, constrain
import config


class WalkingState:
    """
    Complete walking state with all gait patterns
    Handles forward/backward movement, rotation, and strafing
    """
    
    def __init__(self, kinematics, current_points):
        """
        Initialize walking state
        
        Args:
            kinematics: HexapodKinematics instance
            current_points: List of current leg positions
        """
        self.kinematics = kinematics
        self.current_points = current_points
        
        # Movement parameters
        self.forward_amount = 0.0
        self.turn_amount = 0.0
        
        # Timing arrays
        self.t_array = [0.0] * 6
        self.cycle_progress = [0.0] * 6
        self.cycle_start_points = [Vector3(0, 0, 0) for _ in range(6)]
        self.leg_states = [config.LegState.RESET] * 6
        
        # Control points for Bezier curves
        self.control_points = [Vector3(0, 0, 0) for _ in range(10)]
        self.rotate_control_points = [Vector3(0, 0, 0) for _ in range(10)]
        self.control_points_amount = 0
        self.rotate_control_points_amount = 0
        
        # Gait parameters (changed per gait)
        self.push_fraction = 3.0 / 6.0
        self.speed_multiplier = 0.5
        self.stride_length_multiplier = 1.5
        self.lift_height_multiplier = 1.0
        self.max_stride_length = 200.0
        self.max_speed = 100.0
        
        # Fixed parameters
        self.leg_placement_angle = 56.0  # degrees
        
        # Global multipliers (from slider)
        self.global_speed_multiplier = 0.55
        self.global_rotation_multiplier = 0.55
        
        # Constants from config
        self.points = config.POINTS
        self.distance_from_center = config.DISTANCE_FROM_CENTER
        self.distance_from_ground = config.DISTANCE_FROM_GROUND_BASE
        self.lift_height = config.LIFT_HEIGHT
        self.land_height = config.LAND_HEIGHT
        self.stride_overshoot = config.STRIDE_OVERSHOOT
        self.stride_multiplier = config.STRIDE_MULTIPLIER
        self.rotation_multiplier = config.ROTATION_MULTIPLIER
        
        # Dynamic stride length flag
        self.dynamic_stride_length = True
        
        # Previous gait (for transitions)
        self.previous_gait = None
        self.current_gait = config.Gait.TRI
    
    def set_gait(self, gait):
        """
        Set current gait and initialize parameters
        
        Args:
            gait: Gait type from config.Gait
        """
        self.previous_gait = self.current_gait
        self.current_gait = gait
        
        # Initialize leg states on gait change
        if self.previous_gait != self.current_gait:
            for i in range(6):
                self.leg_states[i] = config.LegState.RESET
        
        # Configure gait-specific parameters
        if gait == config.Gait.TRI:
            # Tripod gait - fast, stable
            self.cycle_progress[0] = 0
            self.cycle_progress[1] = self.points / 2
            self.cycle_progress[2] = 0
            self.cycle_progress[3] = self.points / 2
            self.cycle_progress[4] = 0
            self.cycle_progress[5] = self.points / 2
            
            self.push_fraction = 3.1 / 6.0
            self.speed_multiplier = 1.0
            self.stride_length_multiplier = 1.2
            self.lift_height_multiplier = 1.1
            self.max_stride_length = 240.0
            self.max_speed = 200.0
        
        elif gait == config.Gait.WAVE:
            # Wave gait - slow, stable
            self.cycle_progress[0] = 0
            self.cycle_progress[1] = (self.points / 6)
            self.cycle_progress[2] = (self.points / 6) * 2
            self.cycle_progress[3] = (self.points / 6) * 5
            self.cycle_progress[4] = (self.points / 6) * 4
            self.cycle_progress[5] = (self.points / 6) * 3
            
            self.push_fraction = 4.9 / 6.0
            self.speed_multiplier = 0.40
            self.stride_length_multiplier = 2.0
            self.lift_height_multiplier = 1.2
            self.max_stride_length = 150.0
            self.max_speed = 160.0
        
        elif gait == config.Gait.RIPPLE:
            # Ripple gait - medium speed, good stability
            self.cycle_progress[0] = 0
            self.cycle_progress[1] = (self.points / 6) * 4
            self.cycle_progress[2] = (self.points / 6) * 2
            self.cycle_progress[3] = (self.points / 6) * 5
            self.cycle_progress[4] = (self.points / 6)
            self.cycle_progress[5] = (self.points / 6) * 3
            
            self.push_fraction = 3.2 / 6.0
            self.speed_multiplier = 1.0
            self.stride_length_multiplier = 1.3
            self.lift_height_multiplier = 1.1
            self.max_stride_length = 220.0
            self.max_speed = 200.0
        
        elif gait == config.Gait.BI:
            # Bipod gait
            self.cycle_progress[0] = 0
            self.cycle_progress[1] = (self.points / 3)
            self.cycle_progress[2] = (self.points / 3) * 2
            self.cycle_progress[3] = 0
            self.cycle_progress[4] = (self.points / 3)
            self.cycle_progress[5] = (self.points / 3) * 2
            
            self.push_fraction = 2.1 / 6.0
            self.speed_multiplier = 4.0
            self.stride_length_multiplier = 1.0
            self.lift_height_multiplier = 1.8
            self.max_stride_length = 230.0
            self.max_speed = 130.0
        
        elif gait == config.Gait.QUAD:
            # Quadruped gait
            self.cycle_progress[0] = 0
            self.cycle_progress[1] = (self.points / 3)
            self.cycle_progress[2] = (self.points / 3) * 2
            self.cycle_progress[3] = 0
            self.cycle_progress[4] = (self.points / 3)
            self.cycle_progress[5] = (self.points / 3) * 2
            
            self.push_fraction = 4.1 / 6.0
            self.speed_multiplier = 1.0
            self.stride_length_multiplier = 1.2
            self.lift_height_multiplier = 1.1
            self.max_stride_length = 220.0
            self.max_speed = 200.0
        
        elif gait == config.Gait.HOP:
            # Hop gait - all legs together
            self.cycle_progress[0] = 0
            self.cycle_progress[1] = 0
            self.cycle_progress[2] = 0
            self.cycle_progress[3] = 0
            self.cycle_progress[4] = 0
            self.cycle_progress[5] = 0
            
            self.push_fraction = 3.0 / 6.0
            self.speed_multiplier = 1.0
            self.stride_length_multiplier = 1.6
            self.lift_height_multiplier = 2.5
            self.max_stride_length = 240.0
            self.max_speed = 200.0
    
    def update(self, joy1_current, joy2_current, slider1, distance_from_ground):
        """
        Update walking state
        
        Args:
            joy1_current: Vector2 for forward/strafe movement
            joy2_current: Vector2 for rotation/height
            slider1: Speed slider (0-100)
            distance_from_ground: Current height
        """
        # Update global parameters
        self.global_speed_multiplier = (slider1 + 10.0) * 0.01
        self.global_rotation_multiplier = map_float(slider1, 0, 100, 40, 130) * 0.01
        self.distance_from_ground = distance_from_ground
        
        # Calculate t values for each leg
        for i in range(6):
            self.t_array[i] = self.cycle_progress[i] / self.points
        
        # Set movement amounts
        self.forward_amount = joy1_current.magnitude()
        self.turn_amount = joy2_current.x
        
        # Debug: Check if we're getting movement commands
        if config.DEBUG_MODE and (abs(self.forward_amount) > 0.01 or abs(self.turn_amount) > 0.01):
            print(f"  WalkingState: fwd={self.forward_amount:.2f}, turn={self.turn_amount:.2f}, " +
                  f"speed_mult={self.global_speed_multiplier:.2f}")
        
        # Move all legs to their gait positions
        for leg in range(6):
            pos = self.get_gait_point(leg, self.push_fraction, joy1_current, joy2_current)
            if config.DEBUG_MODE and leg == 0:  # Only print leg 0 to avoid spam
                print(f"    Leg 0 pos: {pos}")
            self.kinematics.move_to_pos(leg, pos)
        
        # Update cycle progress
        # Scale up the movement amount to get reasonable walking speed
        # Target: complete cycle in ~1-2 seconds (50-100 frames) = 10-20 points/frame
        progress_change = (max(abs(self.forward_amount), abs(self.turn_amount)) * 
                          self.speed_multiplier * 20.0) * self.global_speed_multiplier
        progress_change = constrain(progress_change, 0, 
                                   self.max_speed * self.global_speed_multiplier)
        
        if config.DEBUG_MODE:
            print(f"    Progress change: {progress_change:.2f}, BEFORE cycle[0]={self.cycle_progress[0]:.1f}/{self.points}")
        
        for i in range(6):
            self.cycle_progress[i] += progress_change
            if self.cycle_progress[i] >= self.points:
                self.cycle_progress[i] = self.cycle_progress[i] - self.points
        
        if config.DEBUG_MODE:
            print(f"    AFTER cycle[0]={self.cycle_progress[0]:.1f}, should have increased by {progress_change:.2f}")
    
    def get_gait_point(self, leg, push_fraction, joy1_current, joy2_current):
        """
        Calculate target position for a leg based on gait cycle
        
        Args:
            leg: Leg index (0-5)
            push_fraction: Fraction of cycle spent pushing
            joy1_current: Forward/strafe vector
            joy2_current: Rotation vector
        
        Returns:
            Vector3 target position for the leg
        """
        rotate_stride_length = joy2_current.x * self.global_rotation_multiplier
        v = joy1_current.copy()
        
        # Handle dynamic vs fixed stride length
        if not self.dynamic_stride_length:
            v = v.normalize()
            v = v * 70
        
        # Apply stride length multiplier to y component only
        v = Vector2(v.x, v.y * self.stride_length_multiplier)
        v.y = constrain(v.y, -self.max_stride_length / 2, self.max_stride_length / 2)
        v = v * self.global_speed_multiplier
        
        if not self.dynamic_stride_length:
            rotate_stride_length = -70 if rotate_stride_length < 0 else 70
        
        weight_sum = abs(self.forward_amount) + abs(self.turn_amount)
        if weight_sum == 0:
            weight_sum = 1.0  # Prevent division by zero
        
        t = self.t_array[leg]
        
        # PROPELLING PHASE (leg on ground pushing)
        if t < push_fraction:
            if self.leg_states[leg] != config.LegState.PROPELLING:
                self.set_cycle_start_point(leg)
            self.leg_states[leg] = config.LegState.PROPELLING
            
            # Straight movement control points
            self.control_points[0] = self.cycle_start_points[leg]
            target_point = Vector3(
                v.x * self.stride_multiplier[leg] + self.distance_from_center,
                -v.y * self.stride_multiplier[leg],
                self.distance_from_ground
            )
            # Rotate around leg placement point
            self.control_points[1] = self.rotate_point(
                target_point,
                self.leg_placement_angle * self.rotation_multiplier[leg],
                Vector2(self.distance_from_center, 0)
            )
            self.control_points_amount = 2
            straight_point = get_point_on_bezier_curve(
                self.control_points, self.control_points_amount,
                map_float(t, 0, push_fraction, 0, 1)
            )
            
            # Rotation control points
            self.rotate_control_points[0] = self.cycle_start_points[leg]
            self.rotate_control_points[1] = Vector3(
                self.distance_from_center + 40, 0, self.distance_from_ground
            )
            self.rotate_control_points[2] = Vector3(
                self.distance_from_center, rotate_stride_length, self.distance_from_ground
            )
            self.rotate_control_points_amount = 3
            rotate_point = get_point_on_bezier_curve(
                self.rotate_control_points, self.rotate_control_points_amount,
                map_float(t, 0, push_fraction, 0, 1)
            )
            
            # Blend straight and rotation movements
            return (straight_point * abs(self.forward_amount) + 
                   rotate_point * abs(self.turn_amount)) / weight_sum
        
        # LIFTING PHASE (leg in air moving forward)
        else:
            if self.leg_states[leg] != config.LegState.LIFTING:
                self.set_cycle_start_point(leg)
            self.leg_states[leg] = config.LegState.LIFTING
            
            # Straight movement control points (4-point Bezier)
            self.control_points[0] = self.cycle_start_points[leg]
            self.control_points[1] = self.cycle_start_points[leg] + Vector3(
                0, 0, self.lift_height * self.lift_height_multiplier
            )
            
            mid_point = Vector3(
                -v.x * self.stride_multiplier[leg] + self.distance_from_center,
                (v.y + self.stride_overshoot) * self.stride_multiplier[leg],
                self.distance_from_ground + self.land_height
            )
            self.control_points[2] = self.rotate_point(
                mid_point,
                self.leg_placement_angle * self.rotation_multiplier[leg],
                Vector2(self.distance_from_center, 0)
            )
            
            end_point = Vector3(
                -v.x * self.stride_multiplier[leg] + self.distance_from_center,
                v.y * self.stride_multiplier[leg],
                self.distance_from_ground
            )
            self.control_points[3] = self.rotate_point(
                end_point,
                self.leg_placement_angle * self.rotation_multiplier[leg],
                Vector2(self.distance_from_center, 0)
            )
            self.control_points_amount = 4
            straight_point = get_point_on_bezier_curve(
                self.control_points, self.control_points_amount,
                map_float(t, push_fraction, 1, 0, 1)
            )
            
            # Rotation control points (5-point Bezier)
            self.rotate_control_points[0] = self.cycle_start_points[leg]
            self.rotate_control_points[1] = self.cycle_start_points[leg] + Vector3(
                0, 0, self.lift_height * self.lift_height_multiplier
            )
            self.rotate_control_points[2] = Vector3(
                self.distance_from_center + 40, 0,
                self.distance_from_ground + self.lift_height * self.lift_height_multiplier
            )
            self.rotate_control_points[3] = Vector3(
                self.distance_from_center,
                -(rotate_stride_length + self.stride_overshoot),
                self.distance_from_ground + self.land_height
            )
            self.rotate_control_points[4] = Vector3(
                self.distance_from_center, -rotate_stride_length, self.distance_from_ground
            )
            self.rotate_control_points_amount = 5
            rotate_point = get_point_on_bezier_curve(
                self.rotate_control_points, self.rotate_control_points_amount,
                map_float(t, push_fraction, 1, 0, 1)
            )
            
            # Blend straight and rotation movements
            return (straight_point * abs(self.forward_amount) + 
                   rotate_point * abs(self.turn_amount)) / weight_sum
    
    def rotate_point(self, point, angle_deg, pivot):
        """
        Rotate a point around a pivot in the XY plane
        
        Args:
            point: Vector3 to rotate
            angle_deg: Rotation angle in degrees
            pivot: Vector2 pivot point
        
        Returns:
            Rotated Vector3
        """
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Translate to origin
        x = point.x - pivot.x
        y = point.y - pivot.y
        
        # Rotate
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        
        # Translate back
        return Vector3(new_x + pivot.x, new_y + pivot.y, point.z)
    
    def set_cycle_start_point(self, leg):
        """Set the cycle start point for a leg"""
        self.cycle_start_points[leg] = self.current_points[leg].copy()
    
    def set_cycle_start_points_all(self):
        """Set cycle start points for all legs"""
        for i in range(6):
            self.cycle_start_points[i] = self.current_points[i].copy()
    
    def reset(self):
        """
        Reset walking state for next transition
        Resets all timing and state tracking variables
        """
        # Reset timing arrays
        self.t_array = [0.0] * 6
        self.cycle_progress = [0.0] * 6
        self.leg_states = [config.LegState.RESET] * 6
        
        # Reset cycle start points
        self.set_cycle_start_points_all()
        
        # Reset movement parameters
        self.forward_amount = 0.0
        self.turn_amount = 0.0
