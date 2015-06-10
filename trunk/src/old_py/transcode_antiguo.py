#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# extract.py
#
# Extracts a codestream from a bigger codestream, discarding a number
# of temporal, resolution or/and quality. The number of temporal
# resolution levels that is going to be discardes must be >= 0 (0 = no
# discarding). Some thing similar happens with the number of discardes
# spatial resolutions. The last parameter is controlled by means of a
# slope, a value between 0 a 65535 where 0 means no discarding and
# 65553 implies a null output video, but notice that if the input
# video was quantized using a slope X and we select a new slope where
# Y <= X, then, this extraction will not have any effect (the output
# will be identical to the input). These parameters can not be used
# simultaneously, but obviously, they can be concatenated. The output
# sequences will overwrite the input sequences.
#
# Examples:
#
# mcj2k transcode --discard_TRLs=1 # Divides the frame-rate by two.
# mcj2k transcode --discard_SRLs=2 # Divides the spatial resolution of the video by 2^2 in each dimmension
# mcj2k transcode --new_slope=45000 # Selects the new slope (quality) 45000
# mcj2k transcode --GOPs=1 # Outputs only the first GOP (only one image)
#

import sys
import getopt
import os
import array
import display
import string
from GOP import GOP
from subprocess import check_call
from subprocess import CalledProcessError
from MCTF_parser import MCTF_parser

HIGH = "high_"
LOW = "low_"

discard_TRLs=0
discard_SRLs_Tex=0
discard_SRLs_Mot=0
new_slope = 45000
GOPs = 1
TRLs = 6
List_Clayers = "11111"


parser = MCTF_parser(description="Transcode.")
parser.add_argument("--discard_TRLs",
                    help="number of discarded temporal resolution levels. (Default = {})".format(discard_TRLs))
parser.add_argument("--discard_SRLs_Tex",
                    help="number of discarded spatial resolution levels for textures. (Default = {})".format(discard_SRLs_Tex))
parser.add_argument("--discard_SRLs_Mot",
                    help="number of discarded spatial resolution levels for motions. (Default = {})".format(discard_SRLs_Mot))
parser.add_argument("--new_slope",
                    help="new slope. (Default = {})".format(new_slope))
parser.add_argument("--GOPs",
                    help="number of GOPs to process. (Default = {})".format(GOPs))
parser.add_argument("--TRLs",
                    help="number of iterations of the temporal transform + 1. (Default = {})".format(TRLs))
parser.add_argument("--List_Clayers",
                    help="Number of quality layers of subband of the textures and motion. May not exceed 16384. (Default = {})".format(List_Clayers))

args = parser.parse_known_args()[0]
if args.discard_TRLs:
    discard_TRLs = int(args.discard_TRLs)
if args.discard_SRLs_Tex:
    discard_SRLs_Tex = int(args.discard_SRLs_Tex)
if args.discard_SRLs_Mot:
    discard_SRLs_Mot = int(args.discard_SRLs_Mot)
if args.new_slope:
    new_slope = int(args.new_slope)
if args.GOPs:
    GOPs = int(args.GOPs)
if args.TRLs:
    TRLs = int(args.TRLs)
if args.List_Clayers:
    List_Clayers = str(args.List_Clayers)

###
#check_call("echo List_Clayers: " + str(List_Clayers) + " " +  str(TRLs), shell=True) #  + " >> output" !!!
#raw_input("Press ENTER to continue ...") # !
#



# Code: Implementa la extracción por niveles de resolución y capas de calidad.

# Inicialization. Jse
gop=GOP()
GOP_size = gop.get_size(TRLs)
pictures = GOPs * GOP_size + 1
fields = pictures / 2

check_call("mkdir extract", shell=True)


#############  #################
#        FUNCTIONS             #
#############  #################

def kdu_transcode (filename, Clayers, discard_SRLs): # kdu_transcode -usage | less
    try:
        check_call("trace kdu_transcode Clayers=" + str(Clayers)
                   + " -i " + filename
                   + " -o " + "extract/" + filename
                   + " -reduce " + str(discard_SRLs),
                   shell=True)
    except CalledProcessError:
        sys.exit(-1)


#############  #################
#          MOTIONS             #
#############  #################
"""
subband = 1
while subband < TRLs:
    print "MOTION: subband=" + str(subband) # !
    print "clayer=" + List_Clayers[(TRLs+subband)-1] # !

    image_number = 0
    while image_number < fields * 4 :
        kdu_transcode ("motion_residue_" + str(subband) + "_" + str('%04d' % image_number) + ".mjc", List_Clayers[(TRLs+subband)-1], discard_SRLs_Mot)
        image_number += 1

    subband += 1
    fields /= 2
"""
#############  #################
#         TEXTURES             #
#############  #################

# Procesa las subbandas de ALTA frecuencia.
subband = 1
while subband < TRLs:

    # Open the file with the size of each color image
    file_sizes = open ("extract/" + HIGH + str(subband) + ".j2c", 'w')
    total = 0

    pictures = (pictures + 1) / 2

    image_number = 0
    while image_number < (pictures - 1):
        str_image_number = '%04d' % image_number

        # Y
        filename = HIGH + str(subband) + "_Y_" + str_image_number 
        kdu_transcode (filename + ".j2c", List_Clayers[TRLs-subband], discard_SRLs_Tex)
        Ysize = os.path.getsize("extract/" + filename + ".j2c") # Recompute file-size

        # U
        filename = HIGH + str(subband) + "_U_" + str_image_number 
        kdu_transcode (filename + ".j2c", List_Clayers[TRLs-subband], discard_SRLs_Tex)
        Usize = os.path.getsize("extract/" + filename + ".j2c")

        # V
        filename = HIGH + str(subband) + "_V_" + str_image_number
        kdu_transcode (filename + ".j2c", List_Clayers[TRLs-subband], discard_SRLs_Tex)
        Vsize = os.path.getsize("extract/" + filename + ".j2c")

        # Total file-sizes
        size = Ysize + Usize + Vsize
        total += size
        file_sizes.write(str(total) + "\n")

        image_number += 1


        ###
        #check_call("echo TRLs: " + str(TRLs) + " subband: " + str(subband) + " List_Clayers[TRLs-subband]: " + str(List_Clayers[TRLs-subband]), shell=True) #  + " >> output" !!!
        #raw_input("Press ENTER to continue ...") # !
        #

    file_sizes.close()
    subband += 1



subband -= 1



# Procesa la subbanda de BAJA frecuencia.
# Open the file with the size of each color image
file_sizes = open ("extract/" + LOW + str(subband) + ".j2c", 'w')
total = 0

image_number = 0
while image_number < pictures:

    str_image_number = '%04d' % image_number

    # Y
    filename = LOW + str(subband) + "_Y_" + str_image_number
    kdu_transcode (filename + ".j2c", List_Clayers[0], discard_SRLs_Tex)
    Ysize = os.path.getsize("extract/" + filename + ".j2c")

    # U
    filename = LOW + str(subband) + "_U_" + str_image_number
    kdu_transcode (filename + ".j2c", List_Clayers[0], discard_SRLs_Tex)
    Usize = os.path.getsize("extract/" + filename + ".j2c")

    # V
    filename = LOW + str(subband) + "_V_" + str_image_number
    kdu_transcode (filename + ".j2c", List_Clayers[0], discard_SRLs_Tex)
    Vsize = os.path.getsize("extract/" + filename + ".j2c")

    # Total file-sizes
    size = Ysize + Usize + Vsize
    total += size
    file_sizes.write(str(total) + "\n")


    ###
    #check_call("echo TRLs: " + str(TRLs) + " subband: " + str(subband) + " List_Clayers[TRLs-subband]: " + str(List_Clayers[TRLs-subband]), shell=True) #  + " >> output" !!!
    #raw_input("Press ENTER to continue ...") # !
    #

    image_number += 1


file_sizes.close()
