# Python-OBD2
Analyse PIDs sur OBD2

obd.py is the original file

obdseb.py is the file modified :

It is the python code I wrote to collect and transfer data from a car to a CSV file.
You have to launch obdseb.py from the same folder where serialport.py is.

It should work on both Windows and Mac platform.
If you run it under windows, you will have to enter the name of the serial port where you plugged the ELM327 (like 'COM4').
Then, you will be prompted to enter a name for the csv file you want to create (like 'Test1').

The OBD Test will start then.
The data collected will be printed on the console and recorded at the same time in the csv file.

If the ignition is not ON, it should not record anything and display :
"AWAITING IGNITION ON..."

If the PID is not supported, it should be written "NO DATA" regarding the value.
If there is some CAN issue, it will be displayed : "CAN ERROR".

Here is an exemple of the log that I obtainned with a Ford C-max :

Voltage:
Hybrid battery pack remaining life (%):	Engine Coolant Temp (C):	Fuel Level Input (%):	RPM:	Speed (m/h):	MPG:	Run time since engine start (sec):
14.1	14.9	68	10	1160	0	0	1279
14	14.9	69	5	1162	2.49	3.99	1289
14.1	14.9	70	8	1160	9.32	7.74	1298
14	15.29	72	9	1497	11.19	9.26	1308
14	16.08	74	9	1462	10.56	8.27	1318
14	16.47	75	14	1458	3.73	60.06	1328
14	16.08	78	17	0	0	0	1338

