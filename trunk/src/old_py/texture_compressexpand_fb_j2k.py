#!/usr/bin/python
# -*- coding: iso-8859-15 -*-






########### COMPRESS


'''
#######
# PGM #
#######

        # to pgm
        try:
            check_call("trace rawtopgm "
                       + str(sDimX) + " " + str(sDimY)
                       + " < " + image_filename
                       + " > " + image_filename + ".pgm"
                       , shell=True)
        except CalledProcessError:
            sys.exit(-1)

        # kdu
        try:
            check_call("trace kdu_compress"
                       + " -i " + image_filename + ".pgm"
                       + " -o " + image_filename + ".j2c"
                       + " -slope " + quantization
                       + " -no_weights"
                       + " Clevels=" + str(dwt_levels)
                       , shell=True)
        except CalledProcessError:
            sys.exit(-1)
'''









########## EXPAND


'''
import math
import struct

a = 382
b = 3
c = 678

pack_a = struct.pack('H',a)
pack_b = struct.pack('H',b)
pack_c = struct.pack('H',c)

with open('data.bin','wb') as f :
    #f.write(pack_a)
    f.write(pack_b)
    #f.write(pack_c)
    f.close()

with open('data.bin','rb') as f :
    bin_data = f.read(2)
    while bin_data != "" :
        
        print 'Value from file:',struct.unpack('H',bin_data)
        print 'Value from file:',struct.unpack('H',bin_data)[0]
        
        print "bin_data representation:"
        for i,c in enumerate(bin_data):
            print 'Byte {0} as binary: {1:08b}'.format(i,ord(c))
        
        print 'Byte 0 as binary: {1:08b}'.format(0,ord(bin_data[0]))
        print 'Byte 1 as binary: {1:08b}'.format(1,ord(bin_data[1])) 
        
        print 'Byte 0:', ord(bin_data[0])
        print 'Byte 1:', ord(bin_data[1])
        
        print 'Byte 0:', bin_data[0]
        print 'Byte 1:', bin_data[1]
        
        print 'Bytes:', bin_data[1] + bin_data[0]
        bin_data = f.read(2)
    f.close()



# 776 = "\x03\x08"


import struct

bin_data = struct.pack('H',333)

with open('f_in','wb') as f :
    f.write(bin_data[1]) # Ej: 3 = bin_data[1] bin_data[0] = 00000000 00000011
    f.write(bin_data[0])
    f.close()

with open('f_in','rb') as f :
    bytes = f.read(2)
    bytes[0]
    bytes[1]
    
    while bytes != "" :
        data_comp = ord(bytes[0])*256 + ord(bytes[1])
        print "data_comp: " + str(data_comp)
        
        with open('f_out','wb') as f_out :
            f_out.write(chr(data_comp))
        
        bytes = f.read(2)
    
    f.close()
    f_out.close()


#####################################################

#A)
#f_out.write(data[0]) # 0 # snr 4.738
bin_data = struct.pack('H', int(desmult_comp))
f_out.write(bin_data[0]) # 0 # snr 4.738
            

#####################################################
import struct

bin_data1 = struct.pack('<H',1303)
bin_data2 = struct.pack('<H',2275)
with open('in.raw','wb') as f :
    f.write(bin_data1[0]) # Ej: 3 = bin_data[1] bin_data[0] = 00000000 00000011
    f.write(bin_data1[1])
    f.write(bin_data2[0])
    f.write(bin_data2[1])
    f.close()

f_out = open('out.raw','wb')
with open('in.raw','rb') as f :
    bytes = f.read(2)
    #bytes[0]
    #bytes[1]
    
    while bytes != "" :
        data_comp = ord(bytes[1])*256 + ord(bytes[0])
        
        print "data_comp: " + str(data_comp)
        
        #f_out.write(chr(data_comp))
        
        bytes = f.read(2)
    
    f.close()
    f_out.close()
'''
