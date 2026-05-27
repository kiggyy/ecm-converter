import argparse
import os
import re
import sys

from bcolors import bcolors
from import_pcb import ALIASES, ImportPcb
from mapping import Mapping
from project_config import build_project_context


SEQ_FIELDS = ["Feeder", "Strk", "FIdx"]


def normalize(value):
    if value is None:
        return ""
    value = str(value).strip()
    try:
        number = float(value)
        if number.is_integer():
            return str(int(number))
        return str(round(number, 6)).rstrip("0").rstrip(".")
    except ValueError:
        return value


def designator_from_remark(remark):
    remark = remark.strip()
    if remark.endswith("0.2"):
        remark = remark[:-3]
    return remark.strip()


def build_designator_info(pcb_items, imported_mapping):
    designator_info = {}
    mapping_keys = set(imported_mapping.keys())
    for _, row in pcb_items.iterrows():
        value = row.value if row.value == row.value else ""
        if value in ALIASES:
            value = ALIASES[value]
        footprint = row.case.upper().strip() if row.case == row.case else ""
        key = value + "#:#" + footprint
        if key not in mapping_keys:
            continue
        designator_info[str(row.designator).strip()[:12]] = {
            "key": key,
            "rotation": float(row.rotation),
        }
    return designator_info


def build_designator_keys(imported_mapping):
    designator_info = {}
    for key, item in imported_mapping.items():
        designators = item["Designators"].split(": ", 1)[-1]
        if ": " in designators:
            designators = designators.split(": ", 1)[-1]
        for designator in designators.split(","):
            designator = designator.strip()
            if designator:
                designator_info[designator[:12]] = {"key": key, "rotation": 0}
    return designator_info


def normalize_angle(angle):
    angle = float(angle) % 360
    if angle.is_integer():
        return int(angle)
    return round(angle, 6)


def machine_angle_to_arot(machine_angle, pcb_rotation, board_rotate):
    return normalize_angle(float(machine_angle) / 100 - pcb_rotation - board_rotate + 90)


def parse_seq(seq_file, designator_info, board_info):
    seq_items = {}
    seq_partno_keys = {}
    if not seq_file:
        return seq_items, seq_partno_keys

    item_re = re.compile(
        r"^\s*(?P<PartNo>\d+)\s*:\s*(?P<Strk>[^:]*)\s*:\s*(?P<FIdx>[^:]*)"
        r"\s*:\s*0\s*:\s*0\s*:\s*(?P<Skip>\*)?1\s*:\s*[^:]*"
        r"\s*:\s*F\s*(?P<Feeder>\d+)X.*?A\s*(?P<Angle>-?\d+(?:\.\d+)?)R(?P<Remark>.*)$"
    )
    with open(seq_file, "rt") as f:
        for line_no, line in enumerate(f, 1):
            match = item_re.match(line)
            if not match:
                continue
            if match["Skip"]:
                continue
            designator = designator_from_remark(match["Remark"])
            info = designator_info.get(designator)
            if not info:
                bcolors.color_print_warning(
                    "WARNING: {}:{} designator {} not found in CSV/mapping".format(
                        seq_file, line_no, designator
                    )
                )
                continue
            key = info["key"]
            seq_partno_keys[int(match["PartNo"])] = key
            seq_items[key] = {field: match[field].strip() for field in SEQ_FIELDS}
            seq_items[key]["Arot"] = machine_angle_to_arot(
                match["Angle"], info["rotation"], board_info.Rotate
            )
    return seq_items, seq_partno_keys


def split_part_remark(remark):
    remark = remark[1:] if remark.startswith("R") else remark
    return {
        "PartRemark": remark[:10].strip(),
    }


def parse_part_dat(parts_file, partno_keys):
    parts = {}
    if not parts_file:
        return parts

    with open(parts_file, "rt") as f:
        for part_no, line in enumerate(f.readlines()[1:], 1):
            fields = line.rstrip("\n").split(":")
            if len(fields) < 12:
                continue
            key = partno_keys.get(part_no)
            if not key:
                continue
            item = {
                "Nz": fields[0].strip(),
                "X": fields[5].strip(),
                "Y": fields[6].strip(),
                "W": fields[8].strip(),
                "H": fields[9].strip(),
            }
            item.update(split_part_remark(fields[11].strip()))
            if not any(item.values()):
                continue
            parts[key] = item
    return parts


def collect_differences(imported_mapping, machine_values, machine_feeders=None):
    machine_feeders = machine_feeders if machine_feeders else {}
    updates = {}
    for key, machine_item in machine_values.items():
        mapping_item = imported_mapping[key]
        machine_feeder = machine_item.get("Feeder", machine_feeders.get(key, ""))
        for field, machine_value in machine_item.items():
            if machine_value is None:
                continue
            if field == "FIdx" and normalize(machine_feeder) and int(normalize(machine_feeder)) > 99:
                continue
            if field == "PartRemark" and normalize(mapping_item.get(field, "")).startswith(normalize(machine_value)):
                continue
            if normalize(mapping_item.get(field, "")) == normalize(machine_value):
                continue
            updates.setdefault(key, {})[field] = machine_value
            print(
                "Mismatch {}/{} feeder {} field {}: mapping [{}] -> machine [{}]".format(
                    mapping_item["Value"],
                    mapping_item["Footprint"],
                    normalize(machine_feeder),
                    field,
                    normalize(mapping_item.get(field, "")),
                    normalize(machine_value),
                )
            )
    return updates


def merge_updates(*updates_list):
    result = {}
    for updates in updates_list:
        for key, fields in updates.items():
            result.setdefault(key, {}).update(fields)
    return result


def apply_excel_values(imported_mapping, excel_mapping):
    for key, item in imported_mapping.items():
        if key not in excel_mapping:
            bcolors.color_print_warning(
                "WARNING: {} / {} not found in Excel mapping".format(
                    item["Value"], item["Footprint"]
                )
            )
            continue
        excel_item = excel_mapping[key]
        item["row"] = excel_item["row"]
        for field, value in excel_item.items():
            if field in ("row", "Value", "Footprint", "Designators"):
                continue
            if field in item:
                item[field] = "" if value is None else value


def main():
    parser = argparse.ArgumentParser(
        description="Compare corrected ECM P&P files with Excel mapping and import corrections back."
    )
    parser.add_argument("project_file", help="Project yaml file, the same file used by im.py")
    parser.add_argument("--seq", default=None, help="Corrected .seq file. Default: generated project .seq")
    parser.add_argument("--part", default=None, help="Corrected part.dat file. Default: project part.dat")
    parser.add_argument("-y", "--yes", action="store_true", help="Update mapping without confirmation")
    args = parser.parse_args()

    context = build_project_context(args.project_file)
    seq_file = args.seq if args.seq else context.seq_file
    parts_file = args.part if args.part else context.parts_file

    im = ImportPcb(context.project_name)
    im.read_input(context.import_pcb_file)
    im.generate_imported_values_mapping()

    mapping = Mapping(context.mapping_file, board_info=context.board_info)
    apply_excel_values(im.imported_mapping, mapping.get_current_mapping())

    designator_info = build_designator_info(im.pcb_items, im.imported_mapping)
    if not designator_info:
        designator_info = build_designator_keys(im.imported_mapping)

    if not os.path.exists(seq_file):
        bcolors.color_print_error("ERROR: corrected seq file not found/read: {}".format(seq_file))
        return 2

    seq_values, seq_partno_keys = parse_seq(seq_file, designator_info, context.board_info)
    part_values = parse_part_dat(parts_file, seq_partno_keys) if os.path.exists(parts_file) else {}

    if not seq_values:
        bcolors.color_print_error("ERROR: no mounted parts found in seq file: {}".format(seq_file))
        return 2

    machine_feeders = {key: item.get("Feeder", "") for key, item in seq_values.items()}
    updates = merge_updates(
        collect_differences(im.imported_mapping, part_values, machine_feeders),
        collect_differences(im.imported_mapping, seq_values, machine_feeders),
    )

    if not updates:
        print("No mismatches found.")
        return 0

    print("Total parts with changes: {}".format(len(updates)))
    if not args.yes:
        answer = input("Import these changes into Excel mapping? [y/N]: ").strip().lower()
        if answer != "y":
            print("Mapping was not changed.")
            return 0

    mapping.apply_updates(updates)
    print("Mapping updated: {} (.bak created)".format(context.mapping_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())
