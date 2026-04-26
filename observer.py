import logging
import os

LOG_PATH = "/root/Delta_Trading_Bot/Bot.log"
os.makedirs("/root/Delta_Trading_Bot", exist_ok=True)

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="a"),
        logging.StreamHandler(),
    ],
)

logging.info("LOGGING_INITIALIZED")

# Observer bootstrap
# Delegates runtime execution to core.decision_loop.

import sys
import fcntl
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger()
logger.info("TRACE_TOP_OF_FILE")


_LOCK_FILE = open("/tmp/trading-bot.lock", "w")
fcntl.flock(_LOCK_FILE, fcntl.LOCK_EX)


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.append(str(PROJECT_ROOT.parent))
os.chdir(PROJECT_ROOT)


load_dotenv(PROJECT_ROOT / ".env")


logger.info("OBSERVER_BOOTSTRAP_OK")


from core.decision_loop import run_loop


def main():
    logger.info("TRACE_MAIN_LOOP_START")
    logger.info("OBSERVER_DELEGATING_TO_DECISION_LOOP")
    for handler in logger.handlers:
        handler.flush()
    run_loop()


if __name__ == "__main__":
    main()
