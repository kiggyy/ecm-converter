import os
import shutil
from openpyxl import Workbook, load_workbook

MAPPING_COLUMNS = {
    "Feeder": 7,
    "Value": 20,
    "Footprint": 10,
    "PartRemark": 14,
    "X": 5,
    "Y": 5,
    "H": 5,
    "W": 4,
    "Afed": 5,
    "Arot": 5,
    "Nz": 4,
    "Strk": 5,
    "FIdx": 4,
    "Designators": 50,
    "DesignatorsCount": 0,
    "PartRemarkTS": 5,
    "PartRemark3P": 1,
}
MAPPING_HEADERS = list(MAPPING_COLUMNS.keys())


class Mapping:
    def __init__(self, mapping_file) -> None:
        self.mapping_file = mapping_file
        self.current_mapping_values = {}
        self.load_mapping()

    def __init_excel_mapping(self, sheet) -> None:
        column_sizes = list(MAPPING_COLUMNS.values())
        for i in range(len(MAPPING_HEADERS)):
            col = i + 1
            sheet.cell(row=1, column=col).value = MAPPING_HEADERS[i]
            sheet.column_dimensions[
                sheet.cell(row=1, column=col).column_letter
            ].width = column_sizes[i]

    def __get_current_mapping_values(self) -> None:
        if self.__is_new:
            return
        col_value = self.__get_column_by_name("Value") - 1
        col_footprint = self.__get_column_by_name("Footprint") - 1
        idx = 0
        for row in self.sheet.rows:
            idx += 1
            if idx > 1:
                key = row[col_value].value + "#:#" + row[col_footprint].value
                self.current_mapping_values[key] = idx

    def load_mapping(self) -> None:
        if os.path.exists(self.mapping_file):
            self.workbook = load_workbook(filename=self.mapping_file)
            self.__is_new = False
        else:
            self.workbook = Workbook()
            self.__is_new = True

        self.__is_resolved = False
        self.sheet = self.workbook.active
        self.__get_current_mapping_values()

    def find_row_by_cell(self, index, value):
        idx = 0
        index = index - 1
        for row in self.sheet.rows:
            idx += 1
            if row[index].value == value:
                return idx
        return 0

    def merge_mapping(self, pcb_new_mapping) -> int:
        if self.__is_new:
            self.changes_count = -1
            return self.changes_count
        self.changes_count = 0

        self.__is_resolved = True
        current_mapping_values = self.current_mapping_values.copy()
        for key, p in pcb_new_mapping.items():
            val = p["Value"]
            if val != val:
                continue
            row_no = self.current_mapping_values.get(key, 0)
            if row_no:
                row = self.sheet[row_no]
#                print("Found {}, row {}".format(val, row_no))
                p["row"] = row_no  # update the pointed cell
                for i in [
                    "H",
                    "Feeder",
                    "X",
                    "Y",
                    "Afed",
                    "Arot",
                    "W",
                    "PartRemark",
                    "Nz",
                    "Strk",
                    "FIdx",
                    "PartRemarkTS",
                    "Remark3",
                ]:
                    p[i] = row[self.__get_column_by_name(i) - 1].value
                    if p[i] == None and i not in ["W", "Afed"]:
                        print(
                            "Row {}: part {}/{} has zero attribute {}".format(
                                row_no, val, p["Footprint"], i
                            )
                        )
                        self.__is_resolved = False

                for i in ["Designators"]:
                    col = self.__get_column_by_name(i) - 1
                    if p[i] != row[col].value:
                        self.changes_count += 1
                        print(
                            "Row {}: part {}/{} changed {}: {} -> {}".format(
                                row_no, val, p["Footprint"], i, row[col].value, p[i]
                            )
                        )
                        self.__is_resolved = False

                current_mapping_values[val] = 0
            else:
                self.changes_count += 1
                self.__is_resolved = False
                print("New value {}".format(val))

        # absent = [k for k in current_mapping_values.keys() if current_mapping_values[k] != 0]
        # for p in absent:
        #     self.__is_resolved = False
        #     print("Absent: {}".format(p))

        print("Mapping changes: {}".format(self.changes_count))
        return self.changes_count

    def __get_column_by_name(self, name) -> int:
        return MAPPING_HEADERS.index(name) + 1 if name in MAPPING_HEADERS else -1

    def save_mapping(self, mapping) -> None:
        self.sheet = self.workbook.active
        if self.__is_new:
            self.__init_excel_mapping(self.sheet)
        row = 2

        for p in mapping.values():
            for k in p:
                col = self.__get_column_by_name(k)
                if col != -1:
                    self.sheet.cell(row=row, column=col).value = p[k]
            row += 1
        if not self.__is_new:
            shutil.copy(self.mapping_file, self.mapping_file + ".bak")
        try:
            self.workbook.save(filename=self.mapping_file)
        except Exception as err:
            print("CAN't update mapping file {}: {}\nExiting!".format(self.mapping_file, err))
            exit(100)
            
    def is_resolved(self) -> bool:
        return self.__is_resolved
