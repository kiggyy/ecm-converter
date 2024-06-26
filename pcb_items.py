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
    "H",
    "Pt",
    "Nzl",
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
PcbAssets = namedtuple("PcbRepPoint", ["Bias", "Feducial", "Items"])


class PcbItems:
    def __init__(self, pcb_def: pd) -> None:
        self.pcb_def = pcb_def
        self.pcb_items = []
        self.pcb_feducial = []
        self.bias = PcbPoint(X=0, Y=0)

    def __test_and_add_non_value_list_items(self, row, point) -> bool:
        r = re.match("[ \t]*([A-Za-z_]+)([0-9]+)?", row.Designator)
        if not r:
            return
        value = str(
            row.Footprint_SMD
            if row.Footprint_SMD == row.Footprint_SMD
            else row.Value
            if row.Value == row.Value
            else row.Description
            if row.Description == row.Description
            else ""
        )

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

        return False

    def build_list(self, current_mapping: dict) -> None:
        self.pcb_def = self.pcb_def.reset_index()
        for index, row in self.pcb_def.iterrows():
            value = row.Value if row.Value == row.Value else ""
            footprint = (
                row.Footprint_SMD.upper().strip()
                if row.Footprint_SMD == row.Footprint_SMD
                else ""
            )

            if not value or not footprint or row.Footprint_SMD == "TH":
                continue

            point = PcbPoint(
                X=row["Ref-X(mm)"] if "Ref-X(mm)" in row else row["Center-X(mm)"],
                Y=row["Ref-Y(mm)"] if "Ref-Y(mm)" in row else row["Center-Y(mm)"],
            )
            if self.__test_and_add_non_value_list_items(row, point):
                continue

            key = value + "#:#" + footprint

            mapping = current_mapping[key]
            p = PcbItem(
                Hd=1,
                Fdr=mapping["Feeder"],
                Point=point,
                A=int(row.Rotation) * 100,
                Pt=mapping["PartNo"],
                H=mapping["H"],
                Nzl=mapping["Nz"],
                Ind=mapping["FIdx"],
                Strk=mapping["Strk"],
                DT="",
                HA="",
                Remark="{0[Designator]:<12.12}0.2".format(row),
            )
            self.pcb_items.append(p)

    def Get(self) -> PcbAssets:
        return PcbAssets(
            Bias=self.bias, Feducial=self.pcb_feducial, Items=self.pcb_items
        )
