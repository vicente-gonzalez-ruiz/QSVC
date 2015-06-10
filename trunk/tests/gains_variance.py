#!/usr/bin/python
# -*- coding: iso-8859-15 -*-



import os
import sys
import math
import statistics
import random
from subprocess import check_call
from subprocess import CalledProcessError
#from MCTF_parser import MCTF_parser


'''
for subband in range (0, 352*288*) :
    random.randrange(256) # Return random value: [0, 255]


# Variance
#---------
def grades_variance(grades):
    average = math.mean(grades)
    variance = 0
    for number in grades:
        variance += ((number - average) ** 2)
    return variance / len(grades)
'''

# Variance signal
#----------------
def variance_signal (file_name) :
    data = []
    file = open (file_name, 'rb')

    byte = file.read(1)
    while str(byte) != "b''" :
        #print ("\nAAAAAA: " + str(byte))
        data.append(ord(byte))
        #print ("\nBBBBBB: " + str(data[len(data)-1]))
        byte = file.read(1)

    file.close()
    return statistics.pvariance(data)
    #return grades_variance(data, mean(data))



# Geometric mean
#---------------
def geomean(num_list):
    productorio = 1
    for num in num_list :
        productorio *= num
    return productorio ** (1.0/len(num_list))



# MAIN
#-----

TRLs = 5
Vx = []
Gx = []

# Variance L
Vx.append ( variance_signal ("low_" + str(TRLs-1)) )

for subband in range (TRLs-1, 0, -1) :

    # Variance Hs
    Vx.append ( variance_signal ("high_" + str(subband)) )
    # Gain
    Gx.append ( statistics.mean(Vx) / geomean(Vx) )

    # Display log
    print ("\nGAINS: " + str(Gx))


exit (0)





'''

cp ~/QSVC/MCTF/trunk/tests/gains_variance.py . ; python3.4 gains_variance.py

'''
