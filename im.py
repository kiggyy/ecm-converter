import sys
from import_pcb import ImportPcb
from mapping import Mapping
from generator_ecm import GeneratorECM
from generator_zb import GeneratorZB
from pcb_items import PcbItems
from pcb_parts import PcbParts
from bcolors import bcolors
from project_config import build_project_context

context = build_project_context(sys.argv[-1])

im = ImportPcb(context.project_name)

mapping = Mapping(context.mapping_file, board_info=context.board_info)

gen_ecm = GeneratorECM(context.board_info)
gen_zb = GeneratorZB(context.board_info)

im.read_input(context.import_pcb_file)
im.generate_imported_values_mapping()
pcb_items = PcbItems(im.pcb_items)
changes_count = mapping.merge_mapping(im.imported_mapping)
if changes_count:
    bcolors.color_print(bcolors.WARNING+"Updating mapping"+bcolors.ENDC+"; the old one will be saved as .bak")
    mapping.save_mapping(im.imported_mapping)

pcb_parts = PcbParts()
if mapping.is_resolved():
    gen_ecm.generate(pcb_items, pcb_parts, im.imported_mapping, context.seq_file, context.parts_file)
    gen_zb.generate(pcb_items, pcb_parts, im.imported_mapping, context.zb_csv_file, context.parts_file)
    print("Files generated: {} {}".format(context.seq_file,context.parts_file))
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
