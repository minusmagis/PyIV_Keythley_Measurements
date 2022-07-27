import kclasses as kc
import pandas as pd

#Calibration
input('Connect the calibration cell and press enter')
keythley = kc.Keythley(24)
keythley.start()
calibration = kc.CalibrationCell(0.000484,0.158,keythley.detect_isc(10,1))
keythley.close()

print(calibration.irradiance)

cell_parameter_list = list()
inwards = input('What is the name of the cell? (END to stop measurement)\n')
while inwards != 'END':
    keythley = kc.Keythley(24)
    keythley.start()
    IV_curve = keythley.voltage_sweep_auto(100,0.1)
    keythley.close()

    # save data in txt:
    df_IV = pd.DataFrame(IV_curve)
    df_IV.to_csv(str(inwards)+'.txt', index=None, sep='\t')

    cell_parameters = kc.SolarCell(df_IV,calibration.irradiance,0.000484)
    cell_parameters.calculate_cell_parameters()
    buffer = {'Cell Name' : inwards}
    buffer.update(cell_parameters.cell_parameters)
    cell_parameter_list.append(buffer)

    inwards = input('What is the name of the cell? (END to stop measurement)\n')

full_treated_data = pd.DataFrame(cell_parameter_list)
full_treated_data.to_csv('Full treated data.txt', mode='a', index=None, sep='\t')
