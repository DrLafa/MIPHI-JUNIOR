#!/usr/bin/env python3
# -*- coding: UTF=8 -*-

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import sr1, TCP, IP, send, RandShort
from datetime import datetime
import ipaddress
import threading
from queue import Queue

class PortscanThread(threading.Thread):
    ports = [80, 8080, 23]
    start_clock = datetime.now()
    SYNACK = 0x12
    RSTACK = 0x14

    def __init__(self, queue, out, verbose=True):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out = out
        self.verbose = verbose

    def run(self):
        while True:
            ip = self.queue.get()
            open_ports = self.ScanPorts(ip)

            if open_ports:
                if self.verbose:
                    print("\tHost:\t%s" % ip)
                    print("\tPorts:\t%s" % ", ".join(map(str, open_ports)), end="\n\n")
                self.out.put((ip, open_ports))

            self.queue.task_done()

    def ScanPorts(self, host):
        open_ports = []
        for port in self.ports:
            port_status = self.ScanPort(host, port)
            if port_status is "Unreachable":
                return False
            elif port_status is "Open":
                open_ports.append(port)

        if open_ports:
            return open_ports
        else:
            return False

    def ScanPort(self, host, port):
        srcport = RandShort()
        SYNACKpkt = sr1(IP(dst = host)/TCP(sport = srcport, dport = port, flags = "S"), timeout=1, verbose=0)
        if not SYNACKpkt:
            return "Unreachable"

        pktflags = SYNACKpkt.getlayer(TCP).flags

        RSTpkt = IP(dst = host)/TCP(sport = srcport, dport = port, flags = "R")
        send(RSTpkt, verbose=0)
        if pktflags == self.SYNACK:
            return "Open"
        else:
            return False


class PortScanner:
    def __init__(self, num_threads=10, verbose=True):
        self.num_threads = num_threads
        self.verbose = verbose

    def scan(self, ip_range):
        """ Принимает список ip-адресов для сканирования,
            возвращает список хостов с открытыми портами в формате
            [ (ip, [port1, port2]), (ip, [port1, port2]), ... ]
        """
        if self.verbose:
            print("Performing port scan...")
            print("-"*40)

        queue = Queue()
        out = Queue()

        for i in range(self.num_threads):
            t = PortscanThread(queue, out, verbose=self.verbose)
            t.setDaemon(True)
            t.start()

        for ip in ip_range:
            queue.put(ip)

        queue.join()
        out = [ip for ip in out.queue]

        if self.verbose:
            if not len(out):
                print("\nDiveces with open ports not found. Exiting...\n")
            print("-"*40, end="\n\n")
        return out


if __name__ == "__main__":
    import sys
    scanner = PortScanner(verbose=True, num_threads=1)
    #ip = "192.168.0.1,192.168.0.2,192.168.0.100"
    ip = sys.argv[1]
    print(ip)
    #exit()
    out = scanner.scan([ip])
    print(out)
