from pcb_items import PcbItems, PcbPoint, PcbAssets
from pcb_parts import PcbParts, PartsItem
from collections import namedtuple
from generator_ecm import BoardInfo
import math

class GeneratorZB:
    def __init__(self, board_info: BoardInfo) -> None:
        self.board_info: BoardInfo = board_info
        self.corr = PcbPoint(1,1)

    def generate(
        self, pcb_items: PcbItems, pcb_parts: list[PartsItem], mapping, csv_file_name, parts_file_name
    ) -> None:

        pcb_items.build_list(mapping, "zb")
        self.__generate_csv(pcb_items.Get(), csv_file_name)

    #        self.parts.generate()

    def __adjust_pcb_coordinates(self, point: PcbPoint, bias: bool = False) -> PcbPoint:
        point = PcbPoint( point.Y, -point.X) #adjust Y
        return point

    def __generate_csv(self, pcb_assets: PcbAssets, file_name) -> None:

        with open(file_name, "wt") as f:
#Designator,Footprint,Mid X,Mid Y,Ref X,Ref Y,Pad X,Pad Y,Layer,Rotation,Comment
            s = []
            s.append("Designator,Footprint,Mid X,Mid Y,Ref X,Ref Y,Pad X,Pad Y,Layer,Rotation,Comment"            )
            for item in pcb_assets.Feducial:
                point: PcbPoint = self.__adjust_pcb_coordinates(
                    item.Point, pcb_assets.Bias
                )
                s.append(
                    "{0[Remark]},FDR,{1[X]},{1[Y]},0,0,0,0,T,0,FED".format(
                        item._asdict(), point._asdict()
                    )
                )

            items = sorted(pcb_assets.Items, key = lambda k: k.Nzl * 10000 + k.Fdr)

            for item in items:
                if item.Fdr >= 999:
                    continue

                point = self.__adjust_pcb_coordinates(item.Point)
                s.append(
                    "\"{0[Designator]}\",\"{0[Footprint]}\", {1[X]},{1[Y]},0,0,0,0,T,{0[A]},\"{0[Value]}\"".format(
                        item._asdict(), point._asdict()
                    )
                )

            f.writelines("\n".join(s))
