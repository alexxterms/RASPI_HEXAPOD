"""
Vector classes for 2D and 3D calculations
Port from vectors.h in the original Arduino code
"""

import math


class Vector2:
    """2D Vector class for x, y coordinates"""
    
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
    
    def magnitude(self):
        """Calculate the magnitude (length) of the vector"""
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self):
        """Return a normalized version of this vector"""
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)
    
    def distance_to(self, other):
        """Calculate distance to another Vector2"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def __add__(self, other):
        """Vector addition"""
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        """Vector subtraction"""
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        """Scalar multiplication"""
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar):
        """Scalar division"""
        if scalar == 0:
            return Vector2(0, 0)
        return Vector2(self.x / scalar, self.y / scalar)
    
    def __str__(self):
        """String representation"""
        return f"Vector2({self.x:.2f}, {self.y:.2f})"
    
    def __repr__(self):
        return self.__str__()
    
    def copy(self):
        """Create a copy of this vector"""
        return Vector2(self.x, self.y)


class Vector3:
    """3D Vector class for x, y, z coordinates"""
    
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def magnitude(self):
        """Calculate the magnitude (length) of the vector"""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def normalize(self):
        """Return a normalized version of this vector"""
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / mag, self.y / mag, self.z / mag)
    
    def distance_to(self, other):
        """Calculate distance to another Vector3"""
        return math.sqrt(
            (self.x - other.x) ** 2 + 
            (self.y - other.y) ** 2 + 
            (self.z - other.z) ** 2
        )
    
    def dot(self, other):
        """Dot product with another Vector3"""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other):
        """Cross product with another Vector3"""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def __add__(self, other):
        """Vector addition"""
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        """Vector subtraction"""
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        """Scalar multiplication"""
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __truediv__(self, scalar):
        """Scalar division"""
        if scalar == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)
    
    def __str__(self):
        """String representation"""
        return f"Vector3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"
    
    def __repr__(self):
        return self.__str__()
    
    def to_string(self):
        """Alternative string format (matches Arduino toString())"""
        return f"({self.x:.1f}, {self.y:.1f}, {self.z:.1f})"
    
    def copy(self):
        """Create a copy of this vector"""
        return Vector3(self.x, self.y, self.z)


# Test code
if __name__ == "__main__":
    """Test vector classes"""
    print("Testing Vector2...")
    v2a = Vector2(3, 4)
    v2b = Vector2(1, 2)
    print(f"v2a: {v2a}")
    print(f"v2b: {v2b}")
    print(f"v2a magnitude: {v2a.magnitude()}")
    print(f"v2a + v2b: {v2a + v2b}")
    print(f"v2a - v2b: {v2a - v2b}")
    print(f"v2a * 2: {v2a * 2}")
    print(f"Distance: {v2a.distance_to(v2b)}")
    
    print("\nTesting Vector3...")
    v3a = Vector3(3, 4, 5)
    v3b = Vector3(1, 2, 3)
    print(f"v3a: {v3a}")
    print(f"v3b: {v3b}")
    print(f"v3a magnitude: {v3a.magnitude()}")
    print(f"v3a + v3b: {v3a + v3b}")
    print(f"v3a - v3b: {v3a - v3b}")
    print(f"v3a * 2: {v3a * 2}")
    print(f"Distance: {v3a.distance_to(v3b)}")
    print(f"Dot product: {v3a.dot(v3b)}")
    print(f"Cross product: {v3a.cross(v3b)}")
