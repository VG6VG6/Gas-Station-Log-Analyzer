import os

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QListWidget, QLineEdit, QPushButton,
                           QLabel, QComboBox,
                           QFileDialog, QMessageBox,
                           QDateEdit)
from PyQt5.QtCore import QDate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime, timedelta

from src.parser import BBOXParser
from src.processor import DataProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BBOX Analyzer")
        self.setGeometry(100, 100, 1200, 800)

        # Создаем центральный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем верхнюю панель с выбором директории
        top_panel = QHBoxLayout()
        self.dir_path = QLineEdit()
        self.dir_path.setReadOnly(True)
        browse_button = QPushButton("Выбрать директорию")
        browse_button.clicked.connect(self.browse_directory)
        top_panel.addWidget(QLabel("Директория:"))
        top_panel.addWidget(self.dir_path)
        top_panel.addWidget(browse_button)
        layout.addLayout(top_panel)

        # Создаем панель с выпадающими списками
        filter_panel = QHBoxLayout()
        self.fuel_column_combo = QComboBox(self)
        self.fuel_type_combo = QComboBox(self)
        self.gas_station = QComboBox(self)

        self.fuel_column_combo.currentIndexChanged.connect(self.onComboBoxChange)
        self.fuel_type_combo.currentIndexChanged.connect(self.onComboBoxChange)
        self.gas_station.currentIndexChanged.connect(self.onComboBoxChange)

        filter_panel.addWidget(QLabel("Топливная колонка:"))
        filter_panel.addWidget(self.fuel_column_combo)
        filter_panel.addWidget(QLabel("Вид топлива:"))
        filter_panel.addWidget(self.fuel_type_combo)
        filter_panel.addWidget(QLabel("Номер заправки:"))
        filter_panel.addWidget(self.gas_station)

        layout.addLayout(filter_panel)

        # Добавляем панель выбора дат
        date_panel = QHBoxLayout()
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.end_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date.setDate(QDate.currentDate())

        self.start_date.dateChanged.connect(self.onDateChange)
        self.end_date.dateChanged.connect(self.onDateChange)

        date_panel.addWidget(QLabel("Начальная дата:"))
        date_panel.addWidget(self.start_date)
        date_panel.addWidget(QLabel("Конечная дата:"))
        date_panel.addWidget(self.end_date)
        layout.addLayout(date_panel)

        # Создаем область для графика
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)  # Устанавливаем минимальную высоту
        layout.addWidget(self.canvas, stretch=1)  # Добавляем stretch=1 для автоматического изменения размера

        # Добавляем консоль для вывода
        console_layout = QVBoxLayout()
        console_label = QLabel("Консоль:")
        self.console = QListWidget()
        self.console.setMaximumHeight(250)
        console_layout.addWidget(console_label)
        console_layout.addWidget(self.console)
        layout.addLayout(console_layout)

        # Инициализируем парсер и список найденных файлов
        self.parser = BBOXParser()
        self.found_files = []
        self.loaded_dates = set()  # Множество для хранения загруженных дат

    def log_message(self, message):
        """Добавляет сообщение в консоль"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.console.addItem(f"[{current_time}] {message}")
        self.console.scrollToBottom()

    def find_bbox_files(self, directory):
        """Рекурсивный поиск BBOX файлов"""
        try:
            self.found_files = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.upper().endswith('.XML') and str(file.upper()).startswith('BBOX'):
                        full_path = os.path.join(root, file)
                        self.found_files.append(full_path)
                        self.log_message(f"Найден файл: {full_path}")
                        break

            self.log_message(f"Всего найдено файлов: {len(self.found_files)}")
            return True
        except Exception as e:
            self.log_message(f"Ошибка при поиске файлов: {str(e)}")
            return False

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию с файлами BBOX")
        if directory:
            self.dir_path.setText(directory)
            self.log_message(f"Выбрана директория: {directory}")
            self.log_message("Начинаем поиск файлов...")
            if self.find_bbox_files(directory):
                self.process_files()

    def process_files(self):
        """Асинхронная обработка файлов"""
        self.processor = DataProcessor(self.parser, self.found_files)
        self.processor.progress.connect(self.log_message)
        self.processor.finished.connect(self.on_processing_finished)
        self.processor.start()

    def on_processing_finished(self):
        self.update_comboboxes()
        self.calculate_graph_data()
        self.draw_graph()

    def validDateUpdate(self, dates):
        """Обработчик завершения обработки файлов"""
        self.loaded_dates = set()
        for date in dates:
            self.loaded_dates.add(date)

        if self.loaded_dates:
            min_date = min(self.loaded_dates)
            max_date = max(self.loaded_dates)

            # Устанавливаем диапазон дат
            self.start_date.setDateRange(QDate.fromString(min_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'),
                                         QDate.fromString(max_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
            self.end_date.setDateRange(QDate.fromString(min_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'),
                                       QDate.fromString(max_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))

            # Устанавливаем значения по умолчанию
            self.start_date.setDate(QDate.fromString(min_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
            self.end_date.setDate(QDate.fromString(max_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))

        self.draw_graph()

    def update_comboboxes(self):
        try:
            self.parser.columns.sort()
            self.parser.fuels.sort()
            self.IsDoClear = True
            fuel_column_combo_last_text = self.fuel_column_combo.currentText()
            self.fuel_column_combo.clear()
            fuel_type_combo_last_text = self.fuel_type_combo.currentText()
            self.fuel_type_combo.clear()
            gas_station_last_text = self.gas_station.currentText()
            self.gas_station.clear()

            # Add all gas_stations
            for station in self.parser.gas_stations:
                self.gas_station.addItem(station)

            # Add columns in this gaz station
            StationsList = []
            Station = self.gas_station.currentText()
            if gas_station_last_text:
                Station = gas_station_last_text
                self.gas_station.setCurrentText(Station)

            for column in self.parser.GlobalDict[Station].keys():
                StationsList.append(column)
            StationsList.sort()
            for station in StationsList:
                self.fuel_column_combo.addItem(str(station).strip())

            # Add fuels in this column
            FuelList = []
            Column = self.fuel_column_combo.currentText()
            if fuel_column_combo_last_text and fuel_column_combo_last_text in self.parser.GlobalDict[Station]:
                Column = fuel_column_combo_last_text
                self.fuel_column_combo.setCurrentText(Column)
            for fuel in self.parser.GlobalDict[Station][Column]:
                FuelList.append(fuel)
            FuelList.sort()
            for fuel in FuelList:
                self.fuel_type_combo.addItem(fuel.strip())

            if fuel_type_combo_last_text and fuel_type_combo_last_text in self.parser.GlobalDict[Station][Column]:
                self.fuel_type_combo.setCurrentText(fuel_type_combo_last_text)

            self.IsDoClear = False
        except Exception as e:
            self.IsDoClear = False
            print(f"Ошибка обновления выпадающих списков. \n{e}")

    def onComboBoxChange(self):
        if not self.IsDoClear:
            self.update_comboboxes()
            self.draw_graph()

    def onDateChange(self):
        """Обработчик изменения дат"""
        if self.start_date.date() > self.end_date.date():
            self.log_message("Начальная дата не может быть позже конечной")
            self.start_date.setDate(self.end_date.date())
            return

        # Проверяем, что выбранные даты входят в диапазон загруженных данных
        selected_start = self.start_date.date().toPyDate()
        selected_end = self.end_date.date().toPyDate()

        if self.loaded_dates:
            min_date = min(self.loaded_dates)
            max_date = max(self.loaded_dates)

            if selected_start < min_date:
                self.log_message(f"Начальная дата не может быть раньше {min_date}")
                self.start_date.setDate(QDate.fromString(min_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
                return

            if selected_end > max_date:
                self.log_message(f"Конечная дата не может быть позже {max_date}")
                self.end_date.setDate(QDate.fromString(max_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
                return

        self.draw_graph()

    def calculate_graph_data(self):
        self.Graph = dict()
        hose_into_fuel = []
        loadedDates = []
        for i in range(len(self.parser.columns)):
            hose_into_fuel.append(dict(zip([_ + 1 for _ in range(len(self.parser.fuels))],
                                           [fuel for fuel in self.parser.fuels])))
        for file_data in self.parser.data:
            Column_operation = [{"Start fuel value": 0.0,
                                 "End fuel value": 0.0,
                                 "Start time": 0,
                                 "Fuel": -1,
                                 "FuelName": "",
                                 "End time": 0} for _ in range(len(self.parser.columns))]

            for Operation in file_data:
                if "Доза установлена" in Operation['ACTION']:
                    actionData = Operation['ACTION'].split(';')
                    ColumnIdx = -1
                    for data in actionData:
                        if "ТРК: " in data:
                            ColumnIdx = int(data[data.find(':') + 1:]) - 1
                        elif "Прод.: " in data:
                            Fuel = data[data.find('Прод.: ') + len("Прод.: "):]
                            Column_operation[ColumnIdx]["FuelName"] = Fuel
                            break
                elif "Установка дозы" in Operation['ACTION']:
                    actionData = Operation['ACTION'].split(';')
                    ColumnIdx = -1
                    for data in actionData:
                        if "ТРК : " in data:
                            ColumnIdx = int(data[data.find(':') + 1:]) - 1
                        elif "Рукав: " in data:
                            Fuel = int(data[data.find('Рукав:') + len("Рукав:"):])
                            Column_operation[ColumnIdx]["Fuel"] = Fuel
                            if Column_operation[ColumnIdx]["FuelName"]:
                                hose_into_fuel[ColumnIdx][Fuel] = Column_operation[ColumnIdx]["FuelName"]
                        elif "Счетчик:" in data:
                            StartFuelValue = float(str(data[data.find(':') + 1:]).replace(',', '.'))
                            Column_operation[ColumnIdx]["Start fuel value"] = StartFuelValue
                elif "На ТРК идет отпуск топлива" in Operation['ACTION']:
                    actionData = Operation['ACTION'].split(';')
                    ColumnIdx = -1
                    for data in actionData:
                        if "ТРК : " in data:
                            ColumnIdx = int(data[data.find(':') + 1:]) - 1
                            break
                    if Column_operation[ColumnIdx]["Start time"]:
                        continue
                    Column_operation[ColumnIdx]["Start time"] = datetime.strptime(Operation['DATETIME'] + "000",
                                                                                  "%Y%m%dT%H:%M:%S%f")
                elif "На ТРК закончен отпуск топлива" in Operation['ACTION']:
                    actionData = Operation['ACTION'].split(';')
                    ColumnIdx = -1
                    for data in actionData:
                        if "ТРК : " in data:
                            ColumnIdx = int(data[data.find(':') + 1:]) - 1
                            break
                    Column_operation[ColumnIdx]["End time"] = datetime.strptime(Operation['DATETIME'] + "000",
                                                                                "%Y%m%dT%H:%M:%S%f")
                elif "Конец транзакции" in Operation['ACTION']:
                    actionData = Operation['ACTION'].split(';')
                    ColumnIdx = -1
                    for data in actionData:
                        if "ТРК : " in data:
                            ColumnIdx = int(data[data.find(':') + 1:]) - 1
                        if "Счетчик:" in data:
                            txt = str(data[data.find(':') + 1:]).replace(',', '.').strip()
                            if txt == "NAN":
                                Column_operation[ColumnIdx] = {"Start fuel value": 0.0, "End fuel value": 0.0,
                                                               "Start time": 0, "Fuel": -1, "FuelName": "",
                                                               "End time": 0}
                                continue
                            EndFuelValue = float(txt)
                            Column_operation[ColumnIdx]["End fuel value"] = EndFuelValue
                    dTime = Column_operation[ColumnIdx]["End time"] - Column_operation[ColumnIdx]["Start time"]
                    if dTime:
                        dTime = dTime.total_seconds() / 60
                        dFuel = Column_operation[ColumnIdx]["End fuel value"] - Column_operation[ColumnIdx][
                            "Start fuel value"]
                        if dFuel < 0:
                            dFuel = 1000000 - Column_operation[ColumnIdx]["Start fuel value"] + \
                                    Column_operation[ColumnIdx]["End fuel value"]
                        Speed = dFuel / dTime
                        DATE = Column_operation[ColumnIdx]["End time"].date()
                        if DATE not in loadedDates:
                            loadedDates.append(DATE)
                        if Speed < 0 or Speed > 150:
                            print("???????????????????", DATE)
                        FuelName = Column_operation[ColumnIdx]["FuelName"]
                        # if not DATE in self.Graph:
                        #     self.Graph[DATE] = []
                        #     for i in range(len(self.parser.columns)):
                        #         self.Graph[DATE].append(dict(zip([fuel for fuel in self.parser.fuels],
                        #                                   [{"time": 0, "fuel": 0} for _ in
                        #                                    range(len(self.parser.fuels))])))
                        # self.Graph[DATE][ColumnIdx][FuelName]["fuel"] += dFuel
                        # self.Graph[DATE][ColumnIdx][FuelName]["time"] += dTime
                        if not DATE in self.Graph:
                            self.Graph[DATE] = []
                            for i in range(len(self.parser.columns)):
                                self.Graph[DATE].append(dict(zip([fuel for fuel in self.parser.fuels],
                                                                 [{"time": [], "fuel": []} for _ in
                                                                  range(len(self.parser.fuels))])))
                        self.Graph[DATE][ColumnIdx][FuelName]["fuel"].append(dFuel)
                        self.Graph[DATE][ColumnIdx][FuelName]["time"].append(
                            (Column_operation[ColumnIdx]["Start time"], Column_operation[ColumnIdx]["End time"]))

                    Column_operation[ColumnIdx] = {"Start fuel value": 0.0, "End fuel value": 0.0, "Start time": 0,
                                                   "Fuel": -1, "FuelName": "", "End time": 0}
                elif "Топливный заказ перемещен" in Operation['ACTION']:
                    # Тр: 3078491;
                    # Топливный заказ перемещен с ТРК: 8 на ТРК: 7
                    FROM, TO = Operation['ACTION'][Operation['ACTION'].find("ТРК:") + len("ТРК:"):].split("на ТРК:")
                    Column_operation[int(TO) - 1]["FuelName"] = Column_operation[int(FROM) - 1]["FuelName"]
                    Column_operation[int(FROM) - 1] = {"Start fuel value": 0.0, "End fuel value": 0.0, "Start time": 0,
                                                       "Fuel": -1, "FuelName": "", "End time": 0}
        self.validDateUpdate(loadedDates)

    def draw_graph(self):
        if not self.Graph:
            self.log_message(f"Не удалось получить данные для построения графика")
            return
        X = []
        Y = []
        dX = []
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        self.Graph = dict(sorted(self.Graph.items()))
        k = 0
        dSpeed = 0
        cnt = 0
        for x, columns in self.Graph.items():
            if x < start_date or x > end_date:
                continue
            fuel = columns[int(self.fuel_column_combo.currentText()) - 1][self.fuel_type_combo.currentText()]["fuel"]
            time = columns[int(self.fuel_column_combo.currentText()) - 1][self.fuel_type_combo.currentText()]["time"]
            if time:
                for _ in range(len(fuel)):
                    if time[_][1] - time[_][0]:
                        dt = ((time[_][1] - time[_][0]).total_seconds() / 60)
                        meanSpeed = fuel[_] / dt
                        dSpeed += meanSpeed
                        cnt += 1
                        Y.append(meanSpeed)
                        X.append(time[_][0])
                        dX.append(timedelta(minutes=dt))
        dSpeed /= cnt
        self.ax.bar(X, Y, dX, color="blue")
        self.ax.axhline(dSpeed, color="red")
        self.ax.set_ylim(0, 100)
        self.ax.margins(0.05)
        self.ax.set_xlabel("Дата")
        self.ax.set_ylabel("Скорость")
        self.ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

        # if X and Y:
        #     self.ax.plot(X, Y)
        #     self.ax.set_xlabel("Дата")
        #     self.ax.set_ylabel("Скорость")
        #     # Форматируем даты на оси X
        #     self.ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
        #     plt.xticks(rotation=45)
        #     self.figure.tight_layout()
        #     self.canvas.draw()
        # else:
        #     self.log_message("Нет данных за выбранный период")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Вы уверены, что хотите закрыть приложение?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
