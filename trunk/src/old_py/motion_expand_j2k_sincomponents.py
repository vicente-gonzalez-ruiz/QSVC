#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# motion_expand_j2k.py

import os
import sys
from subprocess import check_call
from subprocess import CalledProcessError
from MCTF_parser import MCTF_parser

COMPONENTS = 4
BITS_COMPONENT = 16
BYTES_COMPONENT = 2

blocks_in_x = 0
blocks_in_y = 0
fields = 0
file = ""
discard_levels = 0

parser = MCTF_parser(description="Expands the motion data using JPEG 2000.")
#parser.add_argument("--discard_levels",
#                    help="number of discard level. (Default = {})".format(discard_levels))
parser.add_argument("--blocks_in_x",
                    help="number of blocks in the X direction. (Default = {})".format(blocks_in_x))
parser.add_argument("--blocks_in_y",
                    help="number of blocks in the Y direction. (Default = {})".format(blocks_in_y))
parser.add_argument("--fields",
                    help="number of fields in to compress. (Default = {})".format(fields))
parser.add_argument("--file",
                    help="name of the file with the motion fields. (Default = {})".format(file))

args = parser.parse_known_args()[0]
#if args.discard_levels:
#    discard_levels = int(args.discard_levels)
if args.blocks_in_x:
    blocks_in_x = int(args.blocks_in_x)
if args.blocks_in_y:
    blocks_in_y = int(args.blocks_in_y)
if args.fields:
    fields = int(args.fields)
if args.file:
    file = args.file




#check_call("echo ANTES!", shell=True)
#raw_input("")


##########
# expand #
##########
try:
    f = open(file + ".mjc", "rb")
    f.close()

    # Expand
    check_call("trace kdu_v_expand -disjoint_frames"
               + " -i " + file + ".mjc"
               + " -o " + file + ".vix"
               , shell=True)
    
    # Elimina la cabecera .vix
    check_call("mctf vix2raw < "
               + file + ".vix > "
               + file
               , shell=True)

except: # Jse. Sino existe se crea a movimiento lineal
    check_call("echo ESTA INTERPOLANDO!", shell=True)
    raw_input("")

    f = open(file, "wb")
    for a in xrange(COMPONENTS * BYTES_COMPONENT * blocks_in_y * blocks_in_x * fields) :
        f.write('%c' % 0)
    f.close()

#check_call("echo DESPUES!", shell=True)
#raw_input("")
