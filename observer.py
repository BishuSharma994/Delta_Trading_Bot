# Observer bootstrap
# Delegates runtime execution to core.decision_loop.

import sys
import os
import fcntl
import logging
from pathlib import Path

from dotenv import load_dotenv

print("TRACE_TOP_OF_FILE")


_LOCK_FILE = open("/tmp/trading-bot.lock", "w")
fcntl.flock(_LOCK_FILE, fcntl.LOCK_EX)


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.append(str(PROJECT_ROOT.parent))
os.chdir(PROJECT_ROOT)


load_dotenv(PROJECT_ROOT / ".env")


logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logging.info("OBSERVER BOOTSTRAP OK")


from core.decision_loop import run_loop


def main():
    print("TRACE_MAIN_LOOP_START")
    logging.info("OBSERVER DELEGATING TO DECISION LOOP")
    run_loop()


if __name__ == "__main__":
    main()
