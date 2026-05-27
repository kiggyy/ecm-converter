import os
from collections import namedtuple

import yaml

from bcolors import bcolors
from generator_ecm import BoardInfo


ProjectContextFields = [
    "config",
    "project_name",
    "project_dir",
    "mapping_file",
    "import_pcb_file",
    "seq_file",
    "zb_csv_file",
    "parts_file",
    "board_info",
]
ProjectContext = namedtuple("ProjectContext", ProjectContextFields)


def read_config(file_name):
    try:
        with open(file_name) as f:
            return yaml.safe_load(f)
    except Exception as err:
        bcolors.color_print_error("CAN't open project file {}: {}".format(file_name, err))
        bcolors.color_print_error("Exiting")
        exit(101)


def build_project_context(project_file):
    project_dir, project_file_name_ext = os.path.split(project_file)
    upper_dir = os.path.abspath(os.path.join(project_dir, ".."))
    project_file_name, _ = os.path.splitext(project_file_name_ext)

    config = read_config(project_file)
    if "common" in config:
        common_config_file = config["common"].strip()
        if common_config_file.lower() == "up":
            common_config_file = os.path.join(upper_dir, "common.yaml")
        config_common = read_config(common_config_file)
        if "mapping_file" in config_common:
            config_common["mapping_file"] = os.path.join(upper_dir, config_common["mapping_file"])

        config = config_common | config

    project_name = project_file_name if "project_name" not in config else config["project_name"]
    mapping_file = config["mapping_file"] if "mapping_file" in config else project_name + "-mapping.xlsx"
    import_pcb_file = config["import_pcb_file"] if "import_pcb_file" in config else project_name + ".csv"

    seq_file = os.path.join(project_dir, project_name + ".seq")
    zb_csv_file = os.path.join(project_dir, project_name + "_zb.csv")
    parts_file = os.path.join(project_dir, "part.dat")

    if project_dir:
        if ":" not in mapping_file:
            mapping_file = os.path.join(project_dir, mapping_file)
        if ":" not in import_pcb_file:
            import_pcb_file = os.path.join(project_dir, import_pcb_file)

    board_info = BoardInfo(
        GridTrays=config["grid_trays"],
        ChipFeeders=config["chip_feeders"],
        Rotate=config["board_rotate"] if "board_rotate" in config else 0,
        RotateZb=config["board_rotate_zb"] if "board_rotate_zb" in config else 0,
        Aliases=config["aliases"] if "aliases" in config else {},
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
        Name=project_name,
        Dumping_Xmm=config["board_dumping_x_mm"],
        Dumping_Ymm=config["board_dumping_y_mm"],
        CorrRep1_Xmm=config["corr_rep1_x"] if "corr_rep1_x" in config else 0,
        CorrRep1_Ymm=config["corr_rep1_y"] if "corr_rep1_y" in config else 0,
        CorrRep2_Xmm=config["corr_rep2_x"] if "corr_rep2_x" in config else 0,
        CorrRep2_Ymm=config["corr_rep2_y"] if "corr_rep2_y" in config else 0,
        CorrRep_Xcoeff=config["coef_rep_x"] if "coef_rep_x" in config else 0,
        CorrRep_Ycoeff=config["coef_rep_y"] if "coef_rep_y" in config else 0,
    )

    return ProjectContext(
        config=config,
        project_name=project_name,
        project_dir=project_dir,
        mapping_file=mapping_file,
        import_pcb_file=import_pcb_file,
        seq_file=seq_file,
        zb_csv_file=zb_csv_file,
        parts_file=parts_file,
        board_info=board_info,
    )
