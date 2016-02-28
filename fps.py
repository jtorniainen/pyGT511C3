#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Originally
Created on 21/03/2014

@author: Jean Machuca <correojean@gmail.com> @jeanmachuca

Modified on 28/02/2016 by github.com/jtorniainen
'''

import os
import serial
from serial.tools import list_ports
import binascii
import time


def debug_msg(message, tag='Generic'):
    """
    Timestampped debug messages.
    """
    print('[{}][{}] {}'.format(time.asctime()[11:-5], tag, message))


def serial_ports():
    '''
    Returns a generator for all available serial ports
    '''
    if os.name == 'nt':
        # windows
        _comports = [port for port in list_ports.comports()]
        if _comports.__len__() > 0:
            _serial_ports = [p for p in _comports[0]]
        else:
            _serial_ports = []
    else:
        # unix
        _serial_ports = [port[0] for port in list_ports.comports()]
    return _serial_ports


def devices(index=None):
    '''
    Devices list
    :param index if this param is not None, then returns the device name of
    the index in the list
    '''
    portList = [portName for portName in serial_ports()]
    return portList if index is None else portList[index]


class Packet:

    '''
        Generic Internal Packet Class
    '''
    COMMAND_START_CODE_1 = 0x55
    # Static byte to mark the beginning of a command packet    -    never
    # changes
    COMMAND_START_CODE_2 = 0xAA
    # Static byte to mark the beginning of a command packet    -    never
    # changes
    COMMAND_DEVICE_ID_1 = 0x01
    # Device ID Byte 1 (lesser byte)                            -
    # theoretically never changes
    COMMAND_DEVICE_ID_2 = 0x00
    # Device ID Byte 2 (greater byte)                            -
    # theoretically never changes

    def GetHighByte(self, w):
        '''
        Returns the high byte from a word
        '''
        return (w >> 8) & 0x00FF

    def GetLowByte(self, w):
        '''
        Returns the low byte from a word
        '''
        return w & 0x00FF

    def CalculateCheckSum(self, bytearr):
        return sum(map(ord, bytes(bytearr)))

    def serializeToSend(self, bytearr):
        return ' '.join(binascii.hexlify(ch) for ch in bytes(bytearr))


class Command_Packet(Packet):

    '''
        Command Packet Class
        Used to build the serial message
    '''

    command = bytearray(2)
    cmd = ''
    commands = {
        # Default value for enum. Scanner will return error if sent this.
        'NotSet': 0x00,
        'Open': 0x01,        # Open Initialization
        'Close': 0x02,        # Close Termination
        # UsbInternalCheck Check if the connected USB device is valid
        'UsbInternalCheck': 0x03,
        'ChangeBaudrate': 0x04,        # ChangeBaudrate Change UART baud rate
        # SetIAPMode Enter IAP Mode In this mode, FW Upgrade is available
        'SetIAPMode': 0x05,
        'CmosLed': 0x12,        # CmosLed Control CMOS LED
        'GetEnrollCount': 0x20,        # Get enrolled fingerprint count
        # Check whether the specified ID is already enrolled
        'CheckEnrolled': 0x21,
        'EnrollStart': 0x22,        # Start an enrollment
        'Enroll1': 0x23,        # Make 1st template for an enrollment
        'Enroll2': 0x24,        # Make 2nd template for an enrollment
        # Make 3rd template for an enrollment, merge three templates into one
        # template, save merged template to the database
        'Enroll3': 0x25,
        # Check if a finger is placed on the sensor
        'IsPressFinger': 0x26,
        'DeleteID': 0x40,        # Delete the fingerprint with the specified ID
        'DeleteAll': 0x41,        # Delete all fingerprints from the database
        # Verification of the capture fingerprint image with the specified ID
        'Verify1_1': 0x50,
        # Identification of the capture fingerprint image with the database
        'Identify1_N': 0x51,
        # Verification of a fingerprint template with the specified ID
        'VerifyTemplate1_1': 0x52,
        # Identification of a fingerprint template with the database
        'IdentifyTemplate1_N': 0x53,
        # Capture a fingerprint image(256x256) from the sensor
        'CaptureFinger': 0x60,
        'MakeTemplate': 0x61,        # Make template for transmission
        # Download the captured fingerprint image(256x256)
        'GetImage': 0x62,
        # Capture & Download raw fingerprint image(320x240)
        'GetRawImage': 0x63,
        'GetTemplate': 0x70,        # Download the template of the specified ID
        'SetTemplate': 0x71,        # Upload the template of the specified ID
        'GetDatabaseStart': 0x72,        # Start database download, obsolete
        'GetDatabaseEnd': 0x73,        # End database download, obsolete
        'UpgradeFirmware': 0x80,        # Not supported
        'UpgradeISOCDImage': 0x81,        # Not supported
        'Ack': 0x30,        # Acknowledge.
        'Nack': 0x31         # Non-acknowledge
        }

    def __init__(self, *args, **kwargs):
        '''
            Command Packet Constructor
        '''
        commandName = args[0]
        kwargs.setdefault('UseSerialDebug', True)
        self.UseSerialDebug = kwargs['UseSerialDebug']
        if self.UseSerialDebug:
            print 'Command: %s' % commandName
        self.cmd = self.commands[commandName]

    UseSerialDebug = True
    Parameter = bytearray(4)

    def GetPacketBytes(self):
        '''
        Returns the 12 bytes of the generated command packet
        remember to call delete on the returned array
        '''

        self.command[0] = self.GetLowByte(self.cmd)
        self.command[1] = self.GetHighByte(self.cmd)

        packetbytes = bytearray(12)
        packetbytes[0] = self.COMMAND_START_CODE_1
        packetbytes[1] = self.COMMAND_START_CODE_2
        packetbytes[2] = self.COMMAND_DEVICE_ID_1
        packetbytes[3] = self.COMMAND_DEVICE_ID_2
        packetbytes[4] = self.Parameter[0]
        packetbytes[5] = self.Parameter[1]
        packetbytes[6] = self.Parameter[2]
        packetbytes[7] = self.Parameter[3]
        packetbytes[8] = self.command[0]
        packetbytes[9] = self.command[1]
        chksum = self.CalculateCheckSum(packetbytes[0:9])
        packetbytes[10] = self.GetLowByte(chksum)
        packetbytes[11] = self.GetHighByte(chksum)

        return packetbytes

    def ParameterFromInt(self, i):
        '''
        Converts the int to bytes and puts them into the paramter array
        '''

        self.Parameter[0] = (i & 0x000000ff)
        self.Parameter[1] = (i & 0x0000ff00) >> 8
        self.Parameter[2] = (i & 0x00ff0000) >> 16
        self.Parameter[3] = (i & 0xff000000) >> 24


class Response_Packet(Packet):
    '''
        Response Packet Class
    '''
    errors = {
        'NO_ERROR': 0x0000,    # Default value. no error
        'NACK_TIMEOUT': 0x1001,    # Obsolete, capture timeout
        # Obsolete, Invalid serial baud rate
        'NACK_INVALID_BAUDRATE': 0x1002,
        'NACK_INVALID_POS': 0x1003,    # The specified ID is not between 0~199
        'NACK_IS_NOT_USED': 0x1004,    # The specified ID is not used
        'NACK_IS_ALREADY_USED': 0x1005,    # The specified ID is already used
        'NACK_COMM_ERR': 0x1006,    # Communication Error
        'NACK_VERIFY_FAILED': 0x1007,    # 1:1 Verification Failure
        'NACK_IDENTIFY_FAILED': 0x1008,    # 1:N Identification Failure
        'NACK_DB_IS_FULL': 0x1009,    # The database is full
        'NACK_DB_IS_EMPTY': 0x100A,    # The database is empty
        # Obsolete, Invalid order of the enrollment (The order was not as:
        # EnrollStart -> Enroll1 -> Enroll2 -> Enroll3)
        'NACK_TURN_ERR': 0x100B,
        'NACK_BAD_FINGER': 0x100C,    # Too bad fingerprint
        'NACK_ENROLL_FAILED': 0x100D,    # Enrollment Failure
        # The specified command is not supported
        'NACK_IS_NOT_SUPPORTED': 0x100E,
        # Device Error, especially if Crypto-Chip is trouble
        'NACK_DEV_ERR': 0x100F,
        # Obsolete, The capturing is canceled
        'NACK_CAPTURE_CANCELED': 0x1010,
        'NACK_INVALID_PARAM': 0x1011,    # Invalid parameter
        'NACK_FINGER_IS_NOT_PRESSED': 0x1012,    # Finger is not pressed
        'INVALID': 0XFFFF     # Used when parsing fails
        }

    def __init__(self, _buffer=None, UseSerialDebug=False):
        '''
        Creates and parses a response packet from the finger print scanner
        '''
        self.UseSerialDebug = UseSerialDebug

        if not (_buffer is None):
            self.RawBytes = _buffer
            self._lastBuffer = bytes(_buffer)
            if self.UseSerialDebug:
                debug_msg('Read: {}'.format(self.serializeToSend(_buffer)))
            if _buffer.__len__() >= 12:
                self.ACK = True if _buffer[8] == 0x30 else False
                self.ParameterBytes[0] = _buffer[4]
                self.ParameterBytes[1] = _buffer[5]
                self.ParameterBytes[2] = _buffer[6]
                self.ParameterBytes[3] = _buffer[7]
                self.ResponseBytes[0] = _buffer[8]
                self.ResponseBytes[1] = _buffer[9]
                self.Error = self.ParseFromBytes(
                    self.GetHighByte(
                        _buffer[5]), self.GetLowByte(
                        _buffer[4]))

    _lastBuffer = bytes()
    RawBytes = bytearray(12)
    ParameterBytes = bytearray(4)
    ResponseBytes = bytearray(2)
    ACK = False
    Error = None
    UseSerialDebug = True

    def ParseFromBytes(self, high, low):
        '''
        Parses bytes into one of the possible errors from the finger print
        scanner
        '''
        e = 'INVALID'
        if high == 0x01:
            if low in self.errors.values():
                errorIndex = self.errors.values().index(low)
                e = self.errors.keys()[errorIndex]
        return e

    def IntFromParameter(self):
        retval = 0
        retval = (retval << 8) + self.ParameterBytes[3]
        retval = (retval << 8) + self.ParameterBytes[2]
        retval = (retval << 8) + self.ParameterBytes[1]
        retval = (retval << 8) + self.ParameterBytes[0]
        return retval


class SerialCommander:

    '''
        Serializes the args to hex to send to serial port
    '''

    def __serialize_args_hex__(self, *arg, **kwargs):
        return bytes(bytearray([v for v in kwargs.values()]))

    def serializeToSend(self, bytearr):
        return ' '.join(binascii.hexlify(ch) for ch in bytes(bytearr))

    def unserializeFromRead(self, char_readed, bytearr):
        bytearr.append(char_readed)
        return bytearr


def connect(device_name=None, baud=None, timeout=None, is_com=True):
    _ser = None
    if device_name is None:
        device_name = DEVICE_NAME
    else:
        DEVICE_NAME = device_name
    if baud is None:
        baud = 9600
    if timeout is None:
        timeout = 10000
    if isFingerPrintConnected(is_com):
        try:
            _ser = serial.Serial(device_name, baudrate=baud, timeout=timeout)
            if not _ser.isOpen():
                _ser.open()
        except Exception as e:
            debug_msg('Cannot connect to device {}'.format(str(e)))
            pass
    return _ser


class FPS_GT511C3(SerialCommander):
    _serial = None
    _lastResponse = None
    _device_name = None
    _baud = None
    _timeout = None

    '''
    # Enables verbose debug output using hardware Serial
    '''
    UseSerialDebug = True

    def __init__(self, device_name=None, baud=None, timeout=None, is_com=True):
        '''
        Creates a new object to interface with the fingerprint scanner
        '''
        self._device_name = device_name
        self._baud = baud
        self._timeout = timeout
        self._serial = connect(device_name, baud, timeout, is_com=is_com)
        if self._serial:
            time.sleep(.1)
            self.Open()
        elif self.UseSerialDebug:
            debug_msg('Cannot connect to device {}'.format(self._device_name), 'FPS_GT511C3')

    def Open(self):
        '''
            Initialises the device and gets ready for commands
        '''
        self.ChangeBaudRate(BAUD)
        time.sleep(.1)
        cp = Command_Packet('Open', UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(1)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        del packetbytes
        return rp.ACK

    def Close(self):
        '''
             Does not actually do anything (according to the datasheet)
             I implemented open, so had to do closed too... lol
        '''
        cp = Command_Packet('Close', UseSerialDebug=self.UseSerialDebug)
        cp.Parameter[0] = 0x00
        cp.Parameter[1] = 0x00
        cp.Parameter[2] = 0x00
        cp.Parameter[3] = 0x00
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        if not self._serial is None:
            self._serial.close()
        del packetbytes
        return rp.ACK

    def SetLED(self, on=True):
        '''
             Turns on or off the LED backlight
             LED must be on to see fingerprints
             Parameter: true turns on the backlight, false turns it off
             Returns: True if successful, false if not
        '''
        cp = Command_Packet('CmosLed', UseSerialDebug=self.UseSerialDebug)
        cp.Parameter[0] = 0x01 if on else 0x00
        cp.Parameter[1] = 0x00
        cp.Parameter[2] = 0x00
        cp.Parameter[3] = 0x00
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.ACK
        del rp
        del packetbytes
        return retval

    def ChangeBaudRate(self, baud):
        '''
             Changes the baud rate of the connection
             Parameter: 9600 - 115200
             Returns: True if success, false if invalid baud
             NOTE: Untested (don't have a logic level changer and a voltage divider is too slow)
        '''
        retval = False
        if baud != self._serial.getBaudrate():
            cp = Command_Packet(
                'ChangeBaudrate',
                UseSerialDebug=self.UseSerialDebug)
            cp.ParameterFromInt(baud)
            packetbytes = cp.GetPacketBytes()
            self.SendCommand(packetbytes, 12)
            delay(0.5)
            rp = self.GetResponse()
            delay(0.5)
            retval = rp.ACK
            if retval:
                if self.UseSerialDebug:
                    debug_msg('Changing port baudrate')
                self._serial.close()
                BAUD = baud
                self._serial = connect(
                    self._device_name,
                    self._baud,
                    self._timeout)
            del rp
            del packetbytes
        return retval

    def GetEnrollCount(self):
        '''
             Gets the number of enrolled fingerprints
             Return: The total number of enrolled fingerprints
        '''
        cp = Command_Packet(
            'GetEnrollCount',
            UseSerialDebug=self.UseSerialDebug)
        cp.Parameter[0] = 0x00
        cp.Parameter[1] = 0x00
        cp.Parameter[2] = 0x00
        cp.Parameter[3] = 0x00
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.IntFromParameter()
        del rp
        del packetbytes
        return retval

    def CheckEnrolled(self, ID):
        '''
             checks to see if the ID number is in use or not
             Parameter: 0-199
             Return: True if the ID number is enrolled, false if not
        '''
        cp = Command_Packet(
            'CheckEnrolled',
            UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(ID)
        packetbytes = cp.GetPacketBytes()
        del cp
        self.SendCommand(packetbytes, 12)
        del packetbytes
        rp = self.GetResponse()
        retval = rp.ACK
        del rp
        return retval

    def EnrollStart(self, ID):
        '''
             Starts the Enrollment Process
             Parameter: 0-199
             Return:
                0 - ACK
                1 - Database is full
                2 - Invalid Position
                3 - Position(ID) is already used
        '''
        cp = Command_Packet('EnrollStart', UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(ID)
        packetbytes = cp.GetPacketBytes()
        del cp
        self.SendCommand(packetbytes, 12)
        del packetbytes
        rp = self.GetResponse()
        retval = 0
        if not rp.ACK:
            if rp.Error == rp.errors['NACK_DB_IS_FULL']:
                retval = 1
            elif rp.Error == rp.errors['NACK_INVALID_POS']:
                retval = 2
            elif rp.Error == rp.errors['NACK_IS_ALREADY_USED']:
                retval = 3
        del rp
        return retval

    def Enroll1(self):
        '''
             Gets the first scan of an enrollment
             Return:
                0 - ACK
                1 - Enroll Failed
                2 - Bad finger
                3 - ID in use
        '''
        cp = Command_Packet('Enroll1', UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        del cp
        self.SendCommand(packetbytes, 12)
        del packetbytes
        rp = self.GetResponse()
        retval = rp.IntFromParameter()
        retval = 3 if retval < 200 else 0
        if not rp.ACK:
            if rp.Error == rp.errors['NACK_ENROLL_FAILED']:
                retval = 1
            elif rp.Error == rp.errors['NACK_BAD_FINGER']:
                retval = 2
        return 0 if rp.ACK else retval

    def Enroll2(self):
        '''
             Gets the Second scan of an enrollment
             Return:
                0 - ACK
                1 - Enroll Failed
                2 - Bad finger
                3 - ID in use
        '''
        cp = Command_Packet('Enroll2', UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        del cp
        self.SendCommand(packetbytes, 12)
        del packetbytes
        rp = self.GetResponse()
        retval = rp.IntFromParameter()
        retval = 3 if retval < 200 else 0
        if not rp.ACK:
            if rp.Error == rp.errors['NACK_ENROLL_FAILED']:
                retval = 1
            elif rp.Error == rp.errors['NACK_BAD_FINGER']:
                retval = 2
        return 0 if rp.ACK else retval

    def Enroll3(self):
        '''
             Gets the Third scan of an enrollment
             Finishes Enrollment
             Return:
                0 - ACK
                1 - Enroll Failed
                2 - Bad finger
                3 - ID in use
        '''
        cp = Command_Packet('Enroll3', UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        del cp
        self.SendCommand(packetbytes, 12)
        del packetbytes
        rp = self.GetResponse()
        retval = rp.IntFromParameter()
        retval = 3 if retval < 200 else 0
        if not rp.ACK:
            if rp.Error == rp.errors['NACK_ENROLL_FAILED']:
                retval = 1
            elif rp.Error == rp.errors['NACK_BAD_FINGER']:
                retval = 2
        return 0 if rp.ACK else retval

    def IsPressFinger(self):
        '''
             Checks to see if a finger is pressed on the FPS
             Return: true if finger pressed, false if not
        '''
        cp = Command_Packet(
            'IsPressFinger',
            UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        pval = rp.ParameterBytes[0]
        pval += rp.ParameterBytes[1]
        pval += rp.ParameterBytes[2]
        pval += rp.ParameterBytes[3]
        retval = True if pval == 0 else False
        del rp
        del packetbytes
        del cp
        return retval

    def DeleteID(self, ID):
        '''
             Deletes the specified ID (enrollment) from the database
             Returns: true if successful, false if position invalid
        '''
        cp = Command_Packet('DeleteID', UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(ID)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.ACK
        del rp
        del packetbytes
        del cp
        return retval

    def DeleteAll(self):
        '''
             Deletes all IDs (enrollments) from the database
             Returns: true if successful, false if db is empty
        '''
        cp = Command_Packet('DeleteAll', UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.ACK
        del rp
        del packetbytes
        del cp
        return retval

    def Verify1_1(self, ID):
        '''
             Checks the currently pressed finger against a specific ID
             Parameter: 0-199 (id number to be checked)
             Returns:
                0 - Verified OK (the correct finger)
                1 - Invalid Position
                2 - ID is not in use
                3 - Verified FALSE (not the correct finger)
        '''
        cp = Command_Packet('Verify1_1', UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(ID)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = 0
        if not rp.ACK:
            if rp.Error == rp.errors['NACK_INVALID_POS']:
                retval = 1
            elif rp.Error == rp.errors['NACK_IS_NOT_USED']:
                retval = 2
            elif rp.Error == rp.errors['NACK_VERIFY_FAILED']:
                retval = 3
        del rp
        del packetbytes
        del cp
        return retval

    def Identify1_N(self):
        '''
             Checks the currently pressed finger against all enrolled fingerprints
             Returns:
                0-199: Verified against the specified ID (found, and here is the ID number)
                200: Failed to find the fingerprint in the database
        '''
        cp = Command_Packet('Identify1_N', UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.IntFromParameter()
        if retval > 200:
            retval = 200
        del rp
        del packetbytes
        del cp
        return retval

    def CaptureFinger(self, highquality=True):
        '''
             Captures the currently pressed finger into onboard ram
             Parameter: true for high quality image(slower), false for low quality image (faster)
             Generally, use high quality for enrollment, and low quality for verification/identification
             Returns: True if ok, false if no finger pressed
        '''
        cp = Command_Packet(
            'CaptureFinger',
            UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(1 if highquality else 0)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.ACK
        del rp
        del packetbytes
        del cp
        return retval

    def GetImage(self):
        '''
             Gets an image that is 258x202 (52116 bytes) and returns it in 407 Data_Packets
             Use StartDataDownload, and then GetNextDataPacket until done
             Returns: True (device confirming download starting)
        '''
        cp = Command_Packet('GetImage', UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.ACK
        return retval

    def GetRawImage(self):
        '''
             Gets an image that is qvga 160x120 (19200 bytes) and returns it in 150 Data_Packets
             Use StartDataDownload, and then GetNextDataPacket until done
             Returns: True (device confirming download starting)
             Not implemented due to memory restrictions on the arduino
             may revisit this if I find a need for it
        '''
        cp = Command_Packet('GetRawImage', UseSerialDebug=self.UseSerialDebug)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = rp.ACK
        return retval

    def GetTemplate(self, ID):
        '''

             Gets a template from the fps (498 bytes) in 4 Data_Packets
             Use StartDataDownload, and then GetNextDataPacket until done
             Parameter: 0-199 ID number
             Returns:
                0 - ACK Download starting
                1 - Invalid position
                2 - ID not used (no template to download
        '''
        cp = Command_Packet('GetTemplate', UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(ID)
        packetbytes = cp.GetPacketBytes()
        self.SendCommand(packetbytes, 12)
        rp = self.GetResponse()
        retval = 0
        if not rp.ACK:
            if rp.Error == rp.errors['NACK_INVALID_POS']:
                retval = 1
            elif rp.Error == rp.errors['NACK_IS_NOT_USED']:
                retval = 2
        return retval

    '''
         Uploads a template to the fps
         Parameter: the template (498 bytes)
         Parameter: the ID number to upload
         Parameter: Check for duplicate fingerprints already on fps
         Returns:
            0-199 - ID duplicated
            200 - Uploaded ok (no duplicate if enabled)
            201 - Invalid position
            202 - Communications error
            203 - Device error
        int SetTemplate(byte* tmplt, int id, bool duplicateCheck);
    def SetTemplate(self,tmplt,ID,duplicateCheck):
        cp = Command_Packet('SetTemplate',UseSerialDebug=self.UseSerialDebug)
        cp.ParameterFromInt(ID)


         Commands that are not implemented (and why)
         VerifyTemplate1_1 - Couldn't find a good reason to implement this on an arduino
         IdentifyTemplate1_N - Couldn't find a good reason to implement this on an arduino
         MakeTemplate - Couldn't find a good reason to implement this on an arduino
         UsbInternalCheck - not implemented - Not valid config for arduino
         GetDatabaseStart - historical command, no longer supported
         GetDatabaseEnd - historical command, no longer supported
         UpgradeFirmware - Data Sheet says not supported
         UpgradeISOCDImage - Data Sheet says not supported
         SetIAPMode - for upgrading firmware (which is not supported)
         Ack and Nack    are listed as a commands for some unknown reason... not implemented
    '''

    def SendCommand(self, cmd, length):
        '''
             resets the Data_Packet class, and gets ready to download
             Not implemented due to memory restrictions on the arduino
             may revisit this if I find a need for it
            void StartDataDownload();

             Returns the next data packet
             Not implemented due to memory restrictions on the arduino
             may revisit this if I find a need for it
            Data_Packet GetNextDataPacket();
        '''
        if not self._serial is None:
            self._serial.write(bytes(cmd))
            if self.UseSerialDebug:
                print self.serializeToSend(cmd)
                print bytes(cmd)
                print repr(bytes(cmd))[1:-1]
        else:
            if self.UseSerialDebug:
                debug_msg('Cannot write to {}'.format(self._device_name), 'SendCommand')

    def GetResponse(self):
        '''
        Gets the response to the command from the software serial channel (and waits for it)
        '''
        time.sleep(.1)
        if self._serial is None:
            rp = Response_Packet()
            debug_msg('Cannot read from {}'.format(self._device_name), 'GetResponse')
        else:
            r = bytearray(self._serial.read(self._serial.inWaiting()))
            rp = Response_Packet(r, self.UseSerialDebug)

        if rp.ACK:
            time.sleep(.1)
            r2 = bytearray(self._serial.read(self._serial.inWaiting()))
            rp2 = Response_Packet(r2, self.UseSerialDebug)
            while str(rp2._lastBuffer).__len__() > 0:
                rp.RawBytes.extend(rp2.RawBytes)
                rp._lastBuffer += rp2._lastBuffer
                time.sleep(.1)
                r2 = bytearray(self._serial.read(self._serial.inWaiting()))
                rp2 = Response_Packet(r2, self.UseSerialDebug)
        self._lastResponse = rp
        return rp
