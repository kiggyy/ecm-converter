import os
import sys
import re
import pandas as pd
from collections import namedtuple

PcbItemFields = [
    "Hd",
    "Fdr",
    "Point",
    "A",
    "Arot",
    "H",
    "Pt",
    "Nzl",
    "Xofs",
    "Yofs",
    "Ind",
    "Strk",
    "DT",
    "HA",
    "Remark",
]
PcbItem = namedtuple("PcbItem", PcbItemFields)
PcbRepItemFields = ["No", "Fdr", "Point", "Remark"]
PcbRepItem = namedtuple("PcbRepItem", PcbRepItemFields)
PcbPoint = namedtuple("PcbRepPoint", ["X", "Y"])
PcbAssets = namedtuple("PcbRepPoint", ["Bias", "Feducial", "Items", "Size"])


class PcbItems:
    def __init__(self, pcb_def: pd) -> None:
        self.pcb_def = pcb_def
        self.pcb_items = []
        self.pcb_feducial = []
        self.bias = PcbPoint(X=0, Y=0)
        self.size = PcbPoint(X=0, Y=0)

    def __test_and_add_non_value_list_items(self, row, point) -> bool:
        r = re.match("[ \t]*([A-Za-z_]+)([0-9]+)?", row.designator)
        if not r:
            return
        value = str(row.value).strip()
        case = str(row.case).upper().strip()
        if case not in ["TH","PCB"]:
            return False

        if value.startswith("FEDUCIAL"):
            orderNo = 0 if not r[2] else int(r[2])
            p = PcbRepItem(
                No=orderNo,
                Fdr=270 + orderNo,
                Point=point,
                Remark="Rep.{}".format(orderNo),
            )
            self.pcb_feducial.append(p)
            return True

        elif value.startswith("REFERENCE"):
            self.bias = point
            return True

        elif value.startswith("SIZE_MARK"):
            self.size = point
            return True

        return False

    def build_list(self, current_mapping: dict) -> None:
        self.pcb_def = self.pcb_def.reset_index()
        for index, row in self.pcb_def.iterrows():
            value = row.value if row.value == row.value else ""
            footprint = (
                row.case.upper().strip()
                if row.case == row.case
                else ""
            )

            point = PcbPoint(
                X=row["ref-x(mm)"],# if "Ref-X(mm)" in row else row["Center-X(mm)"],
                Y=row["ref-y(mm)"]# if "Ref-Y(mm)" in row else row["Center-Y(mm)"],
            )
            if self.__test_and_add_non_value_list_items(row, point):
                continue
            if not value or not footprint or footprint in ["TH", "PCB"]:
                continue

            key = value + "#:#" + footprint

            mapping = current_mapping[key]
            p = PcbItem(
                Hd=1,
                Fdr=mapping["Feeder"],
                Point=point,
                A=row.rotation,
                Arot=mapping["Arot"],
                Pt=mapping["PartNo"],
                H=mapping["H"],
                Nzl=mapping["Nz"],
                Ind=mapping["FIdx"],
                Strk=mapping["Strk"],
                Xofs=float(mapping["Xofs"]),
                Yofs=float(mapping["Yofs"]),
                DT="",
                HA="",
                Remark="{0[designator]:<12.12}0.2".format(row),
            )
            self.pcb_items.append(p)

    def Get(self) -> PcbAssets:
        return PcbAssets(
            Bias=self.bias, Feducial=self.pcb_feducial, Items=self.pcb_items, Size=self.size
        )
