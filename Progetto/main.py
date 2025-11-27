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
import random



PACKET_TYPE_DATA = 0x01
PACKET_TYPE_ACK = 0x02

waiting_ACK = False  #Serve per evitare che la handle_receive si "mangi" l'ACK prima che arrivi alla send_deal


old_settings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())
counter = 0
counter_pck_sent = 0
counter_pck_lost = 0

# node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=433,addr=0,power=22,rssi=False,air_speed=2400,relay=False)
node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=868,addr=0,power=22,rssi=True,air_speed=2400,relay=False)

#Funzione di gestione della ricezione, capisce il tipo di pacchetto (se DATA o ACK) e lo processa di conseguenza
def handle_receive():
    global counter
    r_buff = node.receive()

    PERC_ERRORE_SIMULATO = 30
    
    if r_buff != None:

        if random.randint(0, 100) < PERC_ERRORE_SIMULATO:
            print(f"[TEST] Pacchetto scartato artificialmente (Simulazione interferenza)")
            return False

        from_addr = (r_buff[0]<<8) | r_buff[1]
        from_freq = r_buff[2]
        payload = r_buff[3:-1] if node.rssi else r_buff[3:] 

        ptype = payload[0]
        rec_counter = payload[1]
        msg = payload[2:]

        if ptype == PACKET_TYPE_DATA:
            print(f"\nReceived from addr {from_addr} freq {from_freq+ (node.start_freq)}MHz : {msg.decode(errors='ignore')} (counter {rec_counter})")

            ack_msg = "ACK"
            ack_payload = bytes([PACKET_TYPE_ACK]) + bytes([rec_counter]) + ack_msg.encode()               
            ack_data = bytes([from_addr>>8]) + bytes([from_addr&0xff]) + bytes([from_freq]) + bytes([node.addr>>8]) + bytes([node.addr&0xff]) + bytes([node.offset_freq]) + ack_payload
            node.send(ack_data)
            return False

        elif ptype == PACKET_TYPE_ACK:
                
                print(f"\nACK received from addr {from_addr} freq {from_freq+ (node.start_freq)}MHz : counter {rec_counter}")
                ack_control = (rec_counter) % 256
                if ack_control == counter:
                    print(f"ACK OK, COUNTER: {rec_counter}")
                    return True
                else:
                    print("ACK NOT OK")
                    return False
        else:
            print("\nUnknown packet type received")
            return False

def send_deal():
    global counter
    global waiting_ACK
    global counter_pck_sent
    global counter_pck_lost
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

    print(f"Sending to addr {get_t[0]} freq {get_t[1]}MHz : {get_t[2]} (counter {counter})")

    #Costruzione del payload per includere altri campi oltre al messaggio (tipo del pacchetto e counter)
    payload = bytes([PACKET_TYPE_DATA]) + bytes([counter]) + get_t[2].encode()

    # the sending message format
    #
    #         receiving node              receiving node                   receiving node           own high 8bit           own low 8bit                 own 
    #         high 8bit address           low 8bit address                    frequency                address                 address                  frequency             message payload
    data = bytes([int(get_t[0])>>8]) + bytes([int(get_t[0])&0xff]) + bytes([offset_frequence]) + bytes([node.addr>>8]) + bytes([node.addr&0xff]) + bytes([node.offset_freq]) + payload

    #print("DATA:", list(data)) utile per DEBUG


    for i in range(3):
        node.send(data)
        

        #RICEZIONE ACK
        ACK_tout = 10
        start = time.time()
        waiting_ACK = True 
        while time.time() - start < ACK_tout:
            if handle_receive():
                waiting_ACK = False  
                counter = (counter + 1) % 256

                #Calcolo Latenza
                end = time.time()
                rtt = end - start
                pps = 1 / rtt
                print(f"Latenza (RTT): {rtt:.4f} secondi")
                print(f"Packets per second (pps): {pps:.2f}")

                #Packet loss rate
                counter_pck_sent += 1
                print(f"Packets sent: {counter_pck_sent}, Packets lost: {counter_pck_lost}, Loss rate: {(counter_pck_lost/counter_pck_sent)*100:.2f}%")

                #Calcolo throughput
                msg_bits = len(get_t[2].encode()) * 8 
                throughput = msg_bits / rtt
                print(f"Throughput: {throughput:.2f} bps")
                print(f"Bits message: {msg_bits}")

    
                #print('\x1b[2A',end='\r')
                #print(" "*200)
                #print(" "*200)
                #print(" "*200)
                #print('\x1b[3A',end='\r')
                return
            time.sleep(0.05)
        counter_pck_sent += 1
        counter_pck_lost += 1
        print(f"{i} attempts finished, no ACK received")    
    print("All attempts finished, no ACK received.")
    print(f"Packets sent: {counter_pck_sent}, Packets lost: {counter_pck_lost}, Loss rate: {(counter_pck_lost/counter_pck_sent)*100:.2f}%")
    waiting_ACK = False

    #print('\x1b[2A',end='\r')
    #print(" "*200)
    #print(" "*200)
    #print(" "*200)
    #print('\x1b[3A',end='\r')    

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
