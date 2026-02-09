import argparse
import copy
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from life_sim.simulation import logic
from life_sim.simulation.state import SimState


def load_config():
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def collect_logs(sim_state):
    lines = [m for m, _ in sim_state.current_year_data.get("events", [])]
    for year in sim_state.history:
        lines.extend(m for m, _ in year.get("events", []))
    return lines


def run_once(base_cfg, seed, months, attendance):
    cfg = copy.deepcopy(base_cfg)
    cfg["agent"]["initial_age"] = 14
    school_cfg = cfg["education"]["schools"][cfg["education"]["active_school_id"]]
    school_cfg["academic_model"]["v2_enabled"] = True

    random.seed(seed)
    sim = SimState(cfg)
    for _ in range(months):
        if not sim.player.is_alive:
            break
        logic.process_turn(sim)
        if sim.player.school:
            sim.player.attendance_rate = attendance

    logs = collect_logs(sim)
    repeats = sum(1 for line in logs if "You must repeat the year" in line or "Attendance too low" in line)
    promotions = sum(1 for line in logs if line.startswith("Finished "))
    graduations = sum(1 for line in logs if "Graduated from" in line)

    subject_grades = []
    if sim.player.subjects:
        subject_grades = [float(s["current_grade"]) for s in sim.player.subjects.values()]

    return {
        "seed": seed,
        "alive": bool(sim.player.is_alive),
        "age": int(sim.player.age),
        "school_enrolled": bool(sim.player.school is not None),
        "repeats": repeats,
        "promotions": promotions,
        "graduations": graduations,
        "grade_mean": statistics.mean(subject_grades) if subject_grades else None,
        "grade_min": min(subject_grades) if subject_grades else None,
        "grade_max": max(subject_grades) if subject_grades else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 6 school balance report")
    parser.add_argument("--months", type=int, default=48, help="Months to simulate per seed")
    parser.add_argument("--attendance", type=float, default=0.9, help="Player attendance rate during enrollment")
    parser.add_argument("--seeds", type=int, nargs="+", default=[7101, 7102, 7103, 7104, 7105])
    args = parser.parse_args()

    cfg = load_config()
    runs = [run_once(cfg, seed, args.months, args.attendance) for seed in args.seeds]

    print("Phase 6 Balance Report")
    for row in runs:
        print(
            f"seed={row['seed']} age={row['age']} alive={row['alive']} "
            f"repeats={row['repeats']} promotions={row['promotions']} graduations={row['graduations']} "
            f"grade_mean={None if row['grade_mean'] is None else round(row['grade_mean'], 2)} "
            f"grade_range={None if row['grade_min'] is None else round(row['grade_min'], 2)}-"
            f"{None if row['grade_max'] is None else round(row['grade_max'], 2)}"
        )

    means = [r["grade_mean"] for r in runs if r["grade_mean"] is not None]
    if means:
        print(f"aggregate_grade_mean={round(statistics.mean(means), 2)}")
    print(f"aggregate_repeats={sum(r['repeats'] for r in runs)}")
    print(f"aggregate_graduations={sum(r['graduations'] for r in runs)}")


if __name__ == "__main__":
    main()
