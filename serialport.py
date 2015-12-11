import sys, os, time
import serial
import serial.rfc2217
import threading

# This is a class to handle the serial port comms.
# It supports 2 main API types:
#  - Always on logging to a file
#  - Command / response request from a host (including filtering the received data to look for a specific string)
# It does not support:
#  - random data from the device being received and understood


class SerialPort():
    def __init__( self, uartPort, baudrate, lineEndings, caseSensitive=False, verbose=False ):
        if verbose:
            print "SerialPort: ", uartPort, str(baudrate)
        try:
            self.serial_port = serial.Serial(port=uartPort, baudrate=baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1, xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=1 )
            self.dummyFile = False
        except Exception as e:
            print e
            #try as a normal file instead
            self.serial_port = open(uartPort, "rw")
            self.dummyFile = True
            print "Using dummy file"
            pass
        self.lineEndings = lineEndings
        self.event = threading.Event()
        self.event.clear()
        self.responseFilter = None
        self.readLine = ""
        self.verbose = verbose
        self.caseSensitive = caseSensitive

        #start the thread automatically
        def read_from_port(self, ser):
            exitThread = False
            readLine = ""
            while not exitThread:
                try:
                    #print "logLine:",
                    self.readLine = ser.readline()
                    logLine = self.readLine
                    #print logLine
                    if len(self.readLine) != 0:
                        if self.caseSensitive:
                            self.readLine = self.readLine.upper().lstrip().rstrip()
                        self.readLine = self.readLine.lstrip().rstrip()
                        lines = self.readLine.splitlines()
                        for l in lines:
                            if( self.verbose ):
                                print "R:", l
                            if( len(l) ):

                                self.response += l

                                if( self.responseFilter != None and l.find(self.responseFilter) != -1):

                                    #trigger the event!
                                    self.event.set()

                except serial.SerialException:
                    exitThread = True
            #print "SerialPort Thread exit!"

        if self.serial_port != None:
            if self.dummyFile == False:
                self.thread = threading.Thread(target=read_from_port, args=(self, self.serial_port))
                self.thread.start()
            #print "Created thread: ", self.thread, self.serial_port
        else:
            raise Exception("Failed to connect to serial port: ", uartPort)

    def shutdown(self):
        #print "shutDown!: ", self.thread, self.serial_port

        if self.serial_port != None:
            self.serial_port.close()
            self.serial_port = None
            if( self.dummyFile == False):
                self.thread.join()

    def __del__( self ):
        self.shutdown()


    #command / pair
    #responseFilter is a very basic strstr
    #returns the response or throws an exception
    def doCommandResponse( self, cmd, responseFilter, timeout ):
        self.responseFilter = responseFilter
        self.response = ""

        if self.dummyFile == False:

            if( self.verbose ):
                print "W:", cmd

            self.serial_port.write(cmd)
            self.serial_port.write(self.lineEndings)
            ok = self.event.wait( timeout )
            self.event.clear()
            if ok:
                return self.response
            else:
                return None
        else:
            return None

    #send a blind command
    def sendCommand(self, cmd):
        if self.dummyFile == False:
            self.serial_port.write(cmd)
            self.serial_port.write(self.lineEndings)

