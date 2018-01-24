#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import subprocess
import threading
import argparse
import socket
import time
from xml.dom import minidom
import binascii
import struct
import sys

class Register(object):
    def __init__(self, name, width):
        self.name = name
        self.width = width
        self.data = bytearray([0 for i in range(width/8)])

    @property
    def value(self):
        if self.width == 32:
            return struct.unpack('<I', self.data)
        elif self.width == 64:
            return struct.unpack('<Q', self.data)
        else:
            return self.data
    
    @value.setter
    def value(self, val):
        if self.width == 32:
            struct.pack_into(self.data, 0, '<I', val)
        elif self.width == 64:
            struct.pack_into(self.data, 0, '<Q', val)
        else:
            assert(isinstance(val, bytearray))
            assert(len(val) == len(self.data))
            self.data = val

class RegisterFile(object):
    def __init__(self):
        self.ordered_regs = []
        for f in ['64bit-core.xml', '64bit-sse.xml']:
            for s in minidom.parse(f).getElementsByTagName('reg'):
                name = s.attributes['name'].value
                width = int(s.attributes['bitsize'].value)
                self.ordered_regs.append(Register(name, width))

        self.regs = {}
        for r in self.ordered_regs:
            self.regs[r.name] = r

    def __getattr__(self, name):
        return self.regs[name]

    def decode(self, data):
        start = 0
        for r in self.ordered_regs:
            end = start + r.width / 4
            enc = data[start:end]
            r.data = binascii.unhexlify(enc)
            start = end
        assert end == len(data)

    def encode(self):
        data = ''
        for r in self.ordered_regs:
            data += binascii.hexlify(r.data)
        return data

reg_file = RegisterFile()

class GdbClient(object):
    def __init__(self, host, port):
        self._s = socket.create_connection((host, port))
    
    def recv_packet(self):
        buf = self._s.recv(1)
        if buf != '$':
            raise ValueError('Expected start of packet token')
        
        # Fill up buffer until end of packet (#XX) detected
        while not (len(buf) >= 4 and buf[-3] == '#'):
            buf += self._s.recv(1)
        
        # print('Received Packet:', buf)

        # Perform packet checksum
        csum_e = int(buf[-2:],16)
        csum_a = sum(bytearray(buf[1:-3])) & 0xff
        if csum_e != csum_a:
            # Nack packet
            print('Bad packet checksum!')
            print('Sending Nack')
            self._s.send('-')
            return None

        # Ack packet
        # print('Sending Ack')
        self._s.send('+')
        return buf[1:-3]

    def send_packet(self, data):
        buf = '$' + data + '#%02x' % (sum(bytearray(data)) & 0xff)
        # print('Sending Packet:', buf)
        self._s.send(buf)
        r = self._s.recv(1)
        if r == '+':
            # print('Ack Recieved')
            return True
        elif r == '-':
            # print('Nack Recieved')
            return False
        else:
            raise Exception('Did not get ack for packet!')

    def loadregs(self):
        #print('Reading CPU registers')
        self.send_packet('g')
        data = self.recv_packet()
        reg_file.decode(data)

    def cmd_continue(self):
        self.send_packet('c')
        self.recv_packet()

class Program(threading.Thread):
    def __init__(self, prog, args=None):
        super(Program, self).__init__()
        self._prog = prog
        self._args = args or []
    
    def run(self):
        gdb_port = 38291
        print('Target:', self._prog)
        print('Arguments:', *self._args)

        # Spawn the subprocess
        print('Launching process...')
        cmd = ['qemu-x86_64', '-g', str(gdb_port), '-singlestep', self._prog] + self._args
        print(' '.join(cmd))
        self._proc = subprocess.Popen(cmd)#,
            # stdout=subprocess.PIPE,
            # stdin=subprocess.PIPE,
            # stderr=subprocess.PIPE
            # )
        print('PID: %d' % self._proc.pid)

        # Try to connect via GDB server
        attempts = 10
        gdb = None
        for i in range(attempts):
            print('Connection attempt #%d' % i)
            gdb = None
            try:
                gdb = GdbClient('127.0.0.1', gdb_port)
            except Exception as e:
                pass
            if gdb is not None:
                break
            time.sleep(0.125)

        if gdb is None:
            print('Failed to connect to gdb service!')
            self._proc.kill()
            return

        print('Ok!')

        gdb.send_packet('qSupported')
        gdb.recv_packet()
        
        gdb.loadregs()
        print('rip = %x' % reg_file.rip.value)

        # Break on prog entry
        gdb.send_packet('Z0,400430,1')
        r = gdb.recv_packet()
        assert(r == 'OK')

        gdb.send_packet('vCont;c')
        # Target will continue...
        r = gdb.recv_packet()

        gdb.send_packet('z0,400430,1')
        r = gdb.recv_packet()
        assert(r == 'OK')

        while True:

            # gdb.send_packet('s')
            gdb.send_packet('s')
            resp = gdb.recv_packet()

            if resp == 'S05':
                # Trap
                gdb.loadregs()
                print('rip = %x' % reg_file.rip.value)
                # sys.stdout.write('.')
                # sys.stdout.flush()
                continue
            
            print('Program terminated with', resp)
            break
            

        # # Wait for program to complete (or for it to be killed)
        # print('Waiting for subprocess completion')
        # self._proc.communicate()

    def stop(self):
        if self._proc.poll() is None:
            print('Killing subprocess')
            self._proc.kill()

def main():
    a = argparse.ArgumentParser()
    a.add_argument('prog', help='program to fuzz')
    a.add_argument('args', nargs='*', help='program arguments (@@ for input file)')
    args = a.parse_args()

    p = Program(args.prog, args.args)

    try:
        p.start()
        p.join()
    except KeyboardInterrupt as e:
        pass
    p.stop()

if __name__ == '__main__':
    main()