from pcb_items import PcbItems, PcbPoint, PcbAssets
from pcb_parts import PcbParts, PartsItem
from collections import namedtuple
import math

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
    "Dumping_Xmm",
    "Dumping_Ymm"
]
BoardInfo = namedtuple("BoardInfo", BoardInfoFields)


class Generator:
    def __init__(self, board_info: BoardInfo) -> None:
        self.board_info: BoardInfo = board_info

    def generate(
        self, pcb_items: PcbItems, pcb_parts: list[PartsItem], mapping, seq_file_name, parts_file_name
    ) -> None:
        pcb_parts.build_list(mapping)
        self.__generate_parts(pcb_parts.Get(), parts_file_name)

        pcb_items.build_list(mapping)
        self.__generate_seq(pcb_items.Get(), seq_file_name)

    #        self.parts.generate()

    def __set_bias(self, bias: PcbPoint) -> None:
        bias = PcbPoint(
            X=bias.X + self.board_info.BiasCorrX_mm,
            Y=bias.Y + self.board_info.BiasCorrY_mm,
        )
        self.__bias = self.__rotate_pcb_cooordinates(bias)

    def __set_size(self, size: PcbPoint) -> None:
        self.__size = PcbPoint(
            X=self.board_info.Xsize_mm if self.board_info.Xsize_mm !=0 else size.X,
            Y=self.board_info.Ysize_mm if self.board_info.Ysize_mm !=0 else size.Y
        )

    def __adjust_pcb_coordinates(self, point: PcbPoint, bias: bool = False) -> PcbPoint:
        point = self.__rotate_pcb_cooordinates(point)
        if bias:
            point = PcbPoint(X=(point.X - self.__bias.X), Y=(point.Y - self.__bias.Y))
        point = self.__multiply_pcb_coordinates_for_ecm(point.X, point.Y)
        return point

    def __multiply_pcb_coordinates_for_ecm(self, X, Y) -> PcbPoint:
        point = PcbPoint(X=self.__toecm_100(X), Y=self.__toecm_100(Y))
        return point

    def __adjust_mount_point(self, point: PcbPoint, x_ofs:float, y_ofs:float, angle:float) -> PcbPoint:
        if x_ofs == 0 and y_ofs == 0:
            return point
        #Деталь надо сместиь по вектору установки на (x_ofs, x_ofs)
        #x'=x*cos(angle)-y*sin(angle);
        #y'=y*cos(angle)+x*sin(angle);
        angle = ((angle + 720) % 360) / 180 * math.pi #radians
        cosA = math.cos(angle)
        sinA = math.sin(angle)
        point = PcbPoint(X=point.X + (x_ofs* cosA - y_ofs * sinA),
                         Y=point.Y + (y_ofs* cosA + x_ofs * sinA))
        return point


    def __rotate_pcb_angle(self, angle: float, angle_rotation: float) -> float:
#Arotation - значение доворота детали, взятой из фидера, для установки на плату, расположенной так, 
# что 0:0 - в левом нижнем углу , "-90" - константа поворота, т.к. станок имеет 0:0 в левом верхнем углу (т.е. поворот на -90)
        angle += self.board_info.Rotate + int(angle_rotation) - 90
        if angle < 0:
            angle+= 720
        angle %= 360 
        return angle
    
    def __rotate_pcb_cooordinates(self, point: PcbPoint) -> PcbPoint:
        if self.board_info.Rotate == 90:
            point = PcbPoint(Y=point.X, X=self.__size.Y - point.Y)
        elif self.board_info.Rotate == -90:
            point = PcbPoint(X=point.Y, Y=self.__size.X - point.X)
        return point

    def __generate_parts(self, pcb_parts: list[PartsItem], file_name) -> None:
        with open(file_name, "wt") as f:
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

    def __toecm_100(self, value) -> int:
        return int(round(value * 100,0))
    
    def __generate_seq(self, pcb_assets: PcbAssets, file_name) -> None:
        self.__set_size(pcb_assets.Size) # order of these calls is important!
        self.__set_bias(pcb_assets.Bias)

        with open(file_name, "wt") as f:
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
                    len(pcb_assets.Items) + len(pcb_assets.Feducial),
                    0,
                    self.board_info.GridTrays,
                    self.board_info.ChipFeeders,
                )
            )
            point = self.__multiply_pcb_coordinates_for_ecm(
                        self.__bias.X + self.board_info.BiasRefX_mm,
                        self.__bias.Y + self.board_info.BiasRefY_mm
            )

            s.append(" {}: {}: 500: 500:  X {}Y {}AR".format(
                self. __toecm_100(self.board_info.Dumping_Xmm), 
                self. __toecm_100(self.board_info.Dumping_Ymm), 
                point.X, point.Y))

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
                if item.Fdr >= 999:
                    feeder = 48
                    ignore = '*'
                else:
                    feeder = item.Fdr
                    ignore = ''
                
                point = self.__adjust_pcb_coordinates(
                    self.__adjust_mount_point(item.Point, item.Xofs, item.Yofs, item.A),
                    pcb_assets.Bias
                )
                angle = self. __toecm_100(self.__rotate_pcb_angle(item.A, item.Arot))
                s.append(
                    "{0[Pt]}: {0[Strk]}: {0[Ind]}:0:0:{3}1:{0[H]}:F {4}X {1[X]}Y {1[Y]}A {2}R{0[Remark]}".format(
                        item._asdict(), point._asdict(), angle, ignore, feeder
                    )
                )

            f.writelines("\n".join(s))
