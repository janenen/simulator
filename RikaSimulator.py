import serial
import serial.tools.list_ports
import random
import math, time 


class RikaEmulator:
    NUL = b"\x00"
    SOH = b"\x01"
    EOT = b"\x04"
    ACK = b"\x06"
    _REPEAT = b"\x07"
    BS = b"\x08"
    FF = b"\x0C"
    CR = b"\x0D"
    SYN = b"\x16"
    ESC = b"\x1B"
    ABM = b"\xD0"
    EINZEL = b"\xD1"
    _10SER = b"\xD2"
    GESAMT = b"\xD3"
    _5SER = b"\xD4"
    REST = b"\xD5"

    def get_checksum(self,data):
        b=0
        for a in data:
            b=b ^ a
        return bytes([b])

    def get_shot(self):

        self.t = 0
        self.phi = 0
        self.x = 0
        self.y = 0
        self.ring = 0

        s = random.uniform(0, 2000)
        t = s * s / 2000
        phi = random.uniform(0, math.pi)
        x = t * math.cos(2 * phi)
        y = t * math.sin(2 * phi)
        ring = 10.9 - math.floor((t - 5) / 25.0) / 10
        if ring < 0:
            ring = 0
        elif ring > 10.9:
            ring = 10.9
        return f"{int(ring*10):03d}\r{int(t*10):05d}\r{int(x):+06d}\r{int(y):+06d}\r"

    def send_data(self):
        print("send data")
        for i in range(0, self.serie):
            time.sleep(random.random()*0.05)
            #DATEN
            data=self.send_header()
            buff = self.get_shot().encode("utf-8")
            data+=buff
            self.serialport.write(buff)
            self.serialport.write(self.EOT)
            data+=self.EOT
            self.serialport.write(self.get_checksum(data))#
            print(data)
            while True:
                ans= self.serialport.read(1)
                print(ans)
                if ans ==self.BS:
                    print("BS")
                    self.serialport.write(self._REPEAT) 
                    self.send_header()
                    self.serialport.write(buff)
                    self.serialport.write(self.EOT)
                    self.serialport.write(self.get_checksum(data))#
                elif ans==self.FF:
                    if i==self.serie-1:
                        break
                    else:
                        continue
                elif ans==self.SYN:
                    break

    def send_header(self):
        data=self.SOH
        self.serialport.write(self.SOH)
        buff = f"{self.serial}\r"
        data+=buff.encode("utf-8")
        self.serialport.write(buff.encode("utf-8"))
        buff = f"{self.bus_address:03d}\r"
        data+=buff.encode("utf-8")
        self.serialport.write(buff.encode("utf-8"))
        buff = "00000000\r"
        data+=buff.encode("utf-8")
        self.serialport.write(buff.encode("utf-8"))
        buff = "LG\r"
        data+=buff.encode("utf-8")
        self.serialport.write(buff.encode("utf-8"))
        buff = f"{self.faktor:02d}\r"
        data+=buff.encode("utf-8")
        self.serialport.write(buff.encode("utf-8"))
        buff = f"{self.serie:03d}\r"
        data+=buff.encode("utf-8")
        self.serialport.write(buff.encode("utf-8"))
        return data
        

    def __init__(self):
        self.state = 0
        self.delaydata = 3
        self.buff = b""
        self.serie = 10
        self.teiler = 0000
        self.faktor = 10
        self.schuss = 1
        self.zehntel = 0
        self.serial = "20013591"
        self.bus_address = 0
        print("Press Ctrl+C to exit")
        self.serialport = serial.Serial("COM4", 9600, timeout=0.5)
        while True:
            input = self.serialport.read(1)
            
            if input:
                print("state: ", self.state, "input: ", input)
                if self.state == 0:
                    if (
                        input == self.EINZEL
                        or input == self._10SER
                        or input == self.GESAMT
                        or input == self._5SER
                        or input == self.REST
                    ):
                        self.state = 1
                        self.serialport.write(b"200")

                elif self.state == 1:

                    if input == self.ABM:
                        self.state = 0
                        self.serialport.write(self.NUL)
                    elif input == self.SYN:
                        print("delay= ", self.delaydata)
                        if self.delaydata == 0:
                            self.send_data()
                            self.delaydata = 3
                            self.state = 1
                        else:
                            self.serialport.write(self.NUL)
                            self.delaydata -= 1
                            self.data_availabel = True
                    elif input == self.ESC:
                        self.state = 3



                elif self.state == 3:
                    if input == b"S":
                        self.state = 4
                        self.n = 3
                    elif input == b"T":
                        self.state = 5
                        self.n = 4
                    elif input == b"F":
                        self.state = 6
                        self.n = 2
                    elif input == b"U":

                        self.state = 7
                        self.n = 1
                    elif input == b"Z":
                        self.state = 8
                        self.n = 1
                    elif input == b"Z":
                        self.state = 9

                elif self.state == 4:  # S XXX CR
                    if self.n > 0:
                        if input.isdigit():
                            self.buff += input
                            self.n -= 1
                    else:
                        if input == self.CR:
                            temp = int(self.buff)
                            if 0 < temp and temp <= 200:
                                self.serie = temp
                                self.serialport.write(self.ACK)
                            else:
                                self.serialport.write(self.NUL)
                            self.state = 1  # Eingabe abgeschlossen
                            self.buff = b""

                elif self.state == 5:  # T XXXX CR
                    if self.n > 0:
                        if input.isdigit():
                            self.buff += input
                            self.n -= 1
                    else:
                        if input == self.CR:
                            temp = int(self.buff)
                            if 0 < temp and temp <= 6500:
                                self.teiler = temp
                                self.serialport.write(self.ACK)
                            else:
                                self.serialport.write(self.NUL)
                            self.state = 1
                            self.buff = b""

                elif self.state == 6:  # F XX CR
                    if self.n > 0:
                        if input.isdigit():
                            self.buff += input
                            self.n -= 1
                    else:
                        if input == self.CR:
                            temp = int(self.buff)
                            if 0 < temp and temp <= 99:
                                self.faktor = temp
                                self.serialport.write(self.ACK)
                            else:
                                self.serialport.write(self.NUL)
                            self.state = 1
                            self.buff = b""

                elif self.state == 7:  # U X CR
                    if self.n > 0:
                        if input.isdigit():
                            self.buff += input
                            self.n -= 1
                    else:
                        if input == self.CR:
                            temp = int(self.buff)
                            if 0 < temp and temp <= 5:
                                self.schuss = temp
                                self.serialport.write(self.ACK)
                            else:
                                self.serialport.write(self.NUL)
                            self.state = 1
                            self.buff = b""

                elif self.state == 8:  # Z X CR
                    if self.n > 0:
                        if input.isdigit():
                            self.buff += input
                            self.n -= 1
                    else:
                        if input == self.CR:
                            temp = int(self.buff)
                            if 0 <= temp and temp <= 3:
                                self.zehntel = temp
                                self.serialport.write(self.ACK)
                            else:
                                self.serialport.write(self.NUL)
                            self.state = 1
                            self.buff = b""

                elif self.state == 9:  # E CR

                    if input == self.CR:
                        buff = f"{self.serial}.\r".encode("UTF-8")
                        self.serialport.write(buff)

                        buff = f"{self.bus_address:03d}\r"
                        self.serialport.write(buff)

                        buff = f"{self.serie:03d}\r"
                        self.serialport.write(buff)

                        buff = f"{self.teiler:04d}\r"
                        self.serialport.write(buff)

                        buff = f"{self.faktor:02d}\r"
                        self.serialport.write(buff)

                        buff = f"{self.schuss:01d}\r"
                        self.serialport.write(buff)

                        buff = f"{self.zehntel:01d}\r"
                        self.serialport.write(buff)
                        self.state = 1


if __name__ == "__main__":
    RikaEmulator()
