# SPDX-License-Identifier: MIT

"""
A simple Python module to make using the Grow barcode scanner modules easier.
Module needs to be configured to communciate over serial. Tested with the GM65 
and GM812, might work with other similar modules as well.
"""

from enum import Enum
from math import ceil
import logging
import serial


class Scanner():
    """
    Class for a barcode scanner module connected over serial."""

    def __init__(self, serial_port):
        # baud is 9600 by default, hard-coded for now
        logging.info("Connecting to serial port: " + serial_port)
        self.connection = serial.Serial(
            serial_port, 9600, timeout=10, write_timeout=1)

    def __del__(self):
        self.connection.flushInput()
        self.connection.flushOutput()
        self.connection.close()

    def scan(self):
        pass

    def disable_all_formats(self):
        pass

    def enable_all_formats(self):
        # TODO: implement this
        pass

    def enable_format(self, code_format, enable=True):
        pass

    def save_config(self):
        pass


class GM65(Scanner):
    class Register():
        """Some register values for the scanner module."""
        # Decode LED enabled
        # Mute off
        # Laser on when scanning
        # Illumination on when scanning
        # Command triger mode
        ScanMode = (0x00, 0b11010101)
        TriggerScanning = (0x02, 0b00000001)
        # Disable all code formats
        # Full range decoding
        DisableAllFormats = (0x2c, 0b00000000)
        # Return original data over serial
        # Termination character CR (default)
        # Enable read fail return
        # Disable prefix
        # Disable code ID
        # Disable suffix
        # Enable termination string (default)
        SerialProtocolConfig = (0x60, 0b00010001)
        # Set read fail message length
        SetReadFailMsgLength = (0x81, 0x02)
        # Set read fail message to 0x15 (NAK) 0x0D (CR)
        SetReadFailMessage = (0x82, 0x150D)
        SaveConfig = (0x0, 0x0)

    class FormatRegister(Enum):
        """Format register addresses"""
        QR = 0x3F
        DATAMATRIX = 0x54
        PDF417 = 0x55

    class CmdHeader(Enum):
        """Message headers"""
        COMMAND = 0x7E00
        RESPONSE = 0x0200

    class CmdType(Enum):
        """Type codes for the commands sent to the module"""
        READ = 0x07
        WRITE = 0x08
        CONFIG = 0x09

    class ResponseType(Enum):
        """Type codes for the responses received from the module"""
        SUCCESS = 0x00

    def __init__(self, serial_port):
        super().__init__(serial_port)
        self.__configure()

    def scan(self):
        logging.info("Triggering a scan on GM65")
        self.__send_command(
            self.CmdType.WRITE, self.Register.TriggerScanning[0], self.Register.TriggerScanning[1])
        data = self.connection.read_until(b'\x0d')  # read until LF
        logging.info("Received data: " + data.decode())
        return data[:-1]

    def __configure(self):
        logging.info("Configuring GM65")
        self.__send_command(
            self.CmdType.WRITE, self.Register.ScanMode[0], self.Register.ScanMode[1])
        self.__send_command(
            self.CmdType.WRITE, self.Register.SerialProtocolConfig[0], self.Register.SerialProtocolConfig[1])
        # This doesn't work on GM812, these registers don't exist, check readme for instructions to
        # set it up manually
        self.__send_command(
            self.CmdType.WRITE, self.Register.SetReadFailMsgLength[0], self.Register.SetReadFailMsgLength[1])
        self.__send_command(
            self.CmdType.WRITE, self.Register.SetReadFailMessage[0], self.Register.SetReadFailMessage[1])

    def disable_all_formats(self):
        logging.info("Disabling all formats on GM65")
        self.__send_command(
            self.CmdType.WRITE, self.Register.ScanMode[0], self.Register.ScanMode[1])

    def enable_format(self, code_format, enable=True):
        logging.info("Enabling format " + code_format.name + " on GM65")
        self.__send_command(
            self.CmdType.WRITE, code_format.value, enable)

    def save_config(self):
        logging.info("Saving configuration to flash on GM65")
        self.__send_command(
            self.CmdType.CONFIG, self.Register.SaveConfig[0], self.Register.SaveConfig[1])

    def __send_command(self, cmd_type, address, data):
        # {Header} {Type} {Length} {Address} {Data} {CRC}
        command_body = bytearray()
        command_body.append(cmd_type.value)
        data_size = ceil(data.bit_length() / 8)
        command_body += (data_size.to_bytes(1, 'big'))
        command_body += address.to_bytes(2, 'big')
        command_body += data.to_bytes(data_size, 'big')
        command = self.CmdHeader.COMMAND.value.to_bytes(
            2, 'big') + command_body + crc16(command_body)
        logging.info("Sending command: " + command.hex())
        self.connection.write(command)
        self.__receive_response()

    def __receive_response(self):
        response = self.connection.read(7)
        logging.info("Received response: " + response.hex())


def crc16(data: bytes):
    '''
    CRC-16 (CCITT) implemented with a precomputed lookup table
    '''
    table = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7, 0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6, 0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485, 0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4, 0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
        0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823, 0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
        0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12, 0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
        0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41, 0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
        0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70, 0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
        0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F, 0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E, 0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D, 0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C, 0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB, 0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
        0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A, 0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
        0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9, 0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
        0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8, 0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
    ]

    crc = 0x00
    for byte in data:
        crc = (crc << 8) ^ table[(crc >> 8) ^ byte]
        crc &= 0xFFFF
    return crc.to_bytes(2, 'big')
