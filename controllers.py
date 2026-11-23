"""The controllers: each one decides the tap opening u (0 to 1)
from the current level h and the target level."""


def clamp(u):
    """A tap can only be between closed (0) and fully open (1)."""
    return min(max(u, 0.0), 1.0)


class Constant:
    """No control: the tap stays at the same opening (used in Step 1)."""

    def __init__(self, u):
        self.u = u

    def reset(self):
        pass

    def update(self, h, target, dt):
        return self.u


class OnOff:
    """Open fully below the target, close above it.

    With band > 0, the tap only changes outside target +/- band,
    and keeps its last position in between.
    """

    def __init__(self, band=0.0):
        self.band = band
        self.u = 1.0

    def reset(self):
        self.u = 1.0

    def update(self, h, target, dt):
        if h < target - self.band:
            self.u = 1.0
        elif h > target + self.band:
            self.u = 0.0
        return self.u


class P:
    """Proportional: the tap opens in proportion to the error."""

    def __init__(self, kp):
        self.kp = kp

    def reset(self):
        pass

    def update(self, h, target, dt):
        error = target - h
        return clamp(self.kp * error)


class PI:
    """Proportional + integral.

    With anti_windup=True, the integral only grows while the tap
    is not already stuck fully open or fully closed.
    """

    def __init__(self, kp, ki, anti_windup=True):
        self.kp = kp
        self.ki = ki
        self.anti_windup = anti_windup
        self.integral = 0.0

    def reset(self):
        self.integral = 0.0

    def update(self, h, target, dt):
        error = target - h
        new_integral = self.integral + error * dt
        u = self.kp * error + self.ki * new_integral

        if not self.anti_windup or 0.0 <= u <= 1.0:
            self.integral = new_integral

        return clamp(self.kp * error + self.ki * self.integral)
