#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# motion_compress_j2k.py

import os
import sys
from subprocess import check_call
from subprocess import CalledProcessError
from MCTF_parser import MCTF_parser

COMPONENTS = 4
BYTES_PER_COMPONENT = 2
BITS_PER_COMPONENT = 16

file = ""
blocks_in_x = 0
blocks_in_y = 0
fields = 0
clayers = 0
quantization = 45000


parser = MCTF_parser(description="Compress the motion data using JPEG 2000.")
parser.add_argument("--blocks_in_x",
                    help="number of blocks in the X direction. (Default = {})".format(blocks_in_x))
parser.add_argument("--blocks_in_y",
                    help="number of blocks in the Y direction. (Default = {})".format(blocks_in_y))
parser.add_argument("--fields",
                    help="number of fields in to compress. (Default = {})".format(fields))
parser.add_argument("--quantization",
                    help="controls the quality level and the bit-rate of the code-stream. (Default = {})".format(quantization))
parser.add_argument("--clayers",
                    help="logarithm controls the quality level and the bit-rate of the code-stream. (Default = {})".format(clayers))
parser.add_argument("--file",
                    help="name of the file with the motion fields. (Default = {})".format(file))

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




dwt_levels = 1 # SRLs - 1 # 
bytes_per_frame = blocks_in_x * blocks_in_y * BYTES_PER_COMPONENT # * COMPONENTS


# Compute file sizes
file_sizes = open (file + ".mjc", 'w')
total = 0

''' # split vs dd (dentro del while)
check_call("split -d -b " + str(bytes_per_field) + " " + file + " " + file, shell=True) # split -d -b 20 w.sh partes_?
'''

# Encode components
image_number = 0
while image_number < fields * 4 :
    #check_call("echo clayers: " + str(clayers), shell=True) #  + " >> output" !!!
    #check_call("echo fields: " + str(fields), shell=True) #  + " >> output"


    # split (fuera del while) vs dd
    image_filename = file + "_" + str('%04d' % image_number)

    try:
        check_call("trace dd" +
                   " if=" + file +
                   " of=" + image_filename + ".rawl" +
                   " bs=" + str(bytes_per_frame) +
                   " count=1" +
                   " skip=" + str(image_number),
                   shell=True)
    except CalledProcessError:
        sys.exit(-1)


    if int(clayers) > 0 :
        try:
            check_call("trace kdu_compress"
                       + " -i " + image_filename + ".rawl"
                       + " -o " + image_filename + ".mjc"
                       + " Creversible=yes"
                       + " -no_weights"
                       + " Sprecision=" + str(BITS_PER_COMPONENT)
                       + " Ssigned=yes"
                       + " Sdims='{'" + str(blocks_in_x) + "," + str(blocks_in_y) + "'}'"
                       + " Clevels=" + str(dwt_levels) # !
                       # + " -slope " + str(quantization),
                       + " Clayers=" + str(clayers),
                       shell=True)
        except CalledProcessError:
            sys.exit(-1)
    else:
        try:
            check_call("trace kdu_compress"
                       + " -i " + image_filename + ".rawl"
                       + " -o " + image_filename + ".mjc"
                       + " Creversible=yes"
                       + " -no_weights"
                       + " Sprecision=" + str(BITS_PER_COMPONENT)
                       + " Ssigned=yes"
                       + " Sdims='{'" + str(blocks_in_x) + "," + str(blocks_in_y) + "'}'"
                       + " Clevels=" + str(dwt_levels) # !
                       + " -slope " + str(quantization),
                       # + " Clayers= + str(clayers)",
                       shell=True)
        except CalledProcessError:
            sys.exit(-1)
    
    '''
    try:
        check_call("trace kdu_compress"
                   + " -i " + image_filename + ".rawl"
                   + " -o " + image_filename + ".mjc"
                   + " Creversible=yes"
                   + " -no_weights"
                   + " Sprecision=" + str(BITS_PER_COMPONENT)
                   + " Ssigned=yes"
                   + " Sdims='{'" + str(blocks_in_x) + "," + str(blocks_in_y) + "'}'"
#                  + " Clevels=" + str(dwt_levels)
                   + " -slope " + str(quantization),
                   shell=True)
    except CalledProcessError:
        sys.exit(-1)

    '''

    total += os.path.getsize(image_filename + ".mjc")
    file_sizes.write(str(total) + "\n")

    image_number += 1

#check_call("echo AQUI", shell=True) #  !!!!
#raw_input("\nFIN\nPress ENTER to continue ...") # !
# sys.exit("\nSTOP !\n")



'''
kdu_compress -i motion_residue_1_0001.raw*4@1584 -o out.jpx Creversible=yes Sdims='{'22,18'}' -jpx_layers 4 Clayers=6 Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes
kdu_compress -i motion_residue_1_0001.raw*4@1584 -o out.jpx Creversible=yes Sdims='{'22,18'}' Clayers=6 Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes
kdu_compress -i motion_residue_1_0001.raw*4@1584 -o out.jpx Creversible=yes Sdims='{'22,18'}' Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes

kdu_compress -i motion_residue_1_0001.raw*4@304128 -o out.jpx Creversible=yes Sdims='{'22,18'}' Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes




kdu_compress -i motion_residue_1_0001.raw*4@396  -o out.jpx Creversible=yes Sdims='{'22,18'}' Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes
'''
