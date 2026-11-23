"""Runs every test from the project and saves the graphs in figures/
and the comparison table in results.md."""

import matplotlib
matplotlib.use("Agg")  # save to files, no window
import matplotlib.pyplot as plt

from tank import simulate
from controllers import Constant, OnOff, P, PI

TARGET = 0.5
LEAK_TIME = 1000


def finish(ax, title):
    ax.set_title(title)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("level (m)")
    ax.grid(True, alpha=0.3)
    ax.legend()


def save(fig, name):
    fig.tight_layout()
    fig.savefig("figures/" + name, dpi=150)
    plt.close(fig)
    print("saved figures/" + name)


def fig1_open_loop():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    t, h, _ = simulate(Constant(1.0), t_end=4000, dt=0.5)
    ax.plot(t, h, label="tap fully open, dt = 0.5 s")
    t, h, _ = simulate(Constant(1.0), t_end=4000, dt=0.1)
    ax.plot(t, h, "--", label="tap fully open, dt = 0.1 s")
    t, h, _ = simulate(Constant(0.0), t_end=4000, h0=1.0)
    ax.plot(t, h, label="tap closed, starting at 1.0 m")
    finish(ax, "Step 1: the tank on its own")
    save(fig, "1_open_loop.png")


def level_and_tap(cases, title, name, t_end=1000):
    """Two graphs one above the other: the level and the tap."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    for label, controller, kwargs in cases:
        t, h, u = simulate(controller, TARGET, t_end=t_end, **kwargs)
        ax1.plot(t, h, label=label)
        ax2.plot(t, u, label=label, linewidth=0.8)
    ax1.axhline(TARGET, color="gray", linestyle=":", label="target")
    finish(ax1, title)
    ax1.set_xlabel("")
    ax2.set_xlabel("time (s)")
    ax2.set_ylabel("tap opening (0 to 1)")
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    save(fig, name)


def levels_only(cases, title, name, t_end=1000, leak=False):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, controller in cases:
        leak_time = LEAK_TIME if leak else None
        t, h, _ = simulate(controller, TARGET, t_end=t_end, leak_time=leak_time)
        ax.plot(t, h, label=label)
    ax.axhline(TARGET, color="gray", linestyle=":", label="target")
    if leak:
        ax.axvline(LEAK_TIME, color="red", linestyle="--", alpha=0.5,
                   label="second drain opens")
    finish(ax, title)
    save(fig, name)


def measure(controller):
    """The numbers for the comparison table."""
    dt = 0.5
    t, h, u = simulate(controller, TARGET, t_end=2000, dt=dt,
                       leak_time=LEAK_TIME)
    before = int(LEAK_TIME / dt)  # index of t = 1000 s

    # time after which the level stays within 2 cm of the target
    settle = None
    for i in range(before):
        if all(abs(x - TARGET) < 0.02 for x in h[i:before]):
            settle = t[i]
            break

    # count how many times the tap went from open to closed or back
    switches = 0
    for i in range(1, len(u)):
        if abs(u[i] - u[i - 1]) > 0.5:
            switches += 1

    return {
        "final": h[before - 1],
        "highest": max(h[:before]),
        "settle": settle,
        "switches": switches,
        "after_leak": h[-1],
    }


def results_table():
    rows = [
        ("On/off", OnOff(0.0)),
        ("On/off with 2 cm band", OnOff(0.02)),
        ("P (Kp = 5)", P(5)),
        ("P (Kp = 20)", P(20)),
        ("PI (Kp = 5, Ki = 0.05)", PI(5, 0.05)),
    ]
    lines = [
        "| Controller | Level at 1000 s (m) | Highest level (m) "
        "| Time to stay within 2 cm (s) | Tap switches "
        "| Level at 2000 s, after the leak (m) |",
        "|---|---|---|---|---|---|",
    ]
    for name, controller in rows:
        r = measure(controller)
        settle = "never" if r["settle"] is None else f"{r['settle']:.0f}"
        lines.append(
            f"| {name} | {r['final']:.3f} | {r['highest']:.3f} | {settle} "
            f"| {r['switches']} | {r['after_leak']:.3f} |"
        )
    table = "\n".join(lines)
    with open("results.md", "w") as f:
        f.write("# Results (made by run.py)\n\n" + table + "\n")
    print(table)


if __name__ == "__main__":
    fig1_open_loop()
    level_and_tap(
        [("no band", OnOff(0.0), {}),
         ("2 cm band", OnOff(0.02), {})],
        "Step 2: on/off control", "2_on_off.png")
    levels_only(
        [("Kp = 1", P(1)), ("Kp = 5", P(5)), ("Kp = 20", P(20))],
        "Step 3: P control never reaches the target", "3_p_control.png")
    levels_only(
        [("Ki = 0.005", PI(5, 0.005)), ("Ki = 0.014", PI(5, 0.014)),
         ("Ki = 0.05", PI(5, 0.05))],
        "Step 4: PI control (Kp = 5)", "4_pi_control.png")
    level_and_tap(
        [("without anti-windup", PI(5, 0.05, anti_windup=False), {}),
         ("with anti-windup", PI(5, 0.05, anti_windup=True), {})],
        "Step 4: integral windup", "5_windup.png")
    levels_only(
        [("on/off, 2 cm band", OnOff(0.02)), ("P (Kp = 5)", P(5)),
         ("PI (Kp = 5, Ki = 0.05)", PI(5, 0.05))],
        "Step 5: a second drain opens at t = 1000 s",
        "6_disturbance.png", t_end=2000, leak=True)
    results_table()
