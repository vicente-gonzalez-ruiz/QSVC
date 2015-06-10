#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# motion_expand_j2k.py

import os
import sys
from subprocess import check_call
from subprocess import CalledProcessError
from MCTF_parser import MCTF_parser

COMPONENTS = 4

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





# EXPAND DE CADA IMAGEN DE VECTORES.
image_number = 0
while image_number < (fields * COMPONENTS) :

    # print "expand: " + file + str('%04d' % image_number) + ".mjc"

    # l) kdu_expand -i out.jpx -o out.raw -jpx_layer 2
    # m) kdu_expand -i out.jpx -o out.raw -raw_components 5 -skip_components 2

    # kdu_expand -i out.jpx -o out.raw -raw_components 4


    # Jse. Sino existe se crea a movimiento lineal 
    # (no se comprueba si existe el H_maximo donde apoyar dicho movimiento):
    try:
        f = open(file + "_" + str('%04d' % image_number) + ".mjc", "rb")
        f.close()

        try: # expand
            check_call("trace kdu_expand"
                       + " -i " + file + "_" + str('%04d' % image_number) + ".mjc"
                       + " -o " + file + "_" + str('%04d' % image_number) + ".rawl",
                       shell=True)
        except CalledProcessError:
            sys.exit(-1)

    except:
        f = open(file + "_" + str('%04d' % image_number) + ".rawl", "wb")
        for a in xrange(fields * blocks_in_y * blocks_in_x):
            f.write('%c' % 0)
        f.close()


    image_number += 1

# MERGE DE TODAS LAS IMÁGENES DEL ACTUAL TRL.
print "cat " + file + "_*.rawl > " + file

check_call("trace cat " + file + "_*.rawl > " + file, shell=True)

#print "Press ENTER to continue ... "
#raw_input("Press ENTER to continue ...") # !


