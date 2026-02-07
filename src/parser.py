import xml.etree.ElementTree as ET


class BBOXParser:
    def __init__(self):
        self.data = []
        self.fuels = []
        self.columns = []
        self.gas_stations = []
        self.GlobalDict = dict()

    def parse_file(self, file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            file_data = []

            # Здесь будет логика парсинга XML файла
            for element in root.iter():
                if element.tag == "ROW":
                    if (station := element.attrib['HOST'][
                        :element.attrib['HOST'].find('-')].strip()) not in self.gas_stations:
                        self.gas_stations.append(station)
                        if station not in self.GlobalDict:
                            self.GlobalDict[station] = dict()  # Добавляем словарь станций
                    if element.attrib['ACTION'].startswith('ТРК : '):
                        action = element.attrib['ACTION']
                        TRK_number = action[action.find("ТРК : ") + len("ТРК : "):action.find(";")].strip()
                        if TRK_number not in self.GlobalDict[station]:
                            self.GlobalDict[station][TRK_number] = list()  # Добавляем массив топлива
                        file_data.append(
                            {'DATETIME': element.attrib['DATETIME'], 'ACTION': element.attrib['ACTION']}
                        )
                    elif element.attrib['ACTION'].startswith('Тр: ') and "Топливный заказ перемещен" in element.attrib[
                        'ACTION']:
                        file_data.append(
                            {'DATETIME': element.attrib['DATETIME'], 'ACTION': element.attrib['ACTION']}
                        )
                    elif element.attrib['ACTION'].startswith('Тр: ') and "Доза установлена" in element.attrib['ACTION']:
                        action = element.attrib['ACTION']
                        TRK_number = action[action.find("ТРК: ") + len("ТРК: "):]
                        TRK_number = TRK_number[:TRK_number.find(";")].strip()
                        FuelName = action[action.find("Прод.:") + len("Прод.:"):]
                        FuelName = FuelName[:FuelName.find(';')].strip()
                        if FuelName not in self.GlobalDict[station][TRK_number]:
                            self.GlobalDict[station][TRK_number].append(FuelName)
                        file_data.append(
                            {'DATETIME': element.attrib['DATETIME'], 'ACTION': element.attrib['ACTION']}
                        )
                    elif (element.attrib['ACTION'].startswith('Тр: ') and
                          "Налив зафиксирован" in element.attrib['ACTION']):
                        action = element.attrib['ACTION']
                        TRK_number = action[action.find("ТРК: ") + len("ТРК: "):]
                        TRK_number = TRK_number[:TRK_number.find(";")].strip()
                        FuelName = action[action.find("Прод.:") + len("Прод.:"):]
                        FuelName = FuelName[:FuelName.find(';')].strip()
                        if FuelName not in self.GlobalDict[station][TRK_number]:
                            self.GlobalDict[station][TRK_number].append(FuelName)
                        dataStartIdx = element.attrib['ACTION'].find('(')
                        dataArr = element.attrib['ACTION'][dataStartIdx + 1:-1].split(';')
                        for data in dataArr:
                            if "Прод.:" in data:
                                FuelName = data[data.find(':') + 1:].strip()
                                if FuelName not in self.fuels:
                                    self.fuels.append(FuelName)
                            elif "ТРК: " in data:
                                ColumnNum = int(data[data.find(':') + 1:])
                                if ColumnNum not in self.columns:
                                    self.columns.append(ColumnNum)

            self.data.append(file_data)
            return True
        except Exception as e:
            print(f"Error parsing file {file_path}: {str(e)}")
            return False
