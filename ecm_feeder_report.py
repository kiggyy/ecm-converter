import argparse
import csv
import html
import os
import re
import sys

from import_pcb import ALIASES, ImportPcb


def normalize_designator(remark):
    remark = remark.strip()
    if remark.endswith("0.2"):
        remark = remark[:-3]
    return remark.strip()


def find_input_file(folder, extension, reject_suffixes=None):
    reject_suffixes = reject_suffixes if reject_suffixes else []
    matches = []
    for name in os.listdir(folder):
        if not name.lower().endswith(extension.lower()):
            continue
        if any(name.lower().endswith(suffix.lower()) for suffix in reject_suffixes):
            continue
        matches.append(os.path.join(folder, name))
    if len(matches) != 1:
        return None
    return matches[0]


def read_csv_items(csv_file):
    project_name = os.path.splitext(os.path.basename(csv_file))[0]
    pcb = ImportPcb(project_name)
    pcb.read_input(csv_file)

    items = {}
    for _, row in pcb.pcb_items.iterrows():
        designator = str(row.designator).strip()
        value = row.value if row.value == row.value else ""
        if value in ALIASES:
            value = ALIASES[value]
        footprint = row.case.upper().strip() if row.case == row.case else ""
        if not designator or not value or not footprint or footprint in ["TH", "PCB"]:
            continue
        items[designator[:12]] = {
            "Designator": designator,
            "Value": value,
            "Footprint": footprint,
        }
    return items


def read_seq_items(seq_file, csv_items):
    seq_items = []
    item_re = re.compile(
        r"^\s*(?P<PartNo>\d+)\s*:\s*(?P<Strk>[^:]*)\s*:\s*(?P<FIdx>[^:]*)"
        r"\s*:\s*0\s*:\s*0\s*:\s*(?P<Skip>\*)?1\s*:\s*[^:]*"
        r"\s*:\s*F\s*(?P<Feeder>\d+)X.*?A\s*(?P<Angle>-?\d+(?:\.\d+)?)R(?P<Remark>.*)$"
    )
    with open(seq_file, "rt") as f:
        for line_no, line in enumerate(f, 1):
            match = item_re.match(line)
            if not match or match["Skip"]:
                continue

            designator_key = normalize_designator(match["Remark"])
            csv_item = csv_items.get(designator_key)
            if not csv_item:
                print(
                    "WARNING: {}:{} designator {} not found in CSV".format(
                        seq_file, line_no, designator_key
                    )
                )
                continue

            item = csv_item.copy()
            item.update(
                {
                    "Feeder": int(match["Feeder"]),
                    "PartNo": int(match["PartNo"]),
                    "Strk": match["Strk"].strip(),
                    "FIdx": match["FIdx"].strip(),
                }
            )
            seq_items.append(item)
    return seq_items


def split_part_remark(remark):
    remark = remark[1:] if remark.startswith("R") else remark
    return remark[:10].strip()


def read_part_dat(parts_file):
    if not parts_file or not os.path.exists(parts_file):
        return {}

    parts = {}
    with open(parts_file, "rt") as f:
        for part_no, line in enumerate(f.readlines()[1:], 1):
            fields = line.rstrip("\n").split(":")
            if len(fields) < 12:
                continue
            parts[part_no] = {
                "Nz": fields[0].strip(),
                "X": fields[5].strip(),
                "Y": fields[6].strip(),
                "H": fields[9].strip(),
                "PartRemark": split_part_remark(fields[11].strip()),
            }
    return parts


def build_report(seq_items, parts):
    grouped = {}
    for item in seq_items:
        key = (item["Feeder"], item["Value"], item["Footprint"], item["PartNo"])
        report_item = grouped.setdefault(
            key,
            {
                "Feeder": item["Feeder"],
                "Value": item["Value"],
                "Footprint": item["Footprint"],
                "PartNo": item["PartNo"],
                "Count": 0,
                "Designators": [],
                "Strk": item["Strk"],
                "FIdx": item["FIdx"],
                "Nz": "",
                "X": "",
                "Y": "",
                "H": "",
                "PartRemark": "",
            },
        )
        report_item["Count"] += 1
        report_item["Designators"].append(item["Designator"])

    for item in grouped.values():
        part = parts.get(item["PartNo"], {})
        for field in ["Nz", "X", "Y", "H", "PartRemark"]:
            item[field] = part.get(field, "")
        item["Designators"] = ", ".join(sorted(item["Designators"]))

    return sorted(grouped.values(), key=lambda x: (x["Feeder"], x["Value"], x["Footprint"]))


def print_report(report):
    headers = ["Feeder", "Count", "Value", "Footprint", "Designators", "PartRemark", "Nz"]
    text = format_text_report(report, headers)
    print(text)


def format_text_report(report, headers=None):
    headers = headers if headers else ["Feeder", "Count", "Value", "Footprint", "Designators", "PartRemark", "Nz"]
    widths = {header: len(header) for header in headers}
    for row in report:
        for header in headers:
            widths[header] = max(widths[header], len(str(row[header])))

    lines = []
    lines.append("  ".join(header.ljust(widths[header]) for header in headers))
    lines.append("  ".join("-" * widths[header] for header in headers))
    for row in report:
        lines.append("  ".join(str(row[header]).ljust(widths[header]) for header in headers))
    return "\n".join(lines)


def save_report(report, output_file):
    headers = [
        "Feeder",
        "Value",
        "Footprint",
        "Count",
        "Designators",
        "PartNo",
        "PartRemark",
        "Nz",
        "X",
        "Y",
        "H",
        "Strk",
        "FIdx",
    ]
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in report:
            writer.writerow({header: row[header] for header in headers})


def save_txt_report(report, output_file):
    headers = ["Feeder", "Count", "Value", "Footprint", "Designators", "PartRemark", "Nz"]
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(format_text_report(report, headers))
        f.write("\n")


def save_html_report(report, output_file):
    headers = [
        "Feeder",
        "Count",
        "Value",
        "Footprint",
        "Designators",
        "PartRemark",
        "Nz",
        "X",
        "Y",
        "H",
    ]
    title = "ECM Feeder Report"
    rows = []
    for row in report:
        cells = []
        for header in headers:
            cls = ' class="designators"' if header == "Designators" else ""
            cells.append("<td{}>{}</td>".format(cls, html.escape(str(row[header]))))
        rows.append("<tr>{}</tr>".format("".join(cells)))

    document = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      color: #111;
    }}
    h1 {{
      font-size: 22px;
      margin: 0 0 16px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid #bbb;
      padding: 5px 7px;
      vertical-align: top;
    }}
    th {{
      background: #eee;
      text-align: left;
      position: sticky;
      top: 0;
    }}
    td:first-child,
    td:nth-child(2),
    td:nth-child(7),
    td:nth-child(8),
    td:nth-child(9),
    td:nth-child(10) {{
      text-align: right;
      white-space: nowrap;
    }}
    .designators {{
      max-width: 760px;
    }}
    @media print {{
      body {{
        margin: 10mm;
      }}
      th {{
        position: static;
      }}
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <table>
    <thead>
      <tr>{headers}</tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
""".format(
        title=html.escape(title),
        headers="".join("<th>{}</th>".format(html.escape(header)) for header in headers),
        rows="\n      ".join(rows),
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(document)


def output_base_name(output):
    root, ext = os.path.splitext(output)
    return root if ext else output


def main():
    parser = argparse.ArgumentParser(
        description="Build feeder report from source CSV and ECM-edited .seq/part.dat files."
    )
    parser.add_argument(
        "source",
        help="Folder with ECM files, or CSV file if --seq is specified. Example: from_ecm",
    )
    parser.add_argument("--csv", default=None, help="Source P&P CSV file")
    parser.add_argument("--seq", default=None, help="ECM-edited .seq file")
    parser.add_argument("--part", default=None, help="ECM-edited part.dat file")
    parser.add_argument("--output", default=None, help="Output base name or file path")
    parser.add_argument("--csv-output", action="store_true", help="Also save CSV report")
    parser.add_argument("--no-save", action="store_true", help="Only print report to console")
    args = parser.parse_args()

    source = args.source
    source_is_folder = os.path.isdir(source)
    folder = source if source_is_folder else os.path.dirname(source)

    csv_file = args.csv if args.csv else (find_input_file(folder, ".csv", ["_zb.csv"]) if source_is_folder else source)
    seq_file = args.seq if args.seq else find_input_file(folder, ".seq")
    parts_file = args.part if args.part else os.path.join(folder, "part.dat")
    output_base = output_base_name(args.output) if args.output else os.path.join(folder, "feeder_report")

    if not csv_file or not os.path.exists(csv_file):
        print("ERROR: source CSV file not found")
        return 2
    if not seq_file or not os.path.exists(seq_file):
        print("ERROR: .seq file not found")
        return 2

    csv_items = read_csv_items(csv_file)
    seq_items = read_seq_items(seq_file, csv_items)
    if not seq_items:
        print("ERROR: no mounted parts found in seq file")
        return 2

    report = build_report(seq_items, read_part_dat(parts_file))
    print_report(report)

    if not args.no_save:
        html_file = output_base + ".html"
        txt_file = output_base + ".txt"
        save_html_report(report, html_file)
        save_txt_report(report, txt_file)
        print("Reports saved: {} {}".format(html_file, txt_file))
        if args.csv_output:
            csv_output_file = output_base + ".csv"
            save_report(report, csv_output_file)
            print("CSV report saved: {}".format(csv_output_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())
