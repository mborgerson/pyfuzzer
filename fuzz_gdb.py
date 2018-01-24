#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import subprocess
import threading
import argparse
import time
import binascii
import struct
import sys

with open('_tracer.script', 'wb') as f:
    f.write("""
shell rm -f _trace.bin
set pagination off
break _start
run
while 1
    if ! $_isvoid ($_exitsignal)
        loop_break
    end
    if ! $_isvoid ($_exitcode)
        loop_break
    end
    append value _trace.bin $rip
    stepi
end
if $_isvoid ($_exitsignal)
    quit 0
else
    quit $_exitsignal
end
""")

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
        cmd = ['gdb', '-x', '_tracer.script', '-q', '-batch-silent', self._prog] + self._args
        print(' '.join(cmd))
        self._proc = subprocess.Popen(cmd)#,
            # stdout=subprocess.PIPE,
            # stdin=subprocess.PIPE,
            # stderr=subprocess.PIPE
            # )
        print('PID: %d' % self._proc.pid)

        # Wait for process to finish
        sig = self._proc.wait()
        if sig == 0:
            print('Process terminated normally')
        else:
            print('Process terminated with signal %d' % sig)

        # Read in program trace and update shared memory for tuple mapping
        print('Processing trace...')
        shared_mem = bytearray([0 for _ in range(64*1024)])
        ins = 0
        f = open('_trace.bin', 'rb')
        prev_location = 0
        while True:
            data = f.read(8)
            if len(data) < 8:
                break
            cur_location = struct.unpack('<Q', data)[0]
            print('%08x' % cur_location)
            index = (cur_location ^ prev_location) & (64*1024-1)
            shared_mem[index] = (shared_mem[index] + 1) & 0xff
            prev_location = cur_location >> 1
            ins += 1
        with open('64k.bin', 'wb') as f:
            f.write(shared_mem)

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