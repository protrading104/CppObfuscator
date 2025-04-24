import os
import shutil
import logging

class BackupManager:
    def __init__(self, backup_ext=".bak"):
        self.backup_ext = backup_ext
        self.logger = logging.getLogger("BackupManager")
        self._setup_logger()

    def _setup_logger(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

    def backup_file(self, file_path):
        backup_path = file_path + self.backup_ext
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"[🛡️] Резервная копия создана: {backup_path}")
        else:
            self.logger.info(f"[ℹ️] Копия уже существует: {backup_path}")

    def restore_file(self, file_path):
        backup_path = file_path + self.backup_ext
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            self.logger.info(f"[⏪] Восстановлен из резервной копии: {file_path}")
        else:
            self.logger.warning(f"[⚠️] Нет резервной копии: {file_path}")

    def restore_all(self, file_list):
        for file_path in file_list:
            self.restore_file(file_path)
