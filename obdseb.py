import sys
import time
import random
import os
import datetime
import csv

from serialport import *
serial = None

# Check the OS running
if os.name == 'nt':
    #windows SERIAL
    serialPortName = raw_input("Write the name of the Port you connected the ELM327 (ex: COM4): ")
else:
    #Linux SERIAL
    serialPortName = "/dev/tty.SLAB_USBtoUART"
    
# PID Variables declaration
HYBBAT = "015B"     #Hybrid battery pack remaining life (%)
RPM = "010C"          #Engine RPM
VOLTAGE = "ATRV"  #Voltage
COOL = "0105"       #Engine Coolant Temp (C)
FLI = "012F"           #Fuel Level Input (%)
SPEED = "010D"     #Speed (m/h)
MAF = "0110"         #Air flow rate
TESTART= "011F"    #Run time since engine start (sec)

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
    
#RPM is actually ((A*256)+B) / 4    
def convertRPM( rpmInput ):
    out = 0
    #make sure we have enough characters - expect in 4 as we use them below
    assert len(rpmInput) >= 4
    A = int(rpmInput[0:2], 16)
    B = int(rpmInput[2:4], 16)
    #the formula
    out_float = (A * 256 + B) / 4
    return out_float

#Testart is actually ((A*256)+B)    
def convertTESTART( testartInput ):
    out = 0
    #make sure we have enough characters - expect in 4 as we use them below
    assert len(testartInput) >= 4
    A = int(testartInput[0:2], 16)
    B = int(testartInput[2:4], 16)
    #the formula
    out_float = (float(A) * 256 + B)
    return out_float

#Get only the A data regarding the wiki formula (first 2 bytes)   
def convertDATA( dataInput ):
    out = 0
    A = int(dataInput[0:2], 16)
    return A

def parseResponse( response, processFunction ):
    value = response.replace( ' ', '' ) #replace the spaces with nothing
    value = value[4:] #strip off the header that was passed in
    out = processFunction( value )
    return out

def main():
    hexdigits = "0123456789ABCDEF " #value to check if the data received is an error message or hexadecimal
    deltatest = 0 #variable to test if engine is still ON, comparing time engine started data
    testart2 = 0 #variable used in deltatest to compare with testart
    global serial
    serial = SerialPort( serialPortName, 38400, "\r\n", verbose=False ) # <<<< change the verbose flag to True to get a full stream out

    #turn echo off (for OBD passthrough)
    doELMCmd( "ATE" + "0" )
    
    #Instructions
    print "\nPress Ctrl+C to exit the Program"
    print "Make sure ignition is ON when running this Test"
    print "\nEnter the title of the csv file you want to create"
    title = raw_input("Do not use any special character like \ : * ? . > : ")
      
    print "\nStarting ODB test"
    
    with open(title + '.csv', 'ab') as obdlog:
        writer = csv.writer(obdlog)
        #writing values names in CSV file
        writer.writerow(["Voltage:", "Hybrid battery pack remaining life (%):","Engine Coolant Temp (C):","Fuel Level Input (%):","RPM:","Speed (m/h):","MPG:","Run time since engine start (sec):"])
        
        while True:
            #read RPM
            rpm = doELMCmd( RPM )
            if all(c in hexdigits for c in rpm):        #test if rpm is hexa or an error message
                rpm = parseResponse( rpm, convertRPM )
            else:
                rpm = 0
                
            # Read Run time since engine start
            testart =  doELMCmd( TESTART )
            if all(c in hexdigits for c in testart):
                testart = parseResponse( testart, convertTESTART )
                deltatest = testart - testart2 #deltatest = 0 means engine is off
                testart2 = testart

			#Waiting ignition/engine ON to start recording data
            if rpm or (testart != 0 and testart != 'NO DATA' and deltatest != 0): #on hybrid car, if engine ON :rpm could be 0, but testart should not. Deltatest created because sometimes testart is not going back to 0 if car is OFF
                #read the voltage of the battery
                voltage = doELMCmd( VOLTAGE )
                v = float(voltage[0:-1]) #convert to a float
                print "\nVoltage:", v
                print "Run time since engine start (sec):", testart
                print "RPM:", rpm
                                           
                #read Hybrid battery pack remaining life
                hybbat = doELMCmd( HYBBAT )
                if all(c in hexdigits for c in hybbat): 
                    hybbat = parseResponse( hybbat, convertDATA )
                    hybbat = float(hybbat)*100/255
                    hybbat = round (hybbat,2)
                print "Hybrid battery pack remaining life (%):",hybbat                    
                    
                #read engine coolant Temperature
                cool = doELMCmd( COOL )
                if all(c in hexdigits for c in cool): 
                    cool = parseResponse( cool, convertDATA )
                    cool = cool - 40
                print "Engine Coolant Temp (C):", cool
                    
                #read Fuel Level Input
                fli = doELMCmd( FLI )
                if all(c in hexdigits for c in fli): 
                    fli = parseResponse( fli, convertDATA )
                    fli = fli * 100 / 255
                print "Fuel Level Input (%):", fli
                    
                #read Speed
                speed = doELMCmd( SPEED )
                if all(c in hexdigits for c in speed): 
                    kph = parseResponse( speed, convertDATA )
                    mph = kph * 0.6214
                    mph = round (mph,2)
                else:
                    mph = speed
                print "Speed mph:", mph
                    
                #read the current MAF
                maf = doELMCmd( MAF )
                if all(c in hexdigits for c in maf) and all(c in hexdigits for c in speed):                
                    #process the response string
                    #parseResponse takes in a result from the ELM 327 command and passes in a function to convert the data format
                    maf = parseResponse( maf, convertMAF )
                    mpg = 7.107 * kph / maf
                    mpg = round (mpg,2)
                else:
                    mpg = maf
                print "MPG:", mpg                    
                    
                #writing values in CSV file
                writer.writerow([v, hybbat, cool, fli, rpm, mph, mpg, testart])
                
            else:
                print '\rAWAITING IGNITION ON...',

#the following code starts up the program above.
#it also closes the serial port down (for if not closed, the program won't exit..)
if __name__ == "__main__":
    try:
        main()
        
    except KeyboardInterrupt:
        print "\nProgram Interrupted"
    
    except Exception as e:
        print e

    if serial != None:
        serial.shutdown()

    sys.exit(0)