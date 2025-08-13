import logging

class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: f"[%(asctime)s] [%(process)d] {grey}[%(levelname)s]{reset} %(message)s",
        logging.INFO: f"[%(asctime)s] [%(process)d] {yellow}[%(levelname)s]{reset} %(message)s",
        logging.WARNING: f"[%(asctime)s] [%(process)d] {red}[%(levelname)s]{reset} %(message)s",
        logging.ERROR: f"[%(asctime)s] [%(process)d] {red}[%(levelname)s]{reset} %(message)s",
        logging.CRITICAL: f"[%(asctime)s] [%(process)d] {bold_red}[%(levelname)s]{reset} %(message)s"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
