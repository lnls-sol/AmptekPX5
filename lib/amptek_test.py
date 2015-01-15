from AmptekLib import AmptekPX5
import struct

ClockWritePackage = struct.pack('BBBBBBBBBBBBBBBB',0xf5,0xfa,0x20,2,0,8,0x43,
                                0x4c,0x43,0x4b,0x3d,0x38,0x30,0x3b,0xfb,0xea)

AcknowlegePackage = struct.pack('BBBBBBBB',0xf5,0xfa,0xff,0, 0, 0,0xfd, 0x12)

if __name__ == '__main__':
    amptek_comm = AmptekPX5('bl13amptek-lab', timeout=1)
    cmd = 'CLCK=80;SCAI=1;SCAL=2;SCAH=41;'
    amptek_comm.sendTextConfig(cmd)
    result = amptek_comm._sendCmd(ClockWritePackage)
    print result == AcknowlegePackage   