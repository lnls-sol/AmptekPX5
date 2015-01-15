from AmptekLib import PacketProc
import struct


ClockWritePackage = struct.pack('BBBBBBBBBBBBBBBB',0xf5,0xfa,0x20,2,0,8,0x43,
                                0x4c,0x43,0x4b,0x3d,0x38,0x30,0x3b,0xfb,0xea)

if __name__ == '__main__':
    data = 'CLCK=80;'
    packet = PacketProc()
    a = packet.getPacket(0x20, 2, data)
    print a == ClockWritePackage
    print packet.getData(a)
    