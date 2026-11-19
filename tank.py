"""Model of the water tank.

The level h changes with the water coming in from the tap minus the water
going out through the hole at the bottom (Torricelli's law):

    dh/dt = (Q_MAX * u - K * sqrt(h)) / A

u is the tap opening, from 0 (closed) to 1 (fully open).
"""

import math

A = 0.5        # floor area of the tank (m^2)
Q_MAX = 0.002  # tap flow when fully open (m^3/s), i.e. 2 L/s
K = 0.002      # size of the drain hole
H_MAX = 1.2    # height of the tank (m)


def tank_step(h, u, dt, k=K):
    """Move the level forward by one time step (Euler's method)."""
    h = max(h, 0.0)
    dhdt = (Q_MAX * u - k * math.sqrt(h)) / A
    h = h + dhdt * dt
    # the level can't go below the bottom or above the top
    return min(max(h, 0.0), H_MAX)


def simulate(controller, target=0.5, t_end=2000, dt=0.5, h0=0.0,
             leak_time=None, leak_factor=1.2):
    """Run the tank with a controller.

    If leak_time is given, the drain hole gets bigger (K * leak_factor)
    from that time on, as if someone opened a second valve.
    Returns three lists: times, levels and tap openings.
    """
    times = []
    levels = []
    taps = []

    controller.reset()
    h = h0
    n_steps = int(t_end / dt)

    for i in range(n_steps):
        t = i * dt
        u = controller.update(h, target, dt)

        if leak_time is not None and t >= leak_time:
            k = K * leak_factor
        else:
            k = K

        times.append(t)
        levels.append(h)
        taps.append(u)

        h = tank_step(h, u, dt, k)

    return times, levels, taps
