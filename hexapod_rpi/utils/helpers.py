"""
Helper functions for hexapod control
Port from Helpers.h and Bezier.ino in the original Arduino code
"""

import math
import time
from utils.vectors import Vector2, Vector3


def lerp(a, b, f):
    """
    Linear interpolation between two values
    
    Args:
        a: Start value (can be float, Vector2, or Vector3)
        b: End value (can be float, Vector2, or Vector3)
        f: Interpolation factor (0.0 to 1.0)
    
    Returns:
        Interpolated value of same type as inputs
    """
    if isinstance(a, Vector2) and isinstance(b, Vector2):
        return Vector2(
            lerp(a.x, b.x, f),
            lerp(a.y, b.y, f)
        )
    elif isinstance(a, Vector3) and isinstance(b, Vector3):
        return Vector3(
            lerp(a.x, b.x, f),
            lerp(a.y, b.y, f),
            lerp(a.z, b.z, f)
        )
    else:
        # Scalar lerp
        return a * (1.0 - f) + (b * f)


def calculate_hypotenuse(x, y):
    """
    Calculate hypotenuse of a right triangle
    
    Args:
        x: First side length
        y: Second side length
    
    Returns:
        Hypotenuse length
    """
    return math.sqrt(x ** 2 + y ** 2)


def map_float(x, in_min, in_max, out_min, out_max):
    """
    Map a value from one range to another (like Arduino's map function)
    
    Args:
        x: Input value
        in_min: Input range minimum
        in_max: Input range maximum
        out_min: Output range minimum
        out_max: Output range maximum
    
    Returns:
        Mapped value
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def constrain(value, min_val, max_val):
    """
    Constrain a value between min and max
    
    Args:
        value: Value to constrain
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Constrained value
    """
    return max(min_val, min(max_val, value))


def binomial_coefficient(n, k):
    """
    Calculate binomial coefficient (n choose k)
    Used in Bezier curve calculations
    
    Args:
        n: Total number of items
        k: Number of items to choose
    
    Returns:
        Binomial coefficient
    """
    result = 1
    
    # Calculate using formula: n! / (k! * (n-k)!)
    for i in range(1, k + 1):
        result *= (n - (k - i))
        result //= i
    
    return result


def get_point_on_bezier_curve(points, num_points, t):
    """
    Calculate a point on a Bezier curve
    Supports both Vector2 and Vector3 point arrays
    
    Args:
        points: List of control points (Vector2 or Vector3)
        num_points: Number of control points
        t: Parameter along curve (0.0 to 1.0)
    
    Returns:
        Point on Bezier curve (Vector2 or Vector3)
    """
    if len(points) == 0:
        return Vector3(0, 0, 0) if isinstance(points[0], Vector3) else Vector2(0, 0)
    
    # Determine if we're working with Vector2 or Vector3
    is_vector3 = isinstance(points[0], Vector3)
    
    # Initialize result
    if is_vector3:
        pos = Vector3(0, 0, 0)
    else:
        pos = Vector2(0, 0)
    
    # Calculate Bezier curve point using Bernstein polynomial
    for i in range(num_points):
        b = binomial_coefficient(num_points - 1, i) * \
            pow(1 - t, num_points - 1 - i) * \
            pow(t, i)
        
        pos.x += b * points[i].x
        pos.y += b * points[i].y
        
        if is_vector3:
            pos.z += b * points[i].z
    
    return pos


class Timer:
    """
    Simple timer class to replace Arduino's millis() based timing
    """
    
    _start_time = None
    
    @classmethod
    def init(cls):
        """Initialize the timer (call once at program start)"""
        cls._start_time = time.time()
    
    @classmethod
    def millis(cls):
        """
        Get milliseconds since timer initialization
        
        Returns:
            Milliseconds as integer
        """
        if cls._start_time is None:
            cls.init()
        return int((time.time() - cls._start_time) * 1000)
    
    @classmethod
    def micros(cls):
        """
        Get microseconds since timer initialization
        
        Returns:
            Microseconds as integer
        """
        if cls._start_time is None:
            cls.init()
        return int((time.time() - cls._start_time) * 1000000)


class EveryTimer:
    """
    Helper class to execute code at regular intervals
    Replaces the Arduino 'every()' macro
    """
    
    def __init__(self, interval_ms):
        """
        Initialize timer
        
        Args:
            interval_ms: Interval in milliseconds
        """
        self.interval_ms = interval_ms
        self.last_time = Timer.millis()
    
    def check(self):
        """
        Check if interval has elapsed
        
        Returns:
            True if interval has elapsed, False otherwise
        """
        current_time = Timer.millis()
        if current_time - self.last_time >= self.interval_ms:
            self.last_time = current_time
            return True
        return False


def angle_to_microseconds(angle):
    """
    Convert servo angle (0-180°) to microseconds (500-2500μs)
    
    Args:
        angle: Angle in degrees (0-180)
    
    Returns:
        Pulse width in microseconds
    """
    # Clamp angle
    angle = constrain(angle, 0, 180)
    
    # Linear mapping
    return int(500 + (angle / 180.0) * 2000)


def microseconds_to_angle(microseconds):
    """
    Convert microseconds (500-2500μs) to servo angle (0-180°)
    
    Args:
        microseconds: Pulse width in microseconds
    
    Returns:
        Angle in degrees
    """
    # Clamp microseconds
    microseconds = constrain(microseconds, 500, 2500)
    
    # Linear mapping
    return ((microseconds - 500) / 2000.0) * 180


# Test code
if __name__ == "__main__":
    """Test helper functions"""
    print("Testing helper functions...")
    
    # Test lerp
    print(f"\nLerp test:")
    print(f"lerp(0, 10, 0.5) = {lerp(0, 10, 0.5)}")
    v1 = Vector3(0, 0, 0)
    v2 = Vector3(10, 10, 10)
    print(f"lerp({v1}, {v2}, 0.5) = {lerp(v1, v2, 0.5)}")
    
    # Test map_float
    print(f"\nMap test:")
    print(f"map_float(5, 0, 10, 0, 100) = {map_float(5, 0, 10, 0, 100)}")
    
    # Test Bezier curve
    print(f"\nBezier curve test:")
    control_points = [
        Vector3(0, 0, 0),
        Vector3(50, 0, 50),
        Vector3(100, 0, 0)
    ]
    
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        point = get_point_on_bezier_curve(control_points, 3, t)
        print(f"t={t}: {point}")
    
    # Test timer
    print(f"\nTimer test:")
    Timer.init()
    print(f"Current time: {Timer.millis()} ms")
    time.sleep(0.1)
    print(f"After 100ms sleep: {Timer.millis()} ms")
    
    # Test EveryTimer
    print(f"\nEveryTimer test (500ms intervals):")
    timer = EveryTimer(500)
    for i in range(10):
        if timer.check():
            print(f"Tick at {Timer.millis()} ms")
        time.sleep(0.1)
