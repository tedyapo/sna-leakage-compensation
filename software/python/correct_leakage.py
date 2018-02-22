#!/usr/bin/env python
#
# one- or two-calibration SNA leakage compensation
#
# run with:
#   ./correct_leakage.py <data_directory> <base_name>
#
# example:
#  ./correct_leakage.py ../data/attenuator/ 70db

import sys
import numpy as np
import matplotlib.pyplot as plt

data_dir = sys.argv[1] + '/'
base_name = sys.argv[2]

if 'preamp' in base_name:
  noise_floor = np.loadtxt(data_dir + 'noise_floor_preamp.dat')
  leakage = np.loadtxt(data_dir + 'leakage_preamp.dat')
else:
  noise_floor = np.loadtxt(data_dir + 'noise_floor.dat')
  leakage = np.loadtxt(data_dir + 'leakage.dat')
through_A = np.loadtxt(data_dir + 'through_a.dat')
through_B = np.loadtxt(data_dir + 'through_b.dat')
meas_A = np.loadtxt(data_dir + base_name + '_a.dat')
meas_B = np.loadtxt(data_dir + base_name + '_b.dat')

def dBm_to_Vpk(dB):
  return np.sqrt(np.power(10., dB/10.) / 10.)

def Vpk_to_dBm(Vpk):
  return 10.*np.log10(1000. * np.square(Vpk/np.sqrt(2.)) / 50.)

def nf_correct(nf, v):
  return np.sqrt(np.square(v) - np.square(nf))

frequency = leakage[1:,0]
NF = dBm_to_Vpk(noise_floor[1:,1])
GL = nf_correct(NF, dBm_to_Vpk(leakage[1:,1]))
GAT = nf_correct(NF, dBm_to_Vpk(through_A[1:,1]))
GBT = nf_correct(NF, dBm_to_Vpk(through_B[1:,1]))
GA = nf_correct(NF, dBm_to_Vpk(meas_A[1:, 1]))
GB = nf_correct(NF, dBm_to_Vpk(meas_B[1:, 1]))

# one-cal solution
a0_1 = ( np.sqrt(np.abs(np.square(GA) + np.square(GB) - 2. * np.square(GL))) /
         (np.sqrt(2.) * GAT) );

# two-cal solution
a0_2 = ((+GAT*np.square(GB) 
      + GBT*np.square(GA) 
       - np.square(GL)*(GBT+GAT))
      /(GAT*GBT*(GBT + GAT)))
a0_2 = np.sqrt(np.abs(a0_2))

# normalize so (a0 = 1.0) --> 0 dBm
# 0 = log10(1000 * Vrms^2/50), Vpk = Vrms*sqrt(2)
a0_1_n = np.sqrt(0.1) * a0_1;
a0_2_n = np.sqrt(0.1) * a0_2;

# save corrected |S21| estimates
a0_onecal = Vpk_to_dBm(a0_1_n)
a0_twocal = Vpk_to_dBm(a0_2_n)
np.savetxt(data_dir + base_name + '_onecal.dat',
           np.stack((frequency, a0_onecal), axis=-1))
np.savetxt(data_dir + base_name + '_twocal.dat',
           np.stack((frequency, a0_twocal), axis=-1))

plt.plot(frequency, Vpk_to_dBm(a0_1_n))
plt.plot(frequency, Vpk_to_dBm(a0_2_n))

plt.show()
