import sys
import time
import random
import os
import datetime

from serialport import *
serial = None

serialPortName = "/dev/tty.SLAB_USBtoUART"

def doELMCmd( cmd ):
    caret = serial.doCommandResponse( cmd, ">", 5 )
    assert caret != None #make sure it worked
    val = caret[0:-1]
    return val

#according to the formulate from here: http://en.wikipedia.org/wiki/OBD-II_PIDs#Mode_01
#MAF is actually ((A*256)+B) / 100
#where A is first 2 bytes and B is second 2 bytes
def convertMAF( mafInput ):
    out = 0

    #make sure we have enough characters - expect in 4 as we use them below
    assert len(mafInput) >= 4

    A = int(mafInput[0:2], 16)
    B = int(mafInput[2:4], 16)

    #the formula
    out_float = (float(A) * 256 + B) / 100

    return out_float

def parseResponse( response, processFunction ):
    value = response.replace( ' ', '' ) #replace the spaces with nothing
    value = value[4:] #strip off the header that was passed in
    out = processFunction( value )
    return out


def main():

    print "starting ODB test"

    global serial
    serial = SerialPort( serialPortName, 38400, "\r\n", verbose=False ) # <<<< change the verbose flag to True to get a full stream out

    #get the version
    ver = doELMCmd( "ATI" )
    print "ELMVersion:", ver

    #turn echo off (for OBD passthrough)
    doELMCmd( "ATE" + "0" )

    #auto determine vehicle protocol
    protocol = doELMCmd( "ATSP0" )
    print "Protocol:", protocol

    #query supports PIDS in mode 0
    mode0 = doELMCmd( "0100" )
    print "Mode 01 PIDS", mode0

    #without looking at the supported PID list above, lets read the current MAF
    #really we should check if this is supported...
    mass_airflow_sensor_raw = doELMCmd( "0110" )

    print "Raw Response from MAF:", mass_airflow_sensor_raw

    #process the response string
    #parseResponse takes in a result from the ELM 327 command and passes in a function to convert the data format
    maf = parseResponse( mass_airflow_sensor_raw, convertMAF )
    print "MAF:", maf

    #read the voltage of the battery
    voltage = doELMCmd( "ATRV" )
    v = float(voltage[0:-1]) #convert to a float
    print "Voltage:", v


#the following code starts up the program above.
#it also closes the serial port down (for if not closed, the program won't exit..)
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print e

    if serial != None:
        serial.shutdown()

    sys.exit(0)