from pcb_items import PcbItems, PcbPoint, PcbAssets
from pcb_parts import PcbParts, PartsItem
from collections import namedtuple

BoardInfoFields = [
    "Rotate",
    "Xsize_mm",
    "Ysize_mm",
    "GridTrays",
    "ChipFeeders",
    "Name",
    "BiasRefX_mm",
    "BiasRefY_mm",
    "BiasCorrX_mm",
    "BiasCorrY_mm",
]
BoardInfo = namedtuple("BoardInfo", BoardInfoFields)


class Generator:
    def __init__(self, board_info: BoardInfo) -> None:
        self.board_info: BoardInfo = board_info

    def generate(
        self, pcb_items: PcbItems, pcb_parts: list[PartsItem], mapping
    ) -> None:
        pcb_parts.build_list(mapping)
        self.__generate_parts(pcb_parts.Get())

        pcb_items.build_list(mapping)
        self.__generate_seq(pcb_items.Get())

    #        self.parts.generate()

    def __set_bias(self, bias: PcbPoint) -> None:
        bias = PcbPoint(
            X=bias.X + self.board_info.BiasCorrX_mm,
            Y=bias.Y + self.board_info.BiasCorrY_mm,
        )
        self.__bias = self.__rotate_pcb_cooordinates(bias)

    def __adjust_pcb_coordinates(self, point: PcbPoint, bias: bool = False) -> PcbPoint:
        point = self.__rotate_pcb_cooordinates(point)
        if bias:
            point = PcbPoint(X=(point.X - self.__bias.X), Y=(point.Y - self.__bias.Y))
        point = PcbPoint(X=int(point.X * 100), Y=int(point.Y * 100))
        return point

    def __rotate_pcb_cooordinates(self, point: PcbPoint) -> PcbPoint:
        if self.board_info.Rotate == -90:
            point = PcbPoint(Y=point.X, X=self.board_info.Ysize_mm - point.Y)
        return point

    def __generate_parts(self, pcb_parts: list[PartsItem]) -> None:
        with open("part.dat", "wt") as f:
            s = []
            # 68:0:0:0:0:6:5.8:0:0:2:1:RQFPIRL120N70

            s.append("{}:0:0:0:0:0:0:0:0:0:0:R".format(len(pcb_parts)))

            for item in pcb_parts:
                # 2:0:0:1:0:3.5:1.8:0:0:0.7:1:RQFPCHI1C1 70
                s.append(
                    "{0[Nzl]}:{0[h1]}:{0[h2]}:{0[h3]}:{0[h4]}:{0[X]}:{0[Y]}:{0[Pt]}:{0[W]}:{0[Thk]}:{0[Lv]}:R{0[Remark]}".format(
                        item._asdict()
                    )
                )

            f.writelines("\n".join(s))

    def __generate_seq(self, pcb_assets: PcbAssets) -> None:
        self.__set_bias(pcb_assets.Bias)

        with open(self.board_info.Name + ".seq", "wt") as f:
            # header
            #  70: 0: 48: 1F 8X 6Y 2A 68R
            # cnt
            #      boards - count in project
            #         tape cassete
            # 		    grid trays
            # 			   chip feeders
            # 			      bits used
            # 				     Positioners
            # 					    ??
            # 500: 22000: 500: 500:X 5399Y 7991AR
            #                        bias  bias

            s = []
            s.append(
                " {}: {}: 48: {}F {}X 6Y 2A 68R".format(
                    len(pcb_assets.Items),
                    0,
                    self.board_info.GridTrays,
                    self.board_info.ChipFeeders,
                )
            )
            point = PcbPoint(
                X=int(self.__bias.X + self.board_info.BiasRefX_mm) * 100,
                Y=int(self.__bias.Y + self.board_info.BiasRefY_mm) * 100,
            )
            s.append(" 500: 500: 500: 500:  X {}Y {}AR".format(point.X, point.Y))

            for item in pcb_assets.Feducial:
                # 1:::::1::F 271X 306Y 12969A 0RRep.1
                point: PcbPoint = self.__adjust_pcb_coordinates(
                    item.Point, pcb_assets.Bias
                )
                s.append(
                    "1:::::1::F {0[Fdr]}X {1[X]}Y {1[Y]}A 0R{0[Remark]}".format(
                        item._asdict(), point._asdict()
                    )
                )

            for item in pcb_assets.Items:
                point: PcbPoint = self.__adjust_pcb_coordinates(
                    item.Point, pcb_assets.Bias
                )
                s.append(
                    "{0[Pt]}: {0[Strk]}: {0[Ind]}:0:0:1:{0[H]}:F {0[Fdr]}X {1[X]}Y {1[Y]}A {0[A]}R{0[Remark]}".format(
                        item._asdict(), point._asdict()
                    )
                )

            f.writelines("\n".join(s))
