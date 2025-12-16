"""
Attacks State - Complete implementation
Animated attack sequences using Bezier curves
Port from Attacks.ino
"""

from utils.vectors import Vector2, Vector3
from utils.helpers import get_point_on_bezier_curve, map_float
import config
import time


class AttacksState:
    """
    Attack animations - slam attack and other offensive moves
    Uses Bezier curves for smooth, dramatic movements
    """
    
    def __init__(self, kinematics, current_points):
        """
        Initialize attacks state
        
        Args:
            kinematics: HexapodKinematics instance
            current_points: List of current leg positions
        """
        self.kinematics = kinematics
        self.current_points = current_points
        
        # Bezier control points buffer (max 5 points for curves)
        self.control_points = [Vector3(0, 0, 0) for _ in range(5)]
        
        # Store starting positions for attack animations
        self.cycle_start_points = [Vector3(0, 0, 0) for _ in range(6)]
        
        # Attack state tracking
        self.slam_started = False
        
        # Get stride and rotation multipliers from config
        self.stride_multiplier = config.STRIDE_MULTIPLIER
        self.rotation_multiplier = config.ROTATION_MULTIPLIER
        
        print("Attacks state initialized")
    
    def set_cycle_start_points(self):
        """Save current leg positions as starting points for animation"""
        for i in range(6):
            self.cycle_start_points[i] = Vector3(
                self.current_points[i].x,
                self.current_points[i].y,
                self.current_points[i].z
            )
    
    def slam_attack(self, attack_speed=25):
        """
        Execute slam attack animation
        
        Three phases:
        1. Foot placement - position legs for attack
        2. Leap - back legs lift, front legs raise high
        3. Slam - front legs slam down forcefully
        
        Args:
            attack_speed: Speed multiplier (20-100, default 25)
                         Lower = slower, more dramatic
                         Higher = faster, more aggressive
        
        Returns:
            True when attack complete
        """
        print(f"Executing slam attack (speed: {attack_speed})...")
        
        # Save starting positions
        self.set_cycle_start_points()
        self.slam_started = False
        
        # === PHASE 1: FOOT PLACEMENT ===
        # Position legs for optimal attack stance
        frames = int(attack_speed * 0.4)
        print(f"Phase 1: Foot placement ({frames} frames)")
        
        for i in range(frames):
            t = i / frames
            
            # Move all legs to placement positions
            for leg in range(6):
                point = self._get_foot_placement_path_point(leg, t)
                self.kinematics.move_to_pos(leg, point)
            
            time.sleep(0.01)  # Small delay for smooth animation
        
        # Update starting positions for next phase
        self.set_cycle_start_points()
        
        # === PHASE 2: LEAP AND RAISE ===
        # Back legs leap up, front legs raise high for slam
        frames = int(attack_speed * 1.2)
        print(f"Phase 2: Leap and raise ({frames} frames)")
        
        for i in range(frames):
            t = i / frames
            
            # Legs 0, 1, 4, 5 - leap backwards
            self.kinematics.move_to_pos(0, self._get_leap_path_point(0, t))
            self.kinematics.move_to_pos(1, self._get_leap_path_point(1, t))
            self.kinematics.move_to_pos(4, self._get_leap_path_point(4, t))
            self.kinematics.move_to_pos(5, self._get_leap_path_point(5, t))
            
            # Legs 2, 3 - raise high for slam
            self.kinematics.move_to_pos(2, self._get_slam_path_point(2, t))
            self.kinematics.move_to_pos(3, self._get_slam_path_point(3, t))
            
            # Trigger slam sound/effect at midpoint
            if t >= 0.5 and not self.slam_started:
                self.slam_started = True
                print("  SLAM!")
            
            time.sleep(0.01)
        
        # Brief pause at impact
        time.sleep(0.1)
        
        # Save final positions
        self.set_cycle_start_points()
        
        print("Slam attack complete!")
        return True
    
    def _get_foot_placement_path_point(self, leg, t):
        """
        Calculate foot placement path for attack stance
        
        Args:
            leg: Leg index (0-5)
            t: Progress along path (0.0 to 1.0)
        
        Returns:
            Vector3 position for this leg at time t
        """
        x_offset = 0
        y_offset = 0
        z_offset = 0
        
        # Leg-specific positioning for attack stance
        if leg == 1:
            z_offset = -60
            y_offset = -50
            x_offset = -70
        
        if leg == 4:
            z_offset = -50
            y_offset = -60
            x_offset = -70
        
        if leg == 0:
            x_offset = 40
        
        if leg == 5:
            x_offset = 40
        
        # Calculate target X position
        x = self.cycle_start_points[leg].x + x_offset
        
        # 2-point Bezier curve from current to placement position
        self.control_points[0] = self.cycle_start_points[leg]
        self.control_points[1] = Vector3(
            x,
            -50 * self.stride_multiplier[leg],
            -50 + z_offset
        ).rotate(55 * self.rotation_multiplier[leg], Vector2(x, 0))
        
        point = get_point_on_bezier_curve(self.control_points, 2, t)
        return point
    
    def _get_leap_path_point(self, leg, t):
        """
        Calculate leap path for back legs during attack
        
        Args:
            leg: Leg index (0, 1, 4, 5)
            t: Progress along path (0.0 to 1.0)
        
        Returns:
            Vector3 position for this leg at time t
        """
        x = self.cycle_start_points[leg].x
        
        # Start and end positions
        start = self.cycle_start_points[leg]
        end = Vector3(
            x - 20,
            self.cycle_start_points[leg].y + (160 * self.stride_multiplier[leg]),
            -80
        ).rotate(55 * self.rotation_multiplier[leg], Vector2(x, 0))
        
        # Middle control point - creates dramatic arc
        middle = ((start + end) * 0.5) + Vector3(0, 0, -300)
        
        # Front legs (0, 5) have higher arc
        if leg == 0 or leg == 5:
            middle.z += 180
        
        # 3-point Bezier curve for leap
        self.control_points[0] = start
        self.control_points[1] = middle
        self.control_points[2] = end
        
        point = get_point_on_bezier_curve(self.control_points, 3, t)
        return point
    
    def _get_slam_path_point(self, leg, t):
        """
        Calculate slam path for front attacking legs
        
        Three phases within the slam:
        1. Raise (0% - 70%): Lift leg high
        2. Slam (70% - 95%): Fast downward strike
        3. Land (95% - 100%): Hold final position
        
        Args:
            leg: Leg index (2, 3)
            t: Progress along path (0.0 to 1.0)
        
        Returns:
            Vector3 position for this leg at time t
        """
        slam_percentage = 0.70  # When to start slam
        land_percentage = 0.95  # When to finish slam
        
        # Phase 1: LEG RAISE (0% - 70%)
        if t < slam_percentage:
            # 3-point Bezier - smooth raise to high position
            self.control_points[0] = self.cycle_start_points[leg]
            self.control_points[1] = Vector3(200, 0, 200).rotate(
                -40 * self.rotation_multiplier[leg],
                Vector2(0, 0)
            )
            self.control_points[2] = Vector3(0, 0, 300).rotate(
                -35 * self.rotation_multiplier[leg],
                Vector2(0, 0)
            )
            
            # Map t from 0-0.7 to 0-1 for this phase
            phase_t = map_float(t, 0, slam_percentage, 0, 1)
            point = get_point_on_bezier_curve(self.control_points, 3, phase_t)
            return point
        
        # Phase 2: LEG SLAM (70% - 95%)
        if slam_percentage <= t < land_percentage:
            # 4-point Bezier - fast aggressive downward strike
            self.control_points[0] = Vector3(0, 0, 300).rotate(
                -35 * self.rotation_multiplier[leg],
                Vector2(0, 0)
            )
            self.control_points[1] = Vector3(300, 0, 300).rotate(
                -35 * self.rotation_multiplier[leg],
                Vector2(0, 0)
            )
            self.control_points[2] = Vector3(325, 0, 50).rotate(
                -35 * self.rotation_multiplier[leg],
                Vector2(0, 0)
            )
            self.control_points[3] = Vector3(250, 0, 0).rotate(
                -35 * self.rotation_multiplier[leg],
                Vector2(0, 0)
            )
            
            # Map t from 0.7-0.95 to 0-1 for this phase
            phase_t = map_float(t, slam_percentage, land_percentage, 0, 1)
            point = get_point_on_bezier_curve(self.control_points, 4, phase_t)
            return point
        
        # Phase 3: LAND (95% - 100%)
        if t >= land_percentage:
            # Hold final position
            return Vector3(250, 0, 0).rotate(
                -35 * self.rotation_multiplier[leg],
                Vector2(0, 0)
            )
    
    def quick_strike(self, target_leg=2):
        """
        Quick single-leg strike animation
        Simpler than full slam attack
        
        Args:
            target_leg: Which leg to strike with (default 2)
        """
        print(f"Quick strike with leg {target_leg}")
        
        self.set_cycle_start_points()
        
        frames = 20
        for i in range(frames):
            t = i / frames
            
            # Raise and slam with one leg
            if t < 0.5:
                # Raise phase
                height = t * 2 * 200  # Up to 200mm
                point = Vector3(
                    self.cycle_start_points[target_leg].x,
                    self.cycle_start_points[target_leg].y,
                    height
                )
            else:
                # Strike phase
                height = (1 - ((t - 0.5) * 2)) * 200
                point = Vector3(
                    self.cycle_start_points[target_leg].x + 50,
                    self.cycle_start_points[target_leg].y,
                    height
                )
            
            self.kinematics.move_to_pos(target_leg, point)
            time.sleep(0.02)
        
        print("Strike complete!")


# Test code
if __name__ == "__main__":
    """Test attacks state"""
    print("Testing Attacks State...")
    
    # Mock classes for testing
    class MockKinematics:
        def __init__(self):
            self.positions = [Vector3(200, 0, -100) for _ in range(6)]
        
        def move_to_pos(self, leg, pos):
            self.positions[leg] = pos
            # Print occasional updates (not every frame)
            if abs(pos.z) > 200 or abs(pos.z) < 10:
                print(f"  Leg {leg} -> x:{pos.x:.0f} y:{pos.y:.0f} z:{pos.z:.0f}")
    
    # Create mock instance
    mock_ik = MockKinematics()
    
    # Create attacks state
    attacks = AttacksState(mock_ik, mock_ik.positions)
    
    print("\n" + "="*60)
    print("SLAM ATTACK TEST")
    print("="*60)
    
    print("\nInitial positions:")
    for i in range(6):
        print(f"  Leg {i}: {mock_ik.positions[i]}")
    
    print("\nExecuting slam attack...")
    attacks.slam_attack(attack_speed=15)  # Slower for testing
    
    print("\nFinal positions:")
    for i in range(6):
        print(f"  Leg {i}: {mock_ik.positions[i]}")
    
    print("\n" + "="*60)
    print("QUICK STRIKE TEST")
    print("="*60)
    
    # Reset positions
    mock_ik.positions = [Vector3(200, 0, -100) for _ in range(6)]
    attacks = AttacksState(mock_ik, mock_ik.positions)
    
    attacks.quick_strike(target_leg=3)
    
    print("\nAttacks state test complete!")
