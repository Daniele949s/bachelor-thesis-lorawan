#!/usr/bin/python
# -*- coding: UTF-8 -*-

#
#    this is an UART-LoRa device and thers is an firmware on Module
#    users can transfer or receive the data directly by UART and dont
#    need to set parameters like coderate,spread factor,etc.
#    |============================================ |
#    |   It does not suport LoRaWAN protocol !!!   |
#    | ============================================|
#   
#    This script is mainly for Raspberry Pi 3B+, 4B, and Zero series
#    Since PC/Laptop does not have GPIO to control HAT, it should be configured by
#    GUI and while setting the jumpers, 
#    Please refer to another script pc_main.py
#

import sys
import sx126x
import threading
import time
import select
import termios
import tty
from threading import Timer



PACKET_TYPE_DATA = 0x01
PACKET_TYPE_ACK = 0x02

waiting_ACK = False


old_settings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())
counter = 0

#
#    Need to disable the serial login shell and have to enable serial interface 
#    command `sudo raspi-config`
#    More details: see https://github.com/MithunHub/LoRa/blob/main/Basic%20Instruction.md
#
#    When the LoRaHAT is attached to RPi, the M0 and M1 jumpers of HAT should be removed.
#


#    The following is to obtain the temprature of the RPi CPU 
def get_cpu_temp():
    tempFile = open( "/sys/class/thermal/thermal_zone0/temp" )
    cpu_temp = tempFile.read()
    tempFile.close()
    return float(cpu_temp)/1000

#   serial_num
#       PiZero, Pi3B+, and Pi4B use "/dev/ttyS0"
#
#    Frequency is [850 to 930], or [410 to 493] MHz
#
#    address is 0 to 65535
#        under the same frequence,if set 65535,the node can receive 
#        messages from another node of address is 0 to 65534 and similarly,
#        the address 0 to 65534 of node can receive messages while 
#        the another note of address is 65535 sends.
#        otherwise two node must be same the address and frequence
#
#    The tramsmit power is {10, 13, 17, and 22} dBm
#
#    RSSI (receive signal strength indicator) is {True or False}
#        It will print the RSSI value when it receives each message
#

# node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=433,addr=0,power=22,rssi=False,air_speed=2400,relay=False)
node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=868,addr=0,power=22,rssi=True,air_speed=2400,relay=False)


def handle_receive():
    r_buff = node.receive()
    
    if r_buff and len(r_buff) > 7:
        recv_addr = (r_buff[0]<<8) + r_buff[1]
        recv_freq = r_buff[2]
        send_addr = (r_buff[3]<<8) + r_buff[4]
        send_freq = r_buff[5]
        packet_type = r_buff[6]

        if recv_addr == node.addr and recv_freq == node.offset_freq:
            if packet_type == PACKET_TYPE_DATA:
                recv_counter = r_buff[7]
                recv_data = r_buff[8:-1].decode()
                print(f"\nReceived from addr {send_addr} freq {send_freq+ (850 if send_freq>18 else 410)}MHz : {recv_data} (counter {recv_counter})")
                print(f"The message is: {recv_data}")
                
                #send ACK
                header = bytes([send_addr>>8]) + bytes([send_addr&0xff]) + bytes([send_freq]) + bytes([node.addr>>8]) + bytes([node.addr&0xff]) + bytes([node.offset_freq])
                ack_data = header + bytes([PACKET_TYPE_ACK]) + bytes([recv_counter])
                node.send(ack_data)
                return False

            elif packet_type == PACKET_TYPE_ACK:
                    recv_counter = r_buff[7]
                    print(f"\nACK received from addr {send_addr} freq {send_freq+ (850 if send_freq>18 else 410)}MHz : counter {recv_counter}")
                    ack_control = (recv_counter + 1) % 256
                    if ack_control == counter:
                        print("The previous message is received successfully")
                        return True
                    else:
                        print("The previous message is not received successfully")
                        return False
            else:
                print("\nUnknown packet type received")
                return False

def send_deal():
    global counter
    global waiting_ACK
    get_rec = ""
    print("")
    print("input a string such as \033[1;32m0,868,Hello World\033[0m,it will send `Hello World` to lora node device of address 0 with 868M ")
    print("please input and press Enter key:",end='',flush=True)
    

    while True:
        rec = sys.stdin.read(1)
        if rec != None:
            if rec == '\x0a': break
            get_rec += rec
            sys.stdout.write(rec)
            sys.stdout.flush()

    get_t = get_rec.split(",")
    if len(get_t) < 3:
        print("Formato errato. Usa: addr,freq,messaggio")
        return

    offset_frequence = int(get_t[1])-(850 if int(get_t[1])>850 else 410)
    #
    # the sending message format
    #
    #         receiving node              receiving node                   receiving node           own high 8bit           own low 8bit                 own 
    #         high 8bit address           low 8bit address                    frequency                address                 address                  frequency             
    header = bytes([int(get_t[0])>>8]) + bytes([int(get_t[0])&0xff]) + bytes([offset_frequence]) + bytes([node.addr>>8]) + bytes([node.addr&0xff]) + bytes([node.offset_freq]) 
    data = header + bytes([PACKET_TYPE_DATA]) + bytes([counter]) + get_t[2].encode() 
    node.send(data)
    counter = (counter + 1) % 256

    ACK_tout = 5
    start = time.time()
    waiting_ACK = True
    while time.time() - start < ACK_tout:
        if handle_receive():
            waiting_ACK = False  
            break
        time.sleep(0.05)
    waiting_ACK = False

    print('\x1b[2A',end='\r')
    print(" "*200)
    print(" "*200)
    print(" "*200)
    print('\x1b[3A',end='\r')    

try:
    time.sleep(1)
    print("Press \033[1;32mEsc\033[0m to exit")
    print("Press \033[1;32mi\033[0m   to send")

    
    while True:

        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            c = sys.stdin.read(1)

            # dectect key Esc
            if c == '\x1b': break
            # dectect key i
            if c == '\x69':
                try:
                    send_deal()
                except Exception as e:
                    print(f"Errore durante send_deal(): {e}")

            sys.stdout.flush()

        if not waiting_ACK:
            handle_receive()
            
        
        # timer,send messages automatically
        
except:
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    # print('\x1b[2A',end='\r')
    # print(" "*100)
    # print(" "*100)
    # print('\x1b[2A',end='\r')

termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
# print('\x1b[2A',end='\r')
# print(" "*100)
# print(" "*100)
# print('\x1b[2A',end='\r')
