import os
from PyQt5.QtCore import QThread, pyqtSignal

class DataProcessor(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parser, found_files):
        super().__init__()
        self.parser = parser
        self.found_files = found_files

    def run(self):
        self.progress.emit("Начинаем обработку файлов...")
        processed = 0
        for file_path in self.found_files:
            try:
                if self.parser.parse_file(file_path):
                    processed += 1
                    self.progress.emit(f"Обработан файл: {os.path.basename(file_path)}")
                else:
                    self.progress.emit(f"Ошибка при обработке файла: {os.path.basename(file_path)}")
            except Exception as e:
                self.progress.emit(f"Исключение при обработке {os.path.basename(file_path)}: {str(e)}")

        self.progress.emit(f"Обработка завершена. Успешно обработано файлов: {processed}/{len(self.found_files)}")
        self.finished.emit()
