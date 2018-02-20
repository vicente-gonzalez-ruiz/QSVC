#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

## @file motion_compress_j2k.py
#  Compressing the motion vectors, using the codec J2K.
#  The compression consists of two major steps:\n
#  - Demultiplexing components.
#  - Encode components (lossless compression).\n
#
#  Additionally is calculated the size in bytes of motion fields belonging 
#  to each component, each image and each temporal subband.\n It records in 
#  a file that can be consulted later. In these calculations do not take 
#  into account the size of the header of a codestream.
#  @authors Jose Carmelo Maturana-Espinosa\n Vicente Gonzalez-Ruiz.
#  @date Last modification: 2015, January 7.

## @package motion_compress_j2k
#  Compressing the motion vectors, using the codec J2K.
#  The compression consists of two major steps:\n
#  - Demux components.
#  - Encode components (lossless compression).\n
#
#  Additionally is calculated the size in bytes of motion fields belonging 
#  to each component, each image and each temporal subband.\n It records in 
#  a file that can be consulted later. In these calculations do not take 
#  into account the size of the header of a codestream.


import os
import sys
import subprocess  as     sub
from   subprocess  import check_call
from   subprocess  import CalledProcessError
from   MCTF_parser import MCTF_parser
from PIL import Image, ImageChops, ImageEnhance, ImageOps

## Number of components of a motion field.
COMPONENTS          = 4
## Number of bytes for each component.
BYTES_PER_COMPONENT = 2
## Number of bits for each component.
BITS_PER_COMPONENT  = BYTES_PER_COMPONENT * 8
## Name of the file with the motion fields.
file         = ""
## Width of the pictures.
blocks_in_x  = 0
## Height of the pictures.
blocks_in_y  = 0
## Number of fields in to compress.
fields       = 0
## Logarithm controls the quality level and the bit-rate of the
#  code-stream used for the motion vectors. Used only 1 because we
#  have seen that compress motion information with loss, is not
#  helpful.
clayers      = 1
## Vector quantization. Normally does not apply, since the motion
#  information is compressed without loss.
quantization = 45000
## Number of Spatial Resolution Levels. Normally it does not apply,
#  since the vectors are usually compress and decompress at the same
#  spatial resolution.
SRLs         = 5

## The parser module provides an interface to Python's internal parser
#  and byte-code compiler.
parser = MCTF_parser(description="Compress the motion data using JPEG 2000.")
parser.add_argument("--blocks_in_x",   help="number of blocks in the X direction. (Default = {})".format(blocks_in_x))
parser.add_argument("--blocks_in_y",   help="number of blocks in the Y direction. (Default = {})".format(blocks_in_y))
parser.add_argument("--fields",        help="number of fields in to compress. (Default = {})".format(fields))
parser.add_argument("--quantization",  help="controls the quality level and the bit-rate of the code-stream. (Default = {})".format(quantization))
parser.add_argument("--clayers",       help="logarithm controls the quality level and the bit-rate of the code-stream. (Default = {})".format(clayers))
parser.add_argument("--file",          help="name of the file with the motion fields. (Default = {})".format(file))

## A script may only parse a few of the command-line arguments,
#  passing the remaining arguments on to another script or program.
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



## Number of levels of the DWT to be applied in compression.
dwt_levels = 0 # 1 # SRLs - 1
## Number of bytes required by the movement information (uncompressed)
#  for each image.
bytes_compF = blocks_in_x * blocks_in_y * BYTES_PER_COMPONENT


for comp_number in range (0, COMPONENTS) :

    # DEMUX components.
    #------------------
    try :
        check_call("trace demux " + str(COMPONENTS * BYTES_PER_COMPONENT) + " " + str(comp_number * BYTES_PER_COMPONENT) + " " + str(BYTES_PER_COMPONENT)
                   + " < " + file
                   + " | /usr/bin/split --numeric-suffixes --suffix-length=4 "
                   + "--bytes=" + str(bytes_compF) + " - " + file + "_comp" + str(comp_number) + "_" # .rawl aqu�!
                   , shell=True)
    except CalledProcessError:
        sys.exit(-1)


    # ENCODE components.
    #-------------------
    ## Refers to a particular component from a field of movement.
    campoMov_number = 0
    while campoMov_number < fields :

        ## Name of the file containing the data of movement of a
        #  component of a desired image and a specific subband.
        campoMov_name = file + "_comp" + str(comp_number) + "_" + str('%04d' % campoMov_number)

        try:
            check_call("mv " + campoMov_name + " " + campoMov_name + ".rawl"
                       , shell=True)
        except CalledProcessError:
            sys.exit(-1)

        try:
            # Compress.
            #----------
            check_call("trace kdu_compress"
                       + " -i "          + campoMov_name + ".rawl"
                       + " -o "          + campoMov_name + ".j2c"
                       + " -no_weights"
                       + " Creversible=" + "yes" # "no" "yes" # Da igual como est� al usar el kernel descrito
                       + " Sprecision="  + str(BITS_PER_COMPONENT)
                       + " Ssigned="     + "yes"
                       + " Sdims='{'"    + str(blocks_in_y) + "," + str(blocks_in_x) + "'}'"
                       + " Clevels="     + str(dwt_levels)
                       + " Cuse_sop="    + "yes"
                       + " Catk=2 Kextension:I2=CON Kreversible:I2=yes Ksteps:I2=\{1,0,0,0\},\{1,0,1,1\} Kcoeffs:I2=-1.0,0.5"
                       , shell=True)
            # An alternative to compress the motion vectors:
            # kdu_compress -i mini_motion_4.rawl -o mini_motion_4.j2c
            # -no_weights Sprecision=16 Ssigned=yes Sdims='{'4,4'}'
            # Clevels=1 Catk=2 Kextension:I2=CON Kreversible:I2=yes
            # Ksteps:I2=\{1,0,0,0\},\{1,0,1,1\} Kcoeffs:I2=-1.0,0.5

        except CalledProcessError:
            sys.exit(-1)

        campoMov_number += 1



## Determines the size of the header of a codestream.
#  @param file_name Name of the file with the motion fields.
#  @return Bytes of the header of a codestream.
def header (file_name) :
    p = sub.Popen("header_size " + str(file_name) + " 2> /dev/null | grep OUT", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    out, err = p.communicate()
    return long(out[4:])



## Records motion size information in a file that can be consulted
#  later.
file_sizes = open (file + ".mjc", 'w') # Compute file sizes
## Determines the size in bytes of motion fields belonging to each 
#  component, each image and each temporal subband.
total = 0
for campoMov_number in range (0, fields) :
    for comp_number in range (0, COMPONENTS) :
        ## Name of the file containing the data of movement of a
        #  component of a desired image and a specific subband.
        name  = file + "_comp" + str(comp_number) + "_" + str('%04d' % campoMov_number)
        total = total + os.path.getsize(name + ".j2c") - header(name + ".j2c")
    file_sizes.write(str(total) + "\n")
