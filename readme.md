Igor Ku, [04/07/2024 13:44]
� �������� ����� yaml. ��������� �����:

<name>.seq
<name>-mapping.xlsx
part.dat
��� <name> - ��� �����.yaml, ���� ������ �� ������ � YAML �������

��� ������ ������� ��������� mapping ����, � ������� ����� ������ ����������� ��� ��������� �������, ������ �� ��������
���� mapping ����� �����������, �������� .bak �����

���������� mapping
�������������� 
Feeder
Arot
Nz
��������� PartRemark (SOP, CHI, QFP)

���������
Afed � Strk ����� ��� ��������� ������ ������� (TAP, FED, TRY) , �� ���� ��� �� ��������� :)

Igor Ku, [04/07/2024 18:44]
��������� YAML �����
���� ���������������� # - �� �����������

#name: GoodProject # ��� �������. ���� �� �����, ������� ��� ����� .yaml, ����� ������������ ��� <name>
#mapping_file: optmappin1.xls   # ��� mapping-�����. ���� �� ����� - <name> + "-mapping.xlsx" 
#import_pcb_file: UMTP04(11)CPU.csv # ��� csv ��� �����������. ���� �� ����� - <name> + ".csv" 
board_rotate: 90 #������� ����� �� ����������� (+90 - 0,0 � 1� ���������, -90 - � �������, 0 - �� ������
#board_xsize_mm: 48 #������ ����� (X, Y ����), ���� �� ����� - ������� �� CSV
#board_ysize_mm: 43.5
board_bias_ref_x_mm: 28      # ��������� ����� BIAS �� �����������
board_bias_ref_y_mm: 68.75 # ��������� ����� BIAS �� �����������
board_bias_correction_x_mm: -1  # ��������� ����� BIAS �� ����� (1 �� �� ������)
board_bias_correction_y_mm: -1  # ��������� ����� BIAS �� ����� (1 �� �� ������)
grid_trays: 6  # ����� trays
chip_feeders: 6 # ����� chip feeders
