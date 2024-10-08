import pandas as pd
import re

FIELD_CASE = "case"

PACKAGE_SIZES_REGEXP = {
    "^#?S(?P<S>[0-9.]+)H(?P<H>[0-9.]+)":"",
    "^#?L(?P<L>[0-9.]+)W(?P<W>[0-9.]+)H(?P<H>[0-9.]+)":"",
}

PACKAGE_SIZES = {
    "R0201": "0.6x0.3x0.5/Nz=2",
    "C0201": "0.6x0.3x0.5/Nz=2",
    "R0405": "1.0x0.5x0.5/Nz=2",
    "C0405": "1.0x0.5x0.5/Nz=2",
    "R0603": "1.7x0.8x0.4/Nz=2",
    "C0603": "1.7x0.8x0.5/Nz=2",
    "R0805": "2.0x1.25x0.5/Nz=2",
    "C0805": "2.0x1.25x0.5/Nz=2",
    "R1206": "3.2x1.6x0.5/Nz=2",
    "C1206": "3.2x1.6x0.5/Nz=2",
    "R1210": "3.2x2.5x0.5/Nz=2",
    "C1210": "3.2x2.5x0.5/Nz=2",
    "R1218": "3.2x4.6x0.5/Nz=2",
    "C1218": "3.2x4.6x0.5/Nz=2",
    "R2010": "5.0x2.5x0.5/Nz=2",
    "C2010": "5.0x2.5x0.5/Nz=2",
    "R2512": "6.3x3.2x0.5/Nz=2",
    "C2512": "6.3x3.2x0.5/Nz=2",
    "Q3225": "3.2x2.5x0.8/Nz=2",
    "SOT23": "2.9x1.7/Nz=2",
    "SOT23-5"   : "2.9x1.7/Nz=2",
    "SOT23-6"   : "2.9x1.7/Nz=2",
    "SOT223"    : "6.4x4/Nz=2",
    "SOD523"    : "1.2x0.8x0.6/Nz=2",
    "LQFP48"    : "7x7/Nz=2",
    "TSSOP16"   : "4.9x4.4x1.2/Nz=6",
    "SO8W"      : "6.9x5.4x1.8/Nz=6",
    "QFN32"     : "5.1x5.1x0.9/Nz=6",
    "Q2016"     : "2x1.6x0.8/Nz=2"

}
#    "SMA": "3.56x2.92",

PACKAGE_TO_ECM_TYPE = {
    "^SO": "SOP",
    "QFP": "QFP",
}


class ImportPcb:
    def __init__(self, project_name) -> None:
        self.project_name = project_name
    
    def read_input(self, csv_file) -> None:
        # self.pcb_items = pd.read_excel('Pick Place for UMTP04(12)PWR(Actual).xlsx')
        with open(csv_file, "rt") as f:
            row = 0
            for l in f:
                line = l.strip().lower()
                if line:
                    row += 1
                if FIELD_CASE in line:
                    break

        self.pcb_items = pd.read_csv(
            csv_file, header=row - 1, encoding="cp1251", encoding_errors="replace"
        )
        self.pcb_items.columns = self.pcb_items.columns.str.lower()
        #        self.pcb_items.insert(3, 'Prefix', '')
        self.pcb_items.insert(3, "type", "")
        #        self.pcb_items['Case/Package'] = self.pcb_items.apply( lambda x: x['Case/Package'] if x['Case/Package'] else "none", axis=1)
        #        self.pcb_items.Prefix = self.pcb_items.apply( lambda x:self.__get_component_type(x.Designator,x['Case/Package'])['P'], axis=1)
        self.pcb_items.type = self.pcb_items.apply(
            lambda x: self.__get_component_type(x), axis=1
        )

    #        self.pcb_items.Value = self.pcb_items.apply( lambda x: x.Value if x.Value else x.Description, axis=1)

    def generate_imported_values_mapping(self) -> None:
        values = self.pcb_items.groupby(["value", FIELD_CASE], dropna=False)
        self.imported_mapping = {}
        index = 0
        for v in values:
            value = v[0][0]
            footprint = v[0][1].upper().strip()
            if footprint in ["TH", "PCB", "FEDUCIAL", "REFERENCE"]:
                continue
            key = value + "#:#" + footprint
            designators = self.project_name.upper() + ': ' + (
                str(v[1].designator.count()) + ": "
                if v[1].designator.count() > 1
                else ""
            )
            designators += ", ".join(v[1].designator)
            t = v[1].type.array[0]
            index += 1
            p = {}
            p["Feeder"] = ""
            p["Value"] = value
            p["Footprint"] = footprint
            p["Type"] = t["T"]
            p["PartRemark"] = t["Part"]
            p["X"] = t["X"] if "X" in t else ""
            p["Y"] = t["Y"] if "Y" in t else ""
            p["H"] = t["H"] if "H" in t else ""
            p["W"] = 0
            p["Afed"] = 0
            p["Arot"] = t["Arot"] if "Arot" in t else ""
            p["Xofs"] = 0
            p["Yofs"] = 0
            p["Designators"] = designators
            p["row"] = 0
            p["PartNo"] = index
            p["Nz"] = t["Nz"] if "Nz" in t else ""
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
        footprint = row[FIELD_CASE]
        #        description = row.Footprint
        #        description_items = description.split('/')

        unknown = {"T": "", "P": "", "Part": ""}
        if not isinstance(footprint, str) or footprint.strip() == "":
            return unknown

        ecm_prefix = ""
        for r in PACKAGE_TO_ECM_TYPE:
            if re.match(r, footprint):
                ecm_prefix = PACKAGE_TO_ECM_TYPE[r]
                break

        m = re.match("([A-Za-z]+)([0-9]+)?", footprint)
        prefix = m[1] if m else ""
        #    if prefix not in ['R','C']:
        #        m = re.match("([A-Za-z]+)[0-9]+", designator)
        #        if not m:
        #            return unknown
        #        prefix = m[1]

        t = None
        if footprint in PACKAGE_SIZES:
            defines = (PACKAGE_SIZES[footprint] if footprint in PACKAGE_SIZES else "xx").split("/")
            size = (defines[0] + "x").split("x")
            t = {"T": footprint, "X": size[0], "Y": size[1], "H": size[2]}
        else:
            for i in PACKAGE_SIZES_REGEXP:
                r = re.match(i, footprint)
                if not r:
                    continue
                H = r['H']
                if 'S' in r.groupdict():
                    X = r['S']
                    Y = X
                else:
                    X = r['L']
                    Y = r['W']
                t = {"T": footprint, "X": X, "Y": Y, "H": H}
                defines = PACKAGE_SIZES_REGEXP[i].split("/")
                break
        if not t:
            return unknown
                
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
