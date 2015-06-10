#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# motion_compress_j2k.py

import os
import sys
from subprocess import check_call
from subprocess import CalledProcessError
from MCTF_parser import MCTF_parser

COMPONENTS          = 4
BYTES_PER_COMPONENT = 2
BITS_PER_COMPONENT  = BYTES_PER_COMPONENT * 8

file         = ""
blocks_in_x  = 0
blocks_in_y  = 0
fields       = 0
clayers      = 1
quantization = 45000
SRLs         = 5

parser = MCTF_parser(description="Compress the motion data using JPEG 2000.")
parser.add_argument("--blocks_in_x",   help="number of blocks in the X direction. (Default = {})".format(blocks_in_x))
parser.add_argument("--blocks_in_y",   help="number of blocks in the Y direction. (Default = {})".format(blocks_in_y))
parser.add_argument("--fields",        help="number of fields in to compress. (Default = {})".format(fields))
parser.add_argument("--quantization",  help="controls the quality level and the bit-rate of the code-stream. (Default = {})".format(quantization))
parser.add_argument("--clayers",       help="logarithm controls the quality level and the bit-rate of the code-stream. (Default = {})".format(clayers))
parser.add_argument("--file",          help="name of the file with the motion fields. (Default = {})".format(file))

args = parser.parse_known_args()[0]
if args.blocks_in_x:
    blocks_in_x = int(args.blocks_in_x)
if args.blocks_in_y:
    blocks_in_y = int(args.blocks_in_y)
if args.fields:
    fields = int(args.fields)
if args.clayers:
    clayers = str(args.clayers)
if args.quantization:
    quantization = str(args.quantization)
if args.file:
    file = args.file

#check_call("echo file: " + str(file) + " >> out", shell=True)

#dwt_levels  = 1 # SRLs - 1

#check_call("echo motion_compress_j2k.py", shell=True)
#raw_input("")

##########
# Encode #
##########

# Generamos la cabecera VIX
fd = open( file + ".vix", 'w' )
fd.write("vix\n")
fd.write(">VIDEO<\n")
fd.write("1.0 0\n")
fd.write(">COLOUR<\n")
fd.write("RGB\n")
fd.write(">IMAGE<\n")
#fd.write("unsigned char 4 little-endian\n")
fd.write("signed word " + str(BITS_PER_COMPONENT) + " little-endian\n")
#fd.write("unsigned char 8 little-endian\n")
# Sí, ya se que es imposible, pero si ponemos signed, el Kakadu no funciona
fd.write("%d " % blocks_in_x)
fd.write("%d " % blocks_in_y)
fd.write("4\n" )
fd.write("1 1\n")
fd.write("1 1\n")
fd.write("1 1\n")
fd.write("1 1\n")
fd.close()

# Concatena los campos de movimiento a la cabecera VIX.
try:
    check_call("trace cat " + file + " >> " + file + ".vix", shell=True)
except CalledProcessError:
    sys.exit(-1)

# Comprime
try:
    check_call("trace kdu_v_compress Clevels=0 Creversible=yes Clayers=0 Cblk=\{64,64\}"
               + " -i " + file + ".vix"
               + " -o " + file + ".mjc",
               shell=True)
except CalledProcessError:
    sys.exit(-1)


#########
# SIZES #
#########
file_sizes = open (file + ".mjc_sizes", 'w')
file_sizes.write(str(os.path.getsize(file + ".mjc")) + "\n") # Compute file sizes
file_sizes.close()



'''
try:
    check_call("mv " + file + " " + file + ".rawl", shell=True)
except CalledProcessError:
    sys.exit(-1)

'''
