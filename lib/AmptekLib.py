import socket
import struct
import time
import logging

class AmptekPX5(object):
    buff = 1000
    
    def __init__(self, host, port=10001, timeout=3, nr_tries=2):
        self.addr = (host,port)
        self.dev_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dev_socket.settimeout(timeout)
        self.dev_socket.connect(self.addr)
        logging.debug('%s socket created\n' % 
                      repr(self.dev_socket.getsockname()))
                      
        self.packet_proc = PacketProc()
        self.nr_tries = nr_tries
        
    def writeTextConfig(self, cmds, write_eeprom=True):
        pid1 = 0x20
        pid2 = 2
        if not write_eeprom:
            pid2 = 4
        cmd = self.packet_proc.getPacket(pid1, pid2, cmds)
        ack = self._sendCmd(cmd)
        self.packet_proc.acknowledgePacket(ack)
    
    def readTextConfig(self, cmds):
        pid1 = 0x20
        pid2 = 3
        cmd = self.packet_proc.getPacket(pid1, pid2, cmds)
        for i in range(self.nr_tries):
            raw_data = self._sendCmd(cmd)
            if raw_data != None:
                break
        else:
            msg = ('There is problem with the communication, Amptek did not'
                   'send a packet. Turn off the Windows program, if it does '
                   'not work, restart the Amptek.')
            raise RuntimeError(msg)
        data = self.packet_proc.getData(raw_data)
        return data
    
    def _read(self):
        try:
            result, socket_rsv = self.dev_socket.recvfrom(self.buff)
        except socket.timeout, e:
            result = None

        return result

    def _write(self, data):
        try:
            self.dev_socket.send(data)
        except socket.timeout, e:
            return False
        return True

    def _sendCmd(self, cmd):
        if self._write(cmd):
            return self._read()
        return None
    
    def close(self):
        if self.dev_socket != None:
            result = self.dev_socket.close()
            logging.debug( 'socket closed')
        else:
            logging.debug('enter to close but there is not socket.')
                 
    def __exit__(self):
        self.close()
        
    def __del__(self):
        self.close()


class PacketOffset(object):
    SYNC1 = 0
    SYNC2 = 1
    PID1 = 2
    PID2 = 3
    LEN_MSB = 4
    LEN_LSB = 5
    DATA = 6
    CKS_MSB = -2
    CKS_LSB = -1
    
class ACK_VALUES(object):
    OK = 0
    SYNC_ERR = 1
    PID_ERR = 2
    LEN_ERR = 3
    CHECKSUM_ERR = 4
    BAD_PARAM = 5
    BAD_HEX = 6
    UNRECOGNIZED_CMD = 7
    FPGA_ERR = 8
    CP2201_NOT_FOUND = 9
    SCOPED_DATA_NOT_AVAILABLE = 10
    PC5_NOT_PRESENT = 11
    OK_INTERFACE_SHERING_REQUEST = 12
    BUSY = 13
    I2C_ERR = 14
    OK_FPGA_UPLOAD_ADDR = 15
    NOT_SUPPORTED =16



class PacketProc(object):
    """
    Class to create the packets
    """
    
    MAX_DATA_SIZE = 512
    

    def __init__(self):
        self.sync1 = 0xF5
        self.sync2 = 0xFA

    def _caclCheckSum(self, data):
        value = sum(bytearray(data))
        invert_value = ~ value
        complement = invert_value +1
        complement &= 0xFFFF
        return complement
    
    def _getBytes(self,value):
        msb = (value & 0xFF00) >> 8
        lsb = (value & 0xFF)
        return msb, lsb
    
    def _getValue(self, msb, lsb):
        value = (msb << 8) + lsb
        return value
    
    def _validateCheckSum(self, packet):
        msb = ord(packet[PacketOffset.CKS_MSB])
        lsb = ord(packet[PacketOffset.CKS_LSB])
        packet_cks = self._getValue(msb, lsb)
        cks = self._caclCheckSum(packet[:PacketOffset.CKS_MSB])
        if cks != packet_cks:
            raise ValueError('CheckSum error')
        
    def acknowledgePacket(self, packet):
        self._validateCheckSum(packet)
        packet_type = ord(packet[PacketOffset.PID1])
        if packet_type != 0xFF: #Acknolewledge PID
            raise ValueError('The packet is not a acknowledge packet.')
      
        ack_type = ord(packet[PacketOffset.PID2])
        
        if ack_type in (ACK_VALUES.OK, ACK_VALUES.OK_FPGA_UPLOAD_ADDR,
                        ACK_VALUES.OK_INTERFACE_SHERING_REQUEST):
            return True
        
        elif ack_type == ACK_VALUES.SYNC_ERR:
            msg = ('Sync bytes in Request Packet were not correct, and '
                   'therefore, the Request Packet was rejected.')
         
        elif ack_type == ACK_VALUES.PID_ERR:
            msg = ('PID1 & PID2 combination is not recognized as a valid '
                   'Request Packet, and therefore, the Request Packet was '
                   'rejected.')
     
        elif ack_type == ACK_VALUES.LEN_ERR:
            msg = ('LEN field of the Request Packet was not consistent '
                   'with Request Packet type defined by the PID1 & PID2 '
                   'combination. It is not recognized as a valid Request '
                   'Packet, and therefore, the Request Packet was '
                   'rejected.')
 
        elif ack_type == ACK_VALUES.LEN_ERR:
            msg = ('LEN field of the Request Packet was not consistent '
                   'with Request Packet type defined by the PID1 & PID2 '
                   'combination. It is not recognized as a valid Request '
                   'Packet, and therefore, the Request Packet was '
                   'rejected.')
          
        elif ack_type == ACK_VALUES.CHECKSUM_ERR:
            msg = ('Checksum of the Request Packet was incorrect, and '
                   'therefore, the Request Packet was rejected.')
                 
        elif ack_type == ACK_VALUES.BAD_PARAM:
            msg = 'Bad parameter.'
         
        elif ack_type == ACK_VALUES.BAD_HEX:
            msg = ('Microcontroller or FPGA upload packets error: hex '
                   'record contained in the data field of the Request '
                   'Packet had a checksum or other structural error.')
         
        elif ack_type == ACK_VALUES.UNRECOGNIZED_CMD:
            msg = 'Unrecognized command.'
 
        elif ack_type == ACK_VALUES.FPGA_ERR:
            mgs = 'FPGA initialization failed.'
         
        elif ack_type == ACK_VALUES.CP2201_NOT_FOUND:
            msg = ('Set Ethernet Settings Request Packet was received, but an '
                   'Ethernet controller was not detected on the DP5.')
                
        elif ack_type == ACK_VALUES.SCOPED_DATA_NOT_AVAILABLE:
            msg = ('Send Scope Data Request Packet was received, but the '
                   'digital oscilloscope has not triggered, so no data is '
                   'available. The digital oscilloscope must be armed, '
                   'and then a trigger must occur for data to be available.')
         
        elif ack_type == ACK_VALUES.PC5_NOT_PRESENT:
            msg = ('ASCII command errors - the data field will contain the '
                   'ASCII command and parameter which caused the error. '
                   '"Bad Parameter" means that the parameter is not '
                   'recognized or exceeds the range of the command. '
                   '"Unrecognized Command" means that the 4-character command' 
                   ' is not recognized. "PC5 Not Present" is returned if a PC5'
                   ' is not mated to the DP5, and a command requiring a PC5 '
                   'is sent. (i.e. "HVSE", Set High Voltage.) '
                   '[A "Bad Parameter" ACK packet may also be returned for a '
                   'malformed I2C Request Packet, in which case LEN=0.] '
                   'If an incomplete or garbled command is returned in the '
                   'data field, it may mean that the ASCII Configuration '
                   'Packet has structural issues. (Disallowed whitespace, '
                   'missing semicolon, etc.)')
            
        elif ack_type == ACK_VALUES.BUSY:
            msg = 'Busy, another interface in use.'
         
        elif ack_type == ACK_VALUES.I2C_ERR:
            msg = ('"I2C Transfer" Request Packet, but no I2C ACK was '
                   'detected from an I2C Slave.')
        
        elif ack_type == ACK_VALUES.NOT_SUPPORTED:
            msg = ('Request Packet has been recognized as valid by the '
                   'firmware, but it is not supported by the installed FPGA '
                   'version. Update the FPGA to the latest FP version.')
  
        else:
            msg = 'Not recognized PID2 of the Acknowledge Package.'
         
        raise ValueError(msg)
  
    def getPacket(self, pid1, pid2, data):
        cmd = ""
        cmd += chr(self.sync1)
        cmd += chr(self.sync2)
        cmd += chr(pid1)
        cmd += chr(pid2)
        len_data = len(data)
        if len_data:
            if len_data > self.MAX_DATA_SIZE:
                raise ValueError('Data too long')
            
            len_msb, len_lsb = self._getBytes(len(data))
            cmd += chr(len_msb)
            cmd += chr(len_lsb)
            cmd += data
        check_sum = self._caclCheckSum(cmd)
        cs_msb, cs_lsb = self._getBytes(check_sum)
        cmd += chr(cs_msb)
        cmd += chr(cs_lsb)
        return cmd
    
    def getData(self, packet):
        self._validateCheckSum(packet)
        data = packet[PacketOffset.DATA:PacketOffset.CKS_MSB]
        return data
        
    
    
    
    
    
    