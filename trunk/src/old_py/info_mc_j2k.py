#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

## @file info_mc_j2k.py
#  The size in bytes, and a codestream Kbps, even detailed subband
#  level and neglecting headers, from a MCJ2K codestream.
#
#  @authors Jose Carmelo Maturana-Espinosa\n Vicente Gonzalez-Ruiz.
#  @date Last modification: 2015, January 7.
#
## @package info_mc_j2k
#  The size in bytes, and a codestream Kbps, even detailed subband
#  level and neglecting headers, from a MCJ2K codestream.


import sys
import os
import re
import math
import os.path
from GOP import GOP
from subprocess import check_call
from subprocess import CalledProcessError
from MCTF_parser import MCTF_parser

## Refers to high frequency subbands.
HIGH = "high_"
## Refers to low frequency subbands.
LOW = "low_"
## Refers to fields of motion.
MOTION = "motion_residue_"
## Indicates whether a log is recorded in a file.
print_file = False
## Number of Group Of Pictures to process.
GOPs = 1
## Number of Temporal Resolution Levels.
TRLs = 5
## Frames per second.
FPS = 30 # 30 # 50


## The parser module provides an interface to Python's internal parser
## and byte-code compiler.
parser = MCTF_parser(description="Information of codestream.")
parser.GOPs(GOPs)
parser.FPS(FPS)

## A script may only parse a few of the command-line arguments,
## passing the remaining arguments on to another script or program.
args = parser.parse_known_args()[0]
if args.GOPs :
    GOPs = int(args.GOPs)
if args.TRLs:
    TRLs = int(args.TRLs)
if args.FPS :
    FPS = int(args.FPS)


## Initializes the class GOP (Group Of Pictures).
gop=GOP()
## Extract the value of the size of a GOP, that is, the number of images.
GOP_size = gop.get_size(TRLs)
## Calculate the total number of video images.
pictures = GOPs * GOP_size + 1
## Duration of the sequence.
duration = pictures / (FPS * 1.0)



## Number of bytes of an entire directory. The size in bytes, and a
## codestream Kbps, even detailed subband level and neglecting headers
## is performed in info.py.
#  @param the_path Directory path.
#  @param key If you want to have only a certain type of files in the directory.
#  @return Files size.
def get_size (the_path, key) :

    path_size = 0
    for path, dirs, files in os.walk(the_path) :
        for fil in files :
            if re.search(key, fil) :
                path_size += os.path.getsize(the_path + "/" + fil)
        return path_size






#-----------------------------------------------
#-----------------------------------------------
#- MAIN ----------------------------------------
#-----------------------------------------------
#-----------------------------------------------


# info = [[kbps GOP1, kbps GOP2, kbps GOPn], kbps GOPs, rmse1D]


## Current path.
p = sub.Popen("echo $PWD", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
out, err = p.communicate()
## Reconstruction path.
path_tmp = out[:-1]



########
# RMSE #
########
# Existe la reconstrucción. Entonces se calcula su distorsión.
if os.path.exists(path_tmp + "/low_0") :

    ##########
    # SNR 1D #
    ##########

    # BRC y UnaSubParaTodas
    p = sub.Popen("snr --file_A=low_0 --file_B=../low_0 2> /dev/null | grep RMSE | cut -f 3",
                  shell=True, stdout=sub.PIPE, stderr=sub.PIPE)

    # subIndependientes
    #p = sub.Popen("snr --file_A=high_4 --file_B=../high_4 2> /dev/null | grep RMSE | cut -f 3",
    #              shell=True, stdout=sub.PIPE, stderr=sub.PIPE)


    out, err = p.communicate()
    #errcode = p.returncode
    
    if out == "" : #if err in locals() :
        check_call("echo SNR sin salida.", shell=True)
        exit (0)

    rmse1D = float(out)

    ##########
    # SNR 2D #
    ##########
    #rmse2D=`snr2D --block_size=$block_size_snr --dim_X=$RES_X --dim_Y=$RES_Y --file_A=$DATA/$VIDEO.yuv --file_B=$data_dir/tmp/low_0_UP --FFT 2>  /dev/null | grep RMSE | cut -f 3` # FFT en 3D

    ##########
    # SNR 3D #
    ##########
    #rmse3D=`snr3D --block_size=$block_size_snr --dim_X=$RES_X --dim_Y=$RES_Y --dim_Z=5 --file_A=$DATA/$VIDEO.yuv --file_B=$data_dir/tmp/low_0_UP --FFT 2> /dev/null | grep RMSE | cut -f 3` # FFT en 3D


    ####################
    # export variables #
    ####################
    globals()["info_rmse1D"] = rmse1D #p = sub.Popen("export info_mc_j2k_rmse1D=" + rmse1D, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)


    info[2] = rmse1D



    # info = [[kbps GOP1, kbps GOP2, kbps GOPn], kbps GOPs, rmse1D]
    if not 'info' in globals() :
        globals()["info"] = [[]]


    ###################
    # Print a fichero #
    ###################

    #########################
    # Media Pts de cada GOP #
    #########################
    for par in range (0, len(info[0])) :
        info[1] = Pts_GOPs[par]


    check_call("echo \"" + Pts_GOPs         + "\" >> ../info_PtsGOPs", shell=True)            #BASH: check_call("echo \"" + ${PtsGOPs[@]} + "\" >> ../info_PtsGOPs", shell=True)
    check_call("echo \"" + average_Pts_GOPs + "\" >> ../info_average_PtsGOPs", shell=True)



########
# KBPS #
########
# No existe la reconstrucción. Entonces se calculan los kbps del codestream aún comprimido.
else :
    TO_KBPS = 8.0 / duration / 1000

    ############
    # KBPS GOP #
    ############
    nGOP = 1
    while nGOP <= GOPs :

        # H's
        subband = TRLs - 1
        nImage = 0
        pictures_sub = GOP_size
        while subband > 0 :
            pictures_sub = ( pictures_sub + 1 ) / 2

            # SIZES MOTION un GOP #
            _kbps_M.append( get_size(path_tmp, MOTION + str(subband) + "_*_[" + str('%04d'%(nImage*1)) + "-" + str('%04d'%pictures_sub) + "].j2c") * TO_KBPS )

            # SIZES H's un GOP #

            # SIZES L un GOP #


            subband -= 1
        nImage = pictures_sub

        # L


        # SUMATORIA #

        print ("sumatoria size de este GOP. Y apuntarlo.")
        nGOP += 1





    ##########################################


    # M
    kbps_M = get_size(path_tmp, MOTION) * TO_KBPS

    # T 1ªL (fuera del GOP)
    kbps_T_first_L = [ get_size(path_tmp, LOW + str(TRLs-1) + "_[YUV]_0000.j2c") * TO_KBPS ]

    # T L (la del GOP)
    _kbps_T = [ get_size(path_tmp, LOW + str(TRLs-1) + "_[YUV]_000?.j2c") * TO_KBPS ]
    # = [ get_size(path_extract, LOW) ] (las imagenes de 2 L)

    # T (Hs)
    for i in range (1, TRLs) :
        _kbps_T.append( get_size(path_tmp, HIGH + str(TRLs - i)) * TO_KBPS )

    # T del GOP (2ªL + Hs)
    _kbps_T.append( _kbps_T[0] + (get_size(path_tmp, HIGH) * TO_KBPS) )
    # kbps_GOP (M + T)
    kbps_GOP = kbps_M + _kbps_T[TRLs]

    # kbps_ALL (M + T). Siendo T = con 1ªL + types
    bytes_mj2k = get_size(path_tmp, "")
    kbps_ALL = bytes_mj2k * TO_KBPS



    ####################
    # export variables #
    ####################
    globals()["info_kbps_M"]   = kbps_M
    globals()["info_kbps_T"]   = _kbps_T
    globals()["info_kbps_GOP"] = kbps_GOP
    globals()["info_kbps_ALL"] = kbps_ALL









''' ##############
NOTAS DEL CODIGO #
''' ##############

'''
    #POR BASH
    #p = sub.Popen("export info_mc_j2k_kbps_M="   + kbps_M   + "; "
    #              "export info_mc_j2k_kbps_T="   + _kbps_T  + "; "
    #              "export info_mc_j2k_kbps_GOP=" + kbps_GOP + "; "
    #              "export info_mc_j2k_kbps_ALL=" + kbps_ALL
    #              , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    #out, err = p.communicate()
    ##errcode = p.returncode

    #POR PYTHON
'''


'''
import re
import os
path_size = 0
for path, dirs, files in os.walk("/home/cmaturana") :
    for fil in files :
        if re.search("aaa0[2-3]", fil) :
            path_size += os.path.getsize("/home/cmaturana" + "/" + fil)
path_size


http://www.tutorialspoint.com/python/python_reg_expressions.htm
'''
