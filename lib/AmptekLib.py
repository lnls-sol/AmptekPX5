import socket
import struct
import time

class AmptekPX5(object):
    buff = 1000
    
    def __init__(self, host, port=10001, timeout=3):
        self.addr = (host,port)
        self.dev_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dev_socket.settimeout(timeout)
        self.dev_socket.connect(self.addr)
        print '%s socket created\n' % repr(self.dev_socket.getsockname())
        self.packet_proc = PacketProc()
        
    def sendTextConfig(self, cmds, write_eeprom=True):
        pid1 = 0x20
        pid2 = 2
        if not write_eeprom:
            pid2 = 4
        cmd = self.packet_proc.getPacket(pid1, pid2, cmds)
        ack = self._sendCmd(cmd)
        
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
    
    def _close(self):
        if self.dev_socket != None:
            result = self.dev_socket.close()
        else:
            print 'enter to close but there is not socket.'
                 
    def __exit__(self):
        self._close()
        
    def __del__(self):
        self._close()


class PacketOffset(object):
    SYNC1 = 1
    SYNC2 = 2
    PID1 = 3
    PID2 = 4
    LEN_MSB = 5
    LEN_LSB = 6
    DATA = 7
    CKS_MSB = -2
    CKS_LSB = -1
    
class ACK_VALUES(object):
    OK = 1
    SYNC_ERR = 2
    PID_ERR = 3
    LEN_ERR = 4
    CHECKSUM_ERR = 5
    BAD_PARAM = 6
    BAD_HEX = 7
    UNRECOGNIZED_CMD = 8
    FPGA_ERR = 9
    CP2201_NOT_FOUND = 10
    SCOPED_DATA_NOT_AVAILABLE = 11
    PC5_NOT_PRESENT = 12
    OK_INTERFACE_SHERING_REQUEST = 13
    BUSY = 14
    I2C_ERR = 15
    OK_FPGA_UPLOAD_ADDR = 16
    NOT_SUPPORTED =17



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
        data = packet[PacketOffset.LEN_LSB:PacketOffset.CKS_MSB]
        return data
        
    
    
    
    
    
    