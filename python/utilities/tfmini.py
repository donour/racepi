import serial
import os, sys
import time
from statistics import mean as avg

def get_version(s):
    s.flush()
    cmd = [0x5A, 0x04, 0x01, 0x5F]
    s.write(cmd)
    while True:
        h = s.read(1)
        if h[0] == 0x5A:
            c = s.read(1)
            if c[0] == 0x07:
                msg = s.read(5)
                v = f"{msg[3]:d}.{msg[2]:d}.{msg[1]:d}"
                s.flushInput()
                return v
        if h[0] == 0x59:
            s.write(cmd)

def set_config(s, cmd):
    s.flush()
    s.write(cmd)
    return
    #while True:
    #    print("getting response")
    #    h = s.read(1)
    #    if h[0] == 0x5A:
    #        c = s.read(1)
    #        if c[0] == 0x06:
    #            msg = s.read(4)
    #            print(hex(h[0]), hex(c[0]), hex(msg[0]), hex(msg[1]), hex(msg[2]))
    #            s.flushInput()
    #            return
    #    if h[0] == 0x59:
    #        s.write(cmd)
            
def set_framerate(s, hz: int = 100):

    # TODO, checksum ignored?
    hb = hz.to_bytes(2, 'little')
    cmd = [0x5A, 0x6, 0x03, hb[0], hb[1], 0x00] # 50 hz
    #cmd = [0x5A, 0x6, 0x3, 0xFF, 0x01, 0x62] # 1 khz
    #cmd = [0x5A, 0x6, 0x3, 0x00, 0x01, 0x63] # ~320 hz
    #cmd = [0x5A, 0x6, 0x3, 0x7F, 0x01, 0xE2] # ~ 500 hz
    set_config(s, cmd)

def set_out_mm(s):
    cmd = [0x5A, 0x05, 0x05, 0x06, 0x6A]
    set_config(s, cmd)
    
def get_line(s):
    while True:
        c = s.read(1)
        if c[0] == 0x59:
            s.read(1)
            if c[0] == 0x59:
                c = s.read(7)
                distance = c[0] + (c[1] << 8)
                strength = c[2] + (c[3] << 8)
                temp = c[4] + (c[5] << 8)
                return (distance, strength, (temp//8)- 256)


if __name__ == "__main__":
    devname = sys.argv[1]
    print(devname)
    s = serial.Serial(devname, baudrate=115200)

    print(get_version(s))
    set_framerate(s, 50)
    set_out_mm(s)

    count = 0
    start = time.time()
    skipped = 0;
    while True:

        # d,strength,t = get_line(s)

        samples = []
        for sample_cnt in range(50):  
            count += 1
            samples.append(get_line(s))

        d = avg([s[0] for s in samples])
        strength = avg([s[1] for s in samples])
        t = avg([s[2] for s in samples])

        if d < 3000:
            end = time.time()
            print(f" {d: 4.1f}mm  {(count)/(end-start):3.1f}(hz) {t:.0f}C  ({skipped})              ", end="\r")
            #count = 0
            #start = time.time()
        else:
            skipped += 1
