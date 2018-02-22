#!/usr/bin/env python
#
# Driver for DSA815TG over LXI (TCP/5555)
#
#!/usr/bin/python

import socket
import math
import time
import sys

class DSA815:
  def __init__(self, ip_address):
    self.sock = socket.socket()
    self.sock.connect((ip_address, 5555))        
    self.max_chars = 1024
    #self.Verify()
    
  def Send(self, command):
    self.sock.sendall(command + '\n')
    time.sleep(0.1)

  def Receive(self):
    result = ''
    while True:
      result = result + self.sock.recv(self.max_chars)
      sys.stdout.flush()
      if result.find('\n') >=0:
        return result

  def SendReceive(self, command):
    self.Send(command)
    return self.Receive()
  
  def Verify(self):
    id = self.SendReceive('*IDN?')
    if id[0:25] != 'Rigol Technologies,DSA815':
      raise RuntimeError('Analyzer ID Not Recognized')

  #
  # read a trace from the analyzer
  #
  def GetTrace(self, trace_number=1):
    freq_start = float(self.SendReceive(':FREQ:STAR?'))
    freq_stop = float(self.SendReceive(':FREQ:STOP?'))
    self.Send(":FORM:TRAC:DATA:ASC")
    command = ':TRAC:DATA? TRACE%d' % trace_number
    data = self.SendReceive(command)
    hdr_len = 3 + int(data[1:2])
    data = data[hdr_len:-1]
    values = data.split(',')
    fstep = (freq_stop - freq_start) / 600.
    freq = freq_start
    array = []
    for value in values:
      val = float(value)
      array.append( (int(freq), val) )
      freq = freq + fstep
    return array

  def Sweep(self, freq_start, freq_stop):
    self.Send(':INIT:CONT OFF')
    sweep_time = float(self.SendReceive(':SWE:TIME?'))
    cmd = ':FREQ:START %d' % freq_start
    #print cmd
    self.Send(cmd)
    cmd = ':FREQ:STOP %d' % freq_stop
    #print cmd
    self.Send(cmd)
    time.sleep(2*sweep_time+1)
    sweep_time = float(self.SendReceive(':SWE:TIME?'))
    #print sweep_time
    self.Send('*TRG')
    time.sleep(2*sweep_time+3)
    return self.GetTrace()

  def LogSweep(self, start_freq, stop_freq, pts_per_dec):
    step = math.pow(10, 1 + math.floor(math.log10(start_freq)))/pts_per_dec
    lower_freq = start_freq
    upper_freq = min(math.floor(lower_freq + 600 * step), stop_freq)
    #print lower_freq, upper_freq, step
    data = self.Sweep(lower_freq, upper_freq)
    if upper_freq == stop_freq:
      return data
    data = data + self.LogSweep(upper_freq, stop_freq, pts_per_dec)
    return(data)

  def NewSweep(self, start_freq, stop_freq, rbw, preamp):
    self.Send(":INIT:CONT OFF")
    self.Send(":TRAC1:MODE WRIT")
    self.Send(":SENS:POW:RF:ATT:AUTO OFF")
    self.Send(":SENS:POW:RF:ATT 0")
    self.Send(":SOUR:POW:LEV:IMM:AMPL 0")
    self.Send(":OUTP:STAT ON")

    if (preamp):
      self.Send(":SENS:POW:RF:GAIN:STAT ON")
    else:
      self.Send(":SENS:POW:RF:GAIN:STAT OFF")

    self.Send(":SENS:DET:FUNC RMS")
    self.Send(":FREQ:START " + str(start_freq))
    self.Send(":FREQ:STOP " + str(stop_freq))
    self.Send(":BAND:RES " + str(rbw))

    sweep_time = float(self.SendReceive(":SWE:TIME?"))
    print sweep_time
    self.Send("*TRG");
    time.sleep(2*sweep_time+3);
    
    return self.GetTrace()

# first argument is IP address of DSA815
if len(sys.argv) == 2:
  dsa = DSA815(sys.argv[1])
else:
  dsa = DSA815('192.168.1.99')

#print dsa.SendReceive('*IDN?')

# reset average
aver_count = 10
dsa.Send(':TRACE1:MODE POWERAVG')
dsa.Send(':TRACE:AVERAGE:COUNT ' + str(aver_count))
time.sleep(1)
dsa.Send(':TRACE:AVERAGE:RESET')
while True:
  n = int(dsa.SendReceive(':TRACE:AVERAGE:COUNT:CURRENT?'))
  sys.stderr.write('n = ' + str(n) + ' averages\n')
  if n == aver_count:
    break
  time.sleep(1)

data =  dsa.GetTrace()
for pair in data:
    (freq, value) = pair
    print freq, value
