import pandas as pd
from collections import namedtuple

PartsItemFields = [
    "Nzl",
    "h1",
    "h2",
    "h3",
    "h4",
    "X",
    "Y",
    "Pt",
    "W",
    "Thk",
    "Lv",
    "Remark",
]
PartsItem = namedtuple("PartsItem", PartsItemFields)


class PcbParts:
    def __init__(self) -> None:
        self.parts_items = []

    def Get(self) -> list[PartsItem]:
        return self.parts_items

    def build_list(self, current_mapping: dict) -> None:
        for index, row in current_mapping.items():
            mapping = row
            p = PartsItem(
                Nzl=mapping["Nz"],
                h1=0,
                h2=0,
                h3=0,
                h4=0,
                X=mapping["X"],
                Y=mapping["Y"],
                Pt=0,
                W=mapping["W"],
                Thk=mapping["H"],
                Lv=1,
                # TS : Part size tolerance in %. 70 means 70% or 100/70=142%..(Laser only)
                # Under +++ of remark, if numeric value exists then the tape will be advanced during the nozzle
                # is in down position and wait specified time (1/100 sec) and picks up a component. This feature
                # is useful to pick up very tiny component such as 0201.
                Remark="{0[PartRemark]:<10.10}{0[PartRemarkTS]:<3d}{0[PartRemark3P]:<3}".format(
                    mapping
                ),
            )
            self.parts_items.append(p)
