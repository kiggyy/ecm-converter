import yaml
import sys
import os
from import_pcb import ImportPcb
from mapping import Mapping
from generator import Generator, BoardInfo
from pcb_items import PcbItems
from pcb_parts import PcbParts
from bcolors import bcolors
project_file = sys.argv[-1]
project_dir, project_file_name_ext = os.path.split(project_file)
project_file_name, project_file_ext = os.path.splitext(project_file_name_ext)

try:
    with open(project_file) as f:
        config = yaml.safe_load(f)
except Exception as err:
    bcolors.color_print_error("CAN't open project file {}: {}".format(project_file, err))
    bcolors.color_print_error("Exiting")
    exit(101)

config_project_name = (
    project_file_name if "project_name" not in config else config["project_name"]
)
config_mapping_file = (
    config_project_name + "-mapping.xlsx"
    if "mapping_file" not in config
    else config["mapping_file"]
)
    
config_import_pcb_file = (
    config_project_name + ".csv"
    if "import_pcb_file" not in config
    else config["import_pcb_file"]
)

config_seq_file = os.path.join(project_dir, config_project_name + ".seq")
config_parts_file = os.path.join(project_dir, "part.dat")

if project_dir:
    if ':' not in config_mapping_file:
        config_mapping_file = os.path.join(project_dir, config_mapping_file)
    if ':' not in config_import_pcb_file:
        config_import_pcb_file = os.path.join(project_dir,config_import_pcb_file)

im = ImportPcb(config_project_name)

mapping = Mapping(config_mapping_file)
board_info = BoardInfo(
    GridTrays=config["grid_trays"],
    ChipFeeders=config["chip_feeders"],
    Rotate=config["board_rotate"],
    Xsize_mm=config["board_xsize_mm"] if "board_xsize_mm" in config else 0,
    Ysize_mm=config["board_ysize_mm"] if "board_ysize_mm" in config else 0,
    BiasRefX_mm=config["board_bias_ref_x_mm"],
    BiasRefY_mm=config["board_bias_ref_y_mm"],
    BiasCorrX_mm=config["board_bias_correction_x_mm"]
    if "board_bias_correction_x_mm" in config
    else 0,
    BiasCorrY_mm=config["board_bias_correction_y_mm"]
    if "board_bias_correction_y_mm" in config
    else 0,
    Name=config_project_name,
    Dumping_Xmm = config["board_dumping_x_mm"],
    Dumping_Ymm = config["board_dumping_y_mm"]
)

gen = Generator(board_info)

im.read_input(config_import_pcb_file)
im.generate_imported_values_mapping()
pcb_items = PcbItems(im.pcb_items)
changes_count = mapping.merge_mapping(im.imported_mapping)
if changes_count:
    bcolors.color_print(bcolors.WARNING+"Updating mapping"+bcolors.ENDC+"; the old one will be saved as .bak")
    mapping.save_mapping(im.imported_mapping)

pcb_parts = PcbParts()
if mapping.is_resolved():
    gen.generate(pcb_items, pcb_parts, im.imported_mapping, config_seq_file, config_parts_file)
    print("Files generated: {} {}".format(config_seq_file,config_parts_file))
else:
    bcolors.color_print_error("ERROR: Mapping IS NOT resolved, exiting")


#  sheet.cell(row=row,column=headers.index("Package")+1).number_format = '@'

# dims = {}
# for row in sheet.rows:
#    for cell in row:
#        if cell.value:
#            #dims[cell.column] = max((dims.get(cell.column, 0), len(str(cell.value))))
#            dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value))/2))
# for col, value in dims.items():
#    sheet.column_dimensions[col].width = value
