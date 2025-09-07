import logging
import os

class HistoryLogger:
    def __init__(self, log_folder='log', log_file='history.log'):
        self.log_folder = log_folder
        self.log_file = log_file
        os.makedirs(self.log_folder, exist_ok=True)
        self.full_path = os.path.join(self.log_folder, self.log_file)

        # Use a module-level logger to prevent duplicate handlers
        self.logger = logging.getLogger('BankHistoryLogger')
        self.logger.setLevel(logging.INFO)
        # Only add handler once for each unique log file
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == self.full_path for h in self.logger.handlers):
            handler = logging.FileHandler(self.full_path, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log(self, message):
        self.logger.info(message)