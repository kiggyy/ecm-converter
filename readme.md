Igor Ku, [04/07/2024 13:44]
в каталоге файла yaml. создаются файлы:

<name>.seq
<name>-mapping.xlsx
part.dat
где <name> - имя файла.yaml, если другое не задано в YAML конфиге

При первом запуске создается mapping файл, в котором далее только добавляются или удаляются строчки, прочее не меняется
Если mapping будет обновляться, делается .bak копия

открываешь mapping
устанавливаешь 
Feeder
Arot
Nz
Уточняешь PartRemark (SOP, CHI, QFP)

Параметры
Afed и Strk нужны для генерации файлов фидеров (TAP, FED, TRY) , но пока они не генерятся :)

Igor Ku, [04/07/2024 18:44]
Параметры YAML файла
Поля закомментаренные # - не обязательны

#name: GoodProject # Имя проекта. Если не задан, берется имя файла .yaml, далее используется как <name>
#mapping_file: optmappin1.xls   # Имя mapping-файла. Если не задан - <name> + "-mapping.xlsx" 
#import_pcb_file: UMTP04(11)CPU.csv # Имя csv для процессинга. Если не задан - <name> + ".csv" 
board_rotate: 90 #поворот платы на установщике (+90 - 0,0 в 1м квадранте, -90 - в третьем, 0 - во втором
#board_xsize_mm: 48 #размер платы (X, Y ниже), если не задан - берется из CSV
#board_ysize_mm: 43.5
board_bias_ref_x_mm: 28      # коррекция точки BIAS на установщике
board_bias_ref_y_mm: 68.75 # коррекция точки BIAS на установщике
board_bias_correction_x_mm: -1  # коррекция точки BIAS на плате (1 мм от центра)
board_bias_correction_y_mm: -1  # коррекция точки BIAS на плате (1 мм от центра)
grid_trays: 6  # число trays
chip_feeders: 6 # число chip feeders
