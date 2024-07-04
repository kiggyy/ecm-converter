import pandas as pd
import re

PACKAGE_SIZES = {
    "R0201": "0.6x0.3/Nz=2",
    "C0201": "0.6x0.3/Nz=2",
    "R0405": "1.0x0.5/Nz=2",
    "C0405": "1.0x0.5/Nz=2",
    "R0603": "1.7x0.8x0.45/Nz=2",
    "C0603": "1.7x0.8/Nz=2",
    "R0805": "2.0x1.25x0.5/Nz=2",
    "C0805": "2.0x1.25/Nz=2",
    "R1206": "3.2x1.6/Nz=2",
    "C1206": "3.2x1.6/Nz=2",
    "R1210": "3.2x2.5/Nz=2",
    "C1210": "3.2x2.5/Nz=2",
    "R1218": "3.2x4.6/Nz=2",
    "C1218": "3.2x4.6/Nz=2",
    "R2010": "5.0x2.5/Nz=2",
    "C2010": "5.0x2.5/Nz=2",
    "R2512": "6.3x3.2/Nz=2",
    "C2512": "6.3x3.2/Nz=2",
    "SOT23": "2.9x2.4x0.9",
    "SMA": "3.56x2.92",
}

PACKAGE_TO_ECM_TYPE = {
    "^SO": "SOP",
    "QFP": "QFP",
}


class ImportPcb:
    def __init__(self) -> None:
        pass

    def read_input(self, csv_file) -> None:
        # self.pcb_items = pd.read_excel('Pick Place for UMTP04(12)PWR(Actual).xlsx')
        with open(csv_file, "rt") as f:
            row = 0
            for l in f:
                if l.strip():
                    row += 1
                if "Footprint_SMD" in l:
                    break

        self.pcb_items = pd.read_csv(
            csv_file, header=row - 1, encoding="cp1251", encoding_errors="replace"
        )
        #        self.pcb_items.insert(3, 'Prefix', '')
        self.pcb_items.insert(3, "Type", "")
        #        self.pcb_items['Case/Package'] = self.pcb_items.apply( lambda x: x['Case/Package'] if x['Case/Package'] else "none", axis=1)
        #        self.pcb_items.Prefix = self.pcb_items.apply( lambda x:self.__get_component_type(x.Designator,x['Case/Package'])['P'], axis=1)
        self.pcb_items.Type = self.pcb_items.apply(
            lambda x: self.__get_component_type(x), axis=1
        )

    #        self.pcb_items.Value = self.pcb_items.apply( lambda x: x.Value if x.Value else x.Description, axis=1)

    def generate_imported_values_mapping(self) -> None:
        values = self.pcb_items.groupby(["Value", "Footprint_SMD"], dropna=False)
        self.imported_mapping = {}
        index = 0
        for v in values:
            value = v[0][0]
            footprint = v[0][1].upper().strip()
            if footprint in ["TH", "FEDUCIAL", "REFERENCE"]:
                continue
            key = value + "#:#" + footprint
            designators = (
                str(v[1].Designator.count()) + ": "
                if v[1].Designator.count() > 1
                else ""
            )
            designators += ", ".join(v[1].Designator)
            t = v[1].Type.array[0]
            index += 1
            p = {}
            p["Feeder"] = 0
            p["Value"] = value
            p["Footprint"] = footprint
            p["Type"] = t["T"]
            p["PartRemark"] = t["Part"]
            p["X"] = t["X"] if "X" in t else ""
            p["Y"] = t["Y"] if "Y" in t else ""
            p["H"] = t["H"] if "H" in t else ""
            p["W"] = 0
            p["Afed"] = 0
            p["Arot"] = t["Arot"] if "Arot" in t else 0
            p["Designators"] = designators
            p["DesignatorsCount"] = v[1].Designator.count()
            p["row"] = 0
            p["PartNo"] = index
            p["Nz"] = t["Nz"] if "Nz" in t else 0
            p["FIdx"] = 1
            p["Strk"] = 310
            p["PartRemarkTS"] = 70
            p["PartRemark3P"] = ""

            self.imported_mapping[key] = p

    def __get_component_type(self, row):
        # CHI : for chip part (slow down)
        # SOP : for SOIC
        # QFP : for QFP
        # CON : for connector
        # SKIP: Dispenser only no placement.
        # TS : Part size tolerance in %. 70 means 70% or 100/70=142%..(Laser only
        # Under +++ of remark, if numeric value exists then the tape will be advanced during the nozzle
        # is in down position and wait specified time (1/100 sec) and picks up a component. This feature
        # is useful to pick up very tiny component such as 0201
        footprint = row.Footprint_SMD
        #        description = row.Footprint
        #        description_items = description.split('/')

        unknown = {"T": "", "P": "", "Part": "Unknown"}
        if not isinstance(footprint, str) or footprint.strip() == "":
            return unknown

        ecm_prefix = ""
        for r in PACKAGE_TO_ECM_TYPE:
            if re.match(r, footprint):
                ecm_prefix = PACKAGE_TO_ECM_TYPE[r]
                break

        m = re.match("([A-Za-z]+)([0-9]+)?", footprint)
        if not m:
            return unknown
        prefix = m[1]
        #    if prefix not in ['R','C']:
        #        m = re.match("([A-Za-z]+)[0-9]+", designator)
        #        if not m:
        #            return unknown
        #        prefix = m[1]

        defines = (PACKAGE_SIZES[footprint] if footprint in PACKAGE_SIZES else "?x?x?").split("/")
        size = (defines[0] + "x?").split("x")
        t = {"T": footprint, "X": size[0], "Y": size[1], "H": size[2]}
        properties = {}
        for i in defines:
            r = re.match("([A-Z0-9a-z_]+)=(.+)", i)
            if r:
                properties[r[1]] = r[2]
                
        if prefix in ["R", "C"]:
            #            if( 1 not in description_items or
            #               (description_items[0] + description_items[1]) != footprint):
            #                   print("WARNING: Footprint and Description do not match to each other: {}, {}".\
            #                       format(description, footprint))

            ecm_prefix = "SOP" if not ecm_prefix else ecm_prefix
            t["P"] = prefix
            t["Part"] = ecm_prefix + footprint
            t["Arot"] = 90
            if 'Nz' in properties:
                t['Nz'] = properties['Nz']
                
        elif prefix == "L":
            ecm_prefix = "SOP" if not ecm_prefix else ecm_prefix
            t["P"] = "L"
            t["Part"] = ecm_prefix + footprint
        elif prefix == "TH":
            t["P"] = "L"
            t["Part"] = ecm_prefix + footprint
        elif footprint.startswith("SOT"):
            ecm_prefix = "SOT" if not ecm_prefix else ecm_prefix
            t["P"] = "SOT"
            t["Part"] = ecm_prefix + footprint
        else:
            ecm_prefix = "CHI" if not ecm_prefix else ecm_prefix
            t["P"] = "SOT"
            t["Part"] = ecm_prefix + footprint
        return t
