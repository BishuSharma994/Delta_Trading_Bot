import argparse
import sys
from pathlib import Path


def _windows_commands(cwd: Path, python_exe: str) -> list[str]:
    return [
        f'schtasks /Create /TN "DeltaBot-DailyReport" /TR "cmd /c cd /d {cwd} && {python_exe} trade_stats.py --equity --save" /SC DAILY /ST 08:00 /F',
        f'schtasks /Create /TN "DeltaBot-WeeklyReport" /TR "cmd /c cd /d {cwd} && {python_exe} trade_stats.py --weekly" /SC WEEKLY /D MON /ST 07:00 /F',
        f'schtasks /Create /TN "DeltaBot-BrainRunner" /TR "cmd /c cd /d {cwd} && {python_exe} -m brain.runner --refresh" /SC WEEKLY /D SUN /ST 02:00 /F',
    ]


def _linux_entries(cwd: Path, python_exe: str) -> list[str]:
    return [
        "# Daily report - 08:00 UTC",
        f"0 8 * * * cd {cwd} && {python_exe} trade_stats.py --equity --save >> logs/scheduler.log 2>&1",
        "",
        "# Weekly report - Monday 07:00 UTC",
        f"0 7 * * 1 cd {cwd} && {python_exe} trade_stats.py --weekly >> logs/scheduler.log 2>&1",
        "",
        "# Brain runner - Sunday 02:00 UTC",
        f"0 2 * * 0 cd {cwd} && {python_exe} -m brain.runner --refresh >> logs/scheduler.log 2>&1",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Print scheduler setup commands for Phase 5 jobs.")
    parser.add_argument("--platform", choices=["windows", "linux"], help="Override platform detection")
    args = parser.parse_args()

    detected = "windows" if sys.platform.startswith("win") else "linux"
    platform_name = args.platform or detected
    cwd = Path.cwd()
    python_exe = sys.executable

    if platform_name == "windows":
        for line in _windows_commands(cwd, python_exe):
            print(line)
        return

    for line in _linux_entries(cwd, python_exe):
        print(line)
    print("")
    print("Run: crontab -e  and paste the lines above")


if __name__ == "__main__":
    main()
