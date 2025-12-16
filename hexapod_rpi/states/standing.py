"""
Standing State - Complete implementation
Smoothly transitions legs to standing position using Bezier curves
Port from Standing_State.ino
"""

from utils.vectors import Vector3
from utils.helpers import get_point_on_bezier_curve
import config


class StandingState:
    """
    Standing state - maintains stable standing position
    Smoothly transitions from any state to standing using Bezier curves
    """
    
    def __init__(self, kinematics, current_points):
        """
        Initialize standing state
        
        Args:
            kinematics: HexapodKinematics instance
            current_points: List of current leg positions
        """
        self.kinematics = kinematics
        self.current_points = current_points
        
        # Standing control points array [6 legs][10 points max]
        self.scpa = [[Vector3(0, 0, 0) for _ in range(10)] for _ in range(6)]
        
        # Standing transition points
        self.standing_start_points = [Vector3(0, 0, 0) for _ in range(6)]
        self.standing_in_between_points = [Vector3(0, 0, 0) for _ in range(6)]
        self.standing_end_point = Vector3(0, 0, 0)
        
        # Current legs being moved (3 at a time)
        self.current_legs = [-1, -1, -1]
        self.stand_loops = 0
        self.stand_progress = 0
        
        # Constants
        self.points = config.POINTS
        self.distance_from_center = config.DISTANCE_FROM_CENTER
        self.distance_from_ground = config.DISTANCE_FROM_GROUND_BASE
        
        # State tracking
        self.initialized = False
    
    def update(self, distance_from_ground, standing_distance_adjustment,
               from_state, move_all_at_once=False, high_lift=False):
        """
        Update standing state
        
        Args:
            distance_from_ground: Target height
            standing_distance_adjustment: Fine height adjustment
            from_state: Previous state (for transition logic)
            move_all_at_once: Move all legs simultaneously (vs 3 at a time)
            high_lift: Use extra high lift (for dramatic transitions)
        
        Returns:
            True if standing complete, False if still transitioning
        """
        self.distance_from_ground = distance_from_ground
        
        # Calculate end point
        self.standing_end_point = Vector3(
            self.distance_from_center,
            0,
            self.distance_from_ground + standing_distance_adjustment
        )
        
        # Initialize on first call or state change
        if not self.initialized:
            self.initialized = True
            self.stand_loops = 0
            self.stand_progress = 0
            
            # Determine transition mode based on previous state
            if from_state in [config.State.CALIBRATE, config.State.INITIALIZE,
                            config.State.SLAM_ATTACK, config.State.SLEEP,
                            config.State.ATTACH]:
                move_all_at_once = True
            
            if from_state in [config.State.SLAM_ATTACK, config.State.SLEEP]:
                high_lift = True
            
            # Select initial legs to move (if not moving all at once)
            if not move_all_at_once:
                self.set_3_highest_legs()
            
            # Store starting positions
            for i in range(6):
                self.standing_start_points[i] = self.current_points[i].copy()
            
            # Calculate intermediate and ending points
            for i in range(6):
                in_between_point = self.standing_start_points[i].copy()
                in_between_point.x = (in_between_point.x + self.standing_end_point.x) / 1.5
                in_between_point.y = (in_between_point.y + self.standing_end_point.y) / 1.5
                in_between_point.z = (in_between_point.z + self.standing_end_point.z) / 2
                
                # Add extra lift if close to ground or if high_lift requested
                if abs(in_between_point.z - self.standing_end_point.z) < 50:
                    in_between_point.z += 70
                if high_lift:
                    in_between_point.z += 80
                
                self.standing_in_between_points[i] = in_between_point
                
                # Set up Bezier curve control points
                self.scpa[i][0] = self.standing_start_points[i]
                self.scpa[i][1] = self.standing_in_between_points[i]
                self.scpa[i][2] = self.standing_end_point
        
        # Update end point constantly (allows height changes while standing)
        for i in range(6):
            self.scpa[i][2] = self.standing_end_point
        
        # Transition phase - moving legs to standing position
        if self.stand_loops < 2:
            self.stand_progress += 20
            
            t = self.stand_progress / self.points
            if t > 1:
                t = 1
            
            if move_all_at_once:
                # Move all 6 legs simultaneously
                for i in range(6):
                    pos = get_point_on_bezier_curve(self.scpa[i], 3, t)
                    self.kinematics.move_to_pos(i, pos)
                
                if self.stand_progress > self.points:
                    self.stand_progress = 0
                    self.stand_loops = 2  # Complete
            
            else:
                # Move 3 legs at a time (more stable)
                for i in range(3):
                    if self.current_legs[i] != -1:
                        pos = get_point_on_bezier_curve(
                            self.scpa[self.current_legs[i]], 3, t
                        )
                        self.kinematics.move_to_pos(self.current_legs[i], pos)
                
                if self.stand_progress > self.points:
                    self.stand_progress = 0
                    self.stand_loops += 1
                    if self.stand_loops < 2:
                        self.set_3_highest_legs()
        
        # Maintain standing position
        for i in range(6):
            pos = get_point_on_bezier_curve(self.scpa[i], 3, 1)
            self.kinematics.move_to_pos(i, pos)
        
        return self.stand_loops >= 2
    
    def set_3_highest_legs(self):
        """
        Select the 3 legs that are highest (furthest from ground)
        These will be moved next to avoid tipping over
        """
        self.current_legs = [-1, -1, -1]
        
        for j in range(3):
            for i in range(6):
                # Skip if leg is already in the list
                if i in self.current_legs:
                    continue
                
                # Skip if leg is already at target position
                if self.current_points[i].distance_to(self.standing_end_point) < 5:
                    continue
                
                # Select leg if it's higher than currently selected leg
                if (self.current_legs[j] == -1 or 
                    self.current_points[i].z > self.current_points[self.current_legs[j]].z):
                    self.current_legs[j] = i
    
    def reset(self):
        """Reset state for next transition"""
        self.initialized = False
        self.stand_loops = 0
        self.stand_progress = 0
