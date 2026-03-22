import logging
import os
from pathlib import Path

def setup_uniform_logging(app_name: str, log_dir: str = None, test: bool = False):
    """Uniform format voor ALLE apps: 2026-01-31 10:15:03 [INFO]"""
    if log_dir is None:
        # Check if we are on Windows ('nt') or Linux ('posix')
        if os.name == 'nt':
            # On Windows, just make a 'logs' folder inside the current project directory
            log_dir = f"logs/{app_name}"
        else:
            # On Linux (morko), use the proper system log folder
            log_dir = f"/var/log/{app_name}"

    log_path = Path(log_dir) / "main.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # ✅ UNIFORM FORMAT: 2026-01-31 10:15:03,123 [INFO] message
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Clear existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if test else logging.INFO)

    logging.basicConfig(level=logging.INFO, handlers=[file_handler])

    logger = logging.getLogger(app_name)
    return logger
