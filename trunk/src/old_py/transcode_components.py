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

import info_j2k
import sys
import getopt
import os
import array
import display
import string
import math
import re
import subprocess as sub
from GOP          import GOP
from subprocess   import check_call
from subprocess   import CalledProcessError
from MCTF_parser  import MCTF_parser


HIGH              = "high_"
LOW               = "low_"
MOTION            = "motion_"
MOTION_COMPONENTS = 4
MAX_VALUE         = 2000000000

GOPs              = 1
TRLs              = 4
SRLs              = 5
BRC               = MAX_VALUE
discard_TRLs      = 0
discard_SRLs      = "0,0,0,0,0,0,0,0,0"
pixels_in_x       = 352  # 352 # 1920
pixels_in_y       = 288  # 288 # 1088
FPS               = 30   # 30 # 50
block_size        = 32   # 32 # 64
block_size_min    = 32   # 32 # 64
search_range      = 4
nLayers           = 1
new_slope         = 45000
update_factor     = 1.0/4


parser = MCTF_parser(description="Transcode.")
parser.add_argument("--GOPs", help="number of GOPs to process. (Default = {})".format(GOPs))
parser.add_argument("--TRLs", help="number of iterations of the temporal transform + 1. (Default = {})".format(TRLs))
parser.SRLs(SRLs)
parser.add_argument("--BRC",  help="bit-rate control (kbps). (Default = {})".format(BRC))
parser.add_argument("--discard_TRLs", help="number of discarded temporal resolution levels. (Default = {})".format(discard_TRLs))
parser.add_argument("--discard_SRLs", help="List of discarded spatial resolution levels for textures and motions. Example: for TRL=3 there are 5 discarded, these values correspond to L2, H2, H1, M2 and M1. (Default = {})".format(discard_SRLs))
parser.pixels_in_x(pixels_in_x)
parser.pixels_in_y(pixels_in_y)
parser.FPS(FPS)
parser.block_size(block_size)
parser.search_range(search_range)
parser.nLayers(nLayers)
parser.add_argument("--new_slope", help="new slope. (Default = {})".format(new_slope))
parser.update_factor(update_factor)


args = parser.parse_known_args()[0]
if args.GOPs:
    GOPs = int(args.GOPs)
if args.TRLs:
    TRLs = int(args.TRLs)
if args.SRLs:
    SRLs = int(args.SRLs)
if args.BRC:
    BRC = int(args.BRC)
if args.discard_TRLs:
    discard_TRLs = int(args.discard_TRLs)
if args.discard_SRLs:
    discard_SRLs = str(args.discard_SRLs)
if args.pixels_in_x:
    pixels_in_x = int(args.pixels_in_x)
if args.pixels_in_y:
    pixels_in_y = int(args.pixels_in_y)
if args.FPS:
    FPS = int(args.FPS)
if args.block_size:
    block_size = int(args.block_size)
if args.search_range:
    search_range = int(args.search_range)
if args.nLayers:
    Ncapas_T = int(args.nLayers)
if args.new_slope:
    new_slope = int(args.new_slope)
if args.update_factor:
    update_factor = float(args.update_factor)


if BRC > MAX_VALUE :
    BRC = MAX_VALUE - 1

#check_call("echo List_Clayers: " + str(List_Clayers) + " " +  str(TRLs), shell=True) #  + " >> output" !!!
#raw_input("Press ENTER to continue ...") # !






################################################################
#                         FUNCTIONS                            #
################################################################

################################
#          kakadu              #
################################

def kdu_transcode (in_filename, out_filename, cLayers, reduces, rate): # kdu_transcode -usage | less
    try:
        if rate <= 0.0 :

            p = sub.Popen("trace kdu_transcode"
                          + " -i "      + in_filename
                          + " -o "      + "extract/" + out_filename
                          + " Clayers=" + str(cLayers)
                          + " -reduce " + str(reduces)
                          , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
            out, err = p.communicate()

        else :

            p = sub.Popen("trace kdu_transcode"
                          + " -i "      + in_filename
                          + " -o "      + "extract/" + out_filename
                          + " Clayers=" + str(cLayers)
                          + " -reduce " + str(reduces)
                          + " -rate "   + str(rate)
                          , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
            out, err = p.communicate()


        #check_call("echo \"OUT: " + str(out) + "\"", shell=True)
        #check_call("echo \"ERR: " + str(err) + "\"", shell=True)

        if err != "" : #if err in locals() :
            check_call("rm extract/" + out_filename, shell=True)
            size = 0
        else :
            size = os.path.getsize("extract/" + out_filename)

        return size

    except CalledProcessError:
        sys.exit(-1)


################################
#         transcode            #
################################

def transcode (N_subbands, FIRST_picture_ofGOP, pictures, _COMBINATION, _COMBINATION_REDUCES_normalized) :

    #check_call("echo _COMBINATION en el transcode: " + str(_COMBINATION), shell=True) # !
    #check_call("echo N_subbands: " + str(N_subbands), shell=True)
    #raw_input("")


    check_call("  rm -rf " + str(path_extract) + "; "
               + "mkdir "  + str(path_extract)
               , shell=True)


    ###############################
    # TRANSCODE DE 1 GOP Ó VARIOS #
    ###############################
    if FIRST_picture_ofGOP == 0 :
        transcode_unitario = False
    else :
        transcode_unitario = True


    ###########
    # MOTIONS #
    ###########
    if TRLs > 1 : # if discard_SRLs_Mot != 0 :

        fields = pictures / 2
        FIRST_fields = FIRST_picture_ofGOP / 2
        subband = 1

        while subband < TRLs :

            if _COMBINATION[N_subbands-subband] != 0 : # Subbanda con alguna/s capa.

                # Files sizes. With the size of each color image.
                file_sizes = open (str(path_extract) + "/motion_residue_" + str(subband) + ".mjc", 'w')
                total = 0

                for campoMov_number in range (FIRST_fields, fields) : # Decode components
                    for comp_number in range (0, MOTION_COMPONENTS) :

                        #check_call("echo MOTION: comp" + str(comp_number) + " " + str('%04d' % campoMov_number) + " " + str('%04d' % (campoMov_number - FIRST_fields)) , shell=True) # !
                        out_filename = in_filename = "motion_residue_" + str(subband) + "_comp" + str(comp_number) + "_" + str('%04d' % campoMov_number) + ".j2c"
                        if transcode_unitario == True :
                            out_filename           = "motion_residue_" + str(subband) + "_comp" + str(comp_number) + "_" + str('%04d' % (campoMov_number - FIRST_fields)) + ".j2c"

                        size = kdu_transcode (in_filename, out_filename, _COMBINATION[N_subbands-subband], _COMBINATION_REDUCES_normalized[N_subbands-subband], 0) #p = sub.Popen("cp " + in_filename + " extract/" + out_filename, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
                        total += size

                    file_sizes.write(str(total) + "\n")
                file_sizes.close()

            subband += 1
            fields /= 2
            FIRST_fields /= 2


    ############
    # TEXTURES #
    ############

    ##################
    # HIGH frecuency #
    ##################
    subband = 1
    while subband < TRLs :

        pictures = (pictures + 1) / 2
        FIRST_picture_ofGOP = FIRST_picture_ofGOP / 2
        #check_call("echo HIGH: sub " + str(subband) + ". De " + str(FIRST_picture_ofGOP) + " a " + str(pictures-2), shell=True) # !


        if _COMBINATION[TRLs-subband] != 0 : # Subbanda con alguna/s capa.

            # Files sizes. With the size of each color image.
            file_sizes = open (str(path_extract) + "/" + HIGH + str(subband) + ".j2c", 'w')
            total = 0

            image_number = FIRST_picture_ofGOP
            while image_number < (pictures - 1) :
                #check_call("echo HIGH: " + str('%04d' % image_number) + " " + str('%04d' % (image_number - FIRST_picture_ofGOP)) , shell=True) # !

                # Y
                out_filename = in_filename = HIGH + str(subband) + "_Y_" + str('%04d' % image_number) + ".j2c"
                if transcode_unitario == True :
                    out_filename           = HIGH + str(subband) + "_Y_" + str('%04d' % (image_number - FIRST_picture_ofGOP)) + ".j2c"
                Ysize = kdu_transcode (in_filename, out_filename, _COMBINATION[TRLs-subband], _COMBINATION_REDUCES_normalized[TRLs-subband], _RATES_Y[TRLs-subband][int(image_number)])

                # U
                out_filename = in_filename = HIGH + str(subband) + "_U_" + str('%04d' % image_number) + ".j2c"
                if transcode_unitario == True :
                    out_filename           = HIGH + str(subband) + "_U_" + str('%04d' % (image_number - FIRST_picture_ofGOP)) + ".j2c"
                Usize = kdu_transcode (in_filename, out_filename, _COMBINATION[TRLs-subband], _COMBINATION_REDUCES_normalized[TRLs-subband], _RATES_U[TRLs-subband][int(image_number)])

                # V
                out_filename = in_filename = HIGH + str(subband) + "_V_" + str('%04d' % image_number) + ".j2c"
                if transcode_unitario == True :
                    out_filename           = HIGH + str(subband) + "_V_" + str('%04d' % (image_number - FIRST_picture_ofGOP)) + ".j2c"
                Vsize = kdu_transcode (in_filename, out_filename, _COMBINATION[TRLs-subband], _COMBINATION_REDUCES_normalized[TRLs-subband], _RATES_V[TRLs-subband][int(image_number)])

                # Total file-sizes
                size = Ysize + Usize + Vsize
                total += size
                file_sizes.write(str(total) + "\n")

                image_number += 1

                #check_call("echo TRLs: " + str(TRLs) + " subband: " + str(subband) + " List_Clayers[TRLs-subband]: " + str(List_Clayers[TRLs-subband]), shell=True) #  + " >> output" !!!
                #raw_input("Press ENTER to continue ...") # !

            file_sizes.close()
        subband += 1
    subband -= 1


    #################
    # LOW frecuency #
    #################

    #check_call("echo LOW: sub " + str(subband) + ". De " + str(FIRST_picture_ofGOP) + " a " + str(pictures-1), shell=True) # !

    if _COMBINATION[0] != 0 : # Subbanda con alguna/s capa.

        # Files sizes. With the size of each color image.
        file_sizes = open (str(path_extract) + "/" + LOW + str(subband) + ".j2c", 'w')
        total = 0

        image_number = FIRST_picture_ofGOP
        while image_number < pictures:
            #check_call("echo LOW: " + str('%04d' % image_number) + " " + str('%04d' % (image_number - FIRST_picture_ofGOP)) , shell=True) # !

            # Y
            out_filename = in_filename = LOW + str(subband) + "_Y_" + str('%04d' % image_number) + ".j2c"
            if transcode_unitario == True :
                out_filename           = LOW + str(subband) + "_Y_" + str('%04d' % (image_number - FIRST_picture_ofGOP)) + ".j2c"
            Ysize = kdu_transcode (in_filename, out_filename, _COMBINATION[0], _COMBINATION_REDUCES_normalized[0], _RATES_Y[0][0])

            # U
            out_filename = in_filename = LOW + str(subband) + "_U_" + str('%04d' % image_number) + ".j2c"
            if transcode_unitario == True :
                out_filename           = LOW + str(subband) + "_U_" + str('%04d' % (image_number - FIRST_picture_ofGOP)) + ".j2c"
            Usize = kdu_transcode (in_filename, out_filename, _COMBINATION[0], _COMBINATION_REDUCES_normalized[0], _RATES_U[0][0])

            # V
            out_filename = in_filename = LOW + str(subband) + "_V_" + str('%04d' % image_number) + ".j2c"
            if transcode_unitario == True :
                out_filename           = LOW + str(subband) + "_V_" + str('%04d' % (image_number - FIRST_picture_ofGOP)) + ".j2c"
            Vsize = kdu_transcode (in_filename, out_filename, _COMBINATION[0], _COMBINATION_REDUCES_normalized[0], _RATES_V[0][0])

            # Total file-sizes
            size = Ysize + Usize + Vsize
            total += size
            file_sizes.write(str(total) + "\n")

            #check_call("echo TRLs: " + str(TRLs) + " subband: " + str(subband) + " List_Clayers[TRLs-subband]: " + str(List_Clayers[TRLs-subband]), shell=True) #  + " >> output" !!!
            #raw_input("Press ENTER to continue ...") # !

            image_number += 1

        file_sizes.close()



################################
#           SIZE               #
################################

def get_size (the_path, key) :

    path_size = 0
    for path, dirs, files in os.walk(the_path) :
        for fil in files:
            if re.search(key, fil) :
                #check_call("echo  ENTRA CON: " + str(fil), shell=True) # !
                path_size += os.path.getsize(the_path + "/" + fil)
        return path_size



################################
#            LBA               #
################################

def lba (FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file) : # looking the best angle

    #raw_input("_COMBINATION en lba: " + str(_COMBINATION)) # !
    #raw_input("_REDUCES en lba: " + str(_REDUCES)) # !
    #raw_input("ANTES TRANSCODE") # !
    #check_call("echo lba:" + str(FIRST_picture_ofGOP) + " " + str(pictures), shell=True) # !
    #raw_input("")

    #####################
    # NORMALIZA REDUCES #
    #####################
    _COMBINATION_REDUCES_normalized = _COMBINATION_REDUCES[:]
    for i in range (0, len(_COMBINATION_REDUCES)) :
        if _COMBINATION_REDUCES[i] > _REDUCES_normalizer[i] :
            _COMBINATION_REDUCES_normalized[i] = _REDUCES_normalizer[i]
    #check_call("echo DESPUES:" + str(_COMBINATION_REDUCES_normalized),shell=True) # !
    #raw_input("")


    #################################################################
    # NUEVOS VALORES (RESOLUCIÓN y TAMAÑO BLOQUE) PARA EL TRANSCODE #
    #################################################################
    _PIXELS_IN_X = []
    _PIXELS_IN_Y = []
    _BLOCK_SIZES = []

    # Escalado de la resolución (REDUCES) afecta a: PIXELS_IN_XY y BLOCK_SIZES
    for i in range (0, TRLs) : # T
        _PIXELS_IN_X.append(pixels_in_x/pow(2,_COMBINATION_REDUCES_normalized[i])) # RES_X_transcode=`echo "$RES_X/(2^$discard_SRLs_Tex)" | bc`
        _PIXELS_IN_Y.append(pixels_in_y/pow(2,_COMBINATION_REDUCES_normalized[i]))
        if i > 0 :
            _BLOCK_SIZES.append(block_size/pow(2,_COMBINATION_REDUCES_normalized[i]))
    for i in range (TRLs, N_subbands) : # M
        _BLOCK_SIZES[i-TRLs] = _BLOCK_SIZES[i-TRLs]*pow(2,_COMBINATION_REDUCES_normalized[i]) # block_size_transcode=`echo "$block_size/(2^$discard_SRLs_Tex)" | bc`


    #################
    # DIVISIBILIDAD #
    #################
    for i in range (1, TRLs) :
        if 0 != _PIXELS_IN_X[i] % _BLOCK_SIZES[i-1] or 0 != _PIXELS_IN_Y[i] % _BLOCK_SIZES[i-1] :
            check_call("echo La resolucion \(" + str(_PIXELS_IN_X[i]) + "x" + str(_PIXELS_IN_Y[i]) + "\) no es divisible entre el tamano de macrobloque \(" + str(_BLOCK_SIZES[i-1]) + "\)"
                       , shell=True)
            exit (0)

    # !
    #check_call("echo \"\n--block_size=" + ','.join(map(str, _BLOCK_SIZES))
    #           + "\n--pixels_in_x=" + ','.join(map(str, _PIXELS_IN_X))
    #           + "\n--pixels_in_y=" + ','.join(map(str, _PIXELS_IN_Y))
    #           + "\n--subpixel_accuracy=" + ','.join(map(str, _COMBINATION_REDUCES_normalized[:TRLs])) + "\""
    #           ,shell=True)
    #raw_input("")
    # !


    ###########
    # EXTRACT #
    ########### Extrae en la carpeta /extract
    transcode (N_subbands, FIRST_picture_ofGOP, pictures, _COMBINATION, _COMBINATION_REDUCES_normalized)

    #check_call("echo DESPUES DE EXTRACT",shell=True) # !
    #raw_input("")




    ######################################
    # COPIA FICHEROS AUXILIARES /EXTRACT #
    ###################################### frame_types_
    pictures = 1 * GOP_size + 1
    subband = 1
    while subband < TRLs :
        pictures = pictures / 2 # !
        p = sub.Popen("dd"
                      + " if="    + str(path_base)    + "/frame_types_" + str(subband)
                      + " of="    + str(path_extract) + "/frame_types_" + str(subband)
                      + " skip="  + str(iGOP-1)
                      + " bs="    + str(pictures)
                      + " count=" + str(GOPs_to_expand)
                      , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
        out, err = p.communicate()
        subband += 1


    #########
    # ENVIO #
    #########
    p = sub.Popen("rm -rf " + str(path_tmp) + "; mkdir " + str(path_tmp)
                  + "; echo \"ENVIO: \"; ls -l " + str(path_extract) # echo
                  + "; cp " + str(path_extract) + "/* " + str(path_tmp)
                  , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    out, err = p.communicate()
    #errcode = p.returncode

    #check_call("echo DESPUES DE ENVIO",shell=True) # !
    #raw_input("")


    ###############
    # INFO (KBPS) #
    ###############
    os.chdir(path_extract)

    instancia_info_j2k                              = info_j2k.info_j2k(GOPs_to_expand, TRLs, FPS)     # ! sólo para j2k
    kbps_M,         kbps_T,         kbps_TM         = instancia_info_j2k.kbps()                        # kbps_TM[0] = kbps del GOP0 (primera imagen L). kbps_TM[1] = kbps del GOP1.
   #kbps_M_average, kbps_T_average, kbps_TM_average = instancia_info_j2k.kbps_average()


    TO_KBPS  = 8.0 / duration / 1000
    kbps_ALL = get_size(path_extract, "") * TO_KBPS


    ##########
    # EXPAND #
    ##########
    #ANTES: check_call("DownConvertStatic $RES_X_transcode $RES_Y_transcode low_0 $RES_X $RES_Y low_0_UP", shell=True)
    #AHORA: en el expand. T: res y accuracy. M: block_size
    os.chdir(path_tmp)

    check_call("mcj2k expand"  # mcj2k expand --GOPs=1 --TRLs=5 --SRLs=5 --block_size=16,16,16,16 --search_range=4 --pixels_in_x=352,352,352,352,352 --pixels_in_y=288,288,288,288,288 --subpixel_accuracy=0,0,0,0,0
               + " --GOPs="              + str(GOPs_to_expand)
               + " --TRLs="              + str(TRLs)
               + " --SRLs="              + str(SRLs)
               + " --update_factor="     + str(update_factor)
               + " --block_size="        + ','.join(map(str, _BLOCK_SIZES))
               + " --block_size_min="    + str(block_size_min)
               + " --search_range="      + str(search_range)
    #          + " --rates="             + str(','.join(map(str, _RATES))) # FALTARÍA DEPURAR
               + " --pixels_in_x="       + ','.join(map(str, _PIXELS_IN_X))
               + " --pixels_in_y="       + ','.join(map(str, _PIXELS_IN_Y))
               + " --subpixel_accuracy=" + ','.join(map(str, _COMBINATION_REDUCES_normalized[:TRLs]))
               , shell=True)

    # redimensionar con downconvert (el de Vicente) en caso de reduce en las texturas !

    #check_call("echo DESPUES DE EXPAND",shell=True) # !
    #raw_input("")


    ###############
    # INFO (RMSE) #
    ###############
    if snr_file == "low_0" : # VIDEO COMPLETO
        p = sub.Popen("snr --file_A=low_0                 --file_B=../low_0" + str(iGOP) + " 2> /dev/null | grep RMSE | cut -f 3", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    else :                   # SUB_INDEPENDIENTES
        p = sub.Popen("snr --file_A=" + str(snr_file) + " --file_B=../" + str(snr_file)  + " 2> /dev/null | grep RMSE | cut -f 3", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
        #                  --file_A=high_4                --file_B=../high_4

    check_call("echo \"" + "snr_file: " + str(snr_file) + "  " + str(_COMBINATION) + "\" >> " + str(path_base) + "pruebasss", shell=True) # !

    out, err = p.communicate()
    #errcode = p.returncode
    if out == "" : #if err in locals() :
        check_call("echo SNR sin salida.", shell=True)
        exit (0)

    rmse1D = float(out)


    ########
    # KBPS #
    ########
    KBPS_DATA  = ""
    KBPS_DATA += "  M "          + str(kbps_M)
    KBPS_DATA += "\toutL "       + str(kbps_T[0])
    KBPS_DATA += "\tT "          + str(kbps_T[-1:])
    KBPS_DATA += "\tTM "         + str(kbps_TM) #KBPS_DATA += "\tTM_average " + str(kbps_TM_average)
    KBPS_DATA += "\tRMSE "       + str(rmse1D) + "\t:: "
    KBPS_DATA  = KBPS_DATA.replace("[", "")
    KBPS_DATA  = KBPS_DATA.replace("]", "")
    KBPS_DATA  = KBPS_DATA.replace(",", " ")


    ###########
    # ÁNGULOS #
    ###########
    os.chdir(path_base)

    # RADIAN
    radian = 0 # fuzzy Python

    # CRIBA
    if _COMBINATION == _CEROS :
        rmse1D_antes = rmse1D
        kbps_antes   = kbps_TM[1]                                                          # kbps @@@
        _CANDIDATO_REDUCES_normalized = _COMBINATION_REDUCES_normalized[:]

    else :
        if rmse1D_antes > rmse1D :    # >
            emptyLayer = 0
            radian     = math.atan ( (rmse1D_antes - rmse1D) / (kbps_TM[1] - kbps_antes) ) # kbps @@@

            if radian > radian_candidato :
                kbps_candidato                = kbps_TM[:]                                 # kbps @@@
                rmse1D_candidato              = rmse1D
                radian_candidato              = radian
                _CANDIDATO                    = _COMBINATION[:]
                _CANDIDATO_REDUCES            = _COMBINATION_REDUCES[:]
                _CANDIDATO_REDUCES_normalized = _COMBINATION_REDUCES_normalized[:]
                CANDIDATO_KBPS                = KBPS_DATA

        else :                        # <=
            emptyLayer += 1
            check_call("echo \"" + str(_COMBINATION) + " * " + str(_COMBINATION_REDUCES_normalized) + KBPS_DATA + "No rectangulo \" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle", shell=True)
            return kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS

    check_call("echo \"" + str(_COMBINATION) + " * " + str(_COMBINATION_REDUCES_normalized) + KBPS_DATA + str("%.9f" % radian) + "\" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle", shell=True)
    check_call("echo \"Y :: " + str(_RATES_Y)  + "\" >> " + str(INFO) + "_rates", shell=True)
    check_call("echo \"U :: " + str(_RATES_U)  + "\" >> " + str(INFO) + "_rates", shell=True)
    check_call("echo \"V :: " + str(_RATES_V)  + "\" >> " + str(INFO) + "_rates ; echo >> " + str(INFO) + "_rates", shell=True)
    return kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS



###################
# Recoge AVERAGES #
###################
def save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D) :

    if iGOP == 1 :
        AVERAGES[0].append(kbps_TM[0]) # El GOP0
        RMSEs   [0].append(0)
    AVERAGES[iGOP].append(kbps_TM[1])  # El GOPn
    RMSEs   [iGOP].append(rmse1D)

    return AVERAGES, RMSEs



#######################
# 6. BRC Fuerza Bruta #
#######################
def BRC_BruteForce (_CAPAS_COMPLETAS, AVERAGES, RMSEs) :

    # Variables de lba (python pide declararlas)
    snr_file         = "low_0"   ######################################################### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    KBPS_DATA        = ""
    CANDIDATO_KBPS   = ""

    kbps_antes       = 0
    kbps_candidato   = [0, 0]
    kbps_TM          = [0, 0]
    kbps_ALL         = 0

    rmse1D           = 0
    rmse1D_antes     = MAX_VALUE
    rmse1D_candidato = 0

    radian_candidato = -MAX_VALUE
    radian           = 0

    emptyLayer       = 0

    _CEROS           = [0] * N_subbands
    _CAPAS           = [0] * N_subbands
    _COMBINATION     = [0] * N_subbands
    _CANDIDATO       = [0] * N_subbands
    #_CAPAS_VACIAS = # para la optimización

    # Esta forma de inicializar un list funciona para un list pero no para un list de lists
    _COMBINATION_REDUCES            = ([Nclevels_T+1] * TRLs) + ([Nclevels_M+1] * (TRLs-1)) # +1 pq el BRC primero modifica y despues evalua
    _CANDIDATO_REDUCES              = _COMBINATION_REDUCES[:]
    _REDUCES_normalizer             = ([Nclevels_T] * TRLs) + ([Nclevels_M] * (TRLs-1))
    _CANDIDATO_REDUCES_normalized   = []
    _COMBINATION_REDUCES_normalized = []

    # Inicializa _REDUCES
    _REDUCES = map(int, discard_SRLs.split(','))

    error = False
    if len(_REDUCES) != N_subbands :
        check_call("echo discard_SRLs: its length must be " + str(N_subbands) + " with TRL=" + str(TRLs) + ".", shell=True) # Types
        error = True
    #if que no supere Nclevels_M ni Nclevels_T

    if error == True :
        _REDUCES = [0] * N_subbands #_REDUCES = ([Nclevels_T] * TRLs) + ([Nclevels_M] * (TRLs-1))
        check_call("echo discard_SRLs default = " + str(_REDUCES) + "   Press ENTER to continue...", shell=True) # Types

    if BRC == MAX_VALUE :
        INFO = str(path_base) + "/info_" + str(TRLs) + "_" + ','.join(map(str, _CAPAS_COMPLETAS)) + "." + ''.join(map(str, _REDUCES))
    else :
        INFO = str(path_base) + "/info_" + str(TRLs) + "_" + str(BRC) + "_" + ','.join(map(str, _CAPAS_COMPLETAS)) + "." + ''.join(map(str, _REDUCES))

    _COMBINATION_REDUCES = _REDUCES[:]
    _REDUCES_normalizer  = _REDUCES[:]
    _CANDIDATO_REDUCES   = _REDUCES[:]

    # Desnormaliza _CANDIDATO_REDUCES
    for i in range (0, len(_REDUCES)) :
        if _REDUCES[i] > 0 :
            _CANDIDATO_REDUCES[i] += 1

    #######
    # BRC #
    #######

    # Inicializa infos
    check_call("rm -f " + str(INFO) + " " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle", shell=True)

    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)
    rmse1D_first = rmse1D_antes

    while _CANDIDATO != _CAPAS_COMPLETAS and kbps_candidato[1] < BRC : # H_min < Ncapas_T
        # max_iteraciones -= 1
        # if max_iteraciones < 0 :
        #    check_call("echo \"" + "\nEvaluaciones completadas. Existen capas que no se han llegado a usar, porque no es provechoso hacerlo.\" >> " + str(INFO) + "_detalle", shell=True)
        #    exit (0)

        radian_candidato = -MAX_VALUE

        _CAPAS = _CANDIDATO[:] # actualiza _CAPAS
        _REDUCES = _CANDIDATO_REDUCES[:]
        # raw_input("actualiza _CAPAS: " + str(_CAPAS)) # !
        check_call("echo \"-> " + str(_CANDIDATO) + " * " + str(_CANDIDATO_REDUCES_normalized) + "\" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle ; echo >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle", shell=True)

        emptyLayer = 0
        z = 0
        while z < len(_CAPAS) : # recorre cada subbanda # For no deja modificar Z para las emptyLayer
            _COMBINATION = _CAPAS[:] # inicializa _COMBINATION
            _COMBINATION_REDUCES = _REDUCES[:]
            # raw_input("inicializa _COMBINATION: " + str(_COMBINATION) + "con REDUCES: " + str(_REDUCES)) # !
            # check_call("echo " + str(_COMBINATION_REDUCES),shell=True) # !
            # raw_input("") # !

            if z < TRLs : # TEXTURES

                if _REDUCES[z] > 0 : # reduces available
                    _COMBINATION_REDUCES[:TRLs] = [_REDUCES[z] - 1] * TRLs # Todas las subbandas por igual (fregao importante)
                    if _COMBINATION[z] == 0 :
                        _COMBINATION[z] = 1 # Al menos una capa # TAMBIÉN EMPTYLAYER ?
                    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

                elif (_CAPAS[z] + emptyLayer) < Ncapas_T : # T capas available
                    _COMBINATION[z] = _CAPAS[z] + 1 + emptyLayer
                    if _COMBINATION[z] < Ncapas_T :
                        _COMBINATION_REDUCES[:TRLs] = [Nclevels_T] * TRLs # Todas las subbandas por igual
                    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

                if _COMBINATION[z] == Ncapas_T :
                    emptyLayer = 0

            else : # MOTION

                if _REDUCES[z] > 0 : # reduces available
                    _COMBINATION_REDUCES[z] = _REDUCES[z] - 1 # Cada campo mov independientemente
                    if _COMBINATION[z] == 0 :
                        _COMBINATION[z] = 1 # Al menos una capa
                    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

                elif (_CAPAS[z] + emptyLayer) < Ncapas_M : # M capas available
                    _COMBINATION[z] = _CAPAS[z] + 1 + emptyLayer
                    if _COMBINATION[z] < Ncapas_M :
                        _COMBINATION_REDUCES[z] = Nclevels_M # Cada campo mov independientemente
                    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

                if _COMBINATION[z] == Ncapas_M :
                    emptyLayer = 0


            if emptyLayer > 0 : # Repite la evaluación de una subbanda hasta que encuentra una capa que mejore el RMSE (!= capa vacía)
                z -= 1
            z += 1

        # Se ajustan los parámetros de la nueva búsqueda, para la situación actual.
        kbps_antes   = kbps_candidato[1]
        rmse1D_antes = rmse1D_candidato

        check_call("echo \"" + str(_CANDIDATO)+ " * " + str(_CANDIDATO_REDUCES_normalized) + CANDIDATO_KBPS + str(radian_candidato) + "\" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_optimizado_BRCbruto", shell=True)

        if _CAPAS == _CANDIDATO and _REDUCES == _CANDIDATO_REDUCES : # No se ha encontrado un candidato mejor al vector base propuesto (_COMBINATION)
            rmse1D_antes = rmse1D_first
            check_call("echo \"" + "\nLa distorsion ha aumentado.\" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle", shell=True)
        else : # Recoge AVERAGES
            AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_candidato, rmse1D_candidato)


    return AVERAGES, RMSEs

####################################
# 7. Control BR -rate a componente #
####################################

def OneRate_ForComponent (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS) :

    Npuntos_T = (Ncapas_T + 1) * 1 # Nº de puntos que se quieren sacar en la gráfica # = 50; Así saldrán muchos puntos             !
    TO_BPPS_Y = 8.0 / (pixels_in_x * pixels_in_y)
    TO_BPPS_UV = 8.0 / ((pixels_in_x/2) * (pixels_in_y/2))

    # LOW
    L_bpps_Y_subband = get_size(path_base, LOW + str(TRLs-1) + "_Y_0001.j2c") * TO_BPPS_Y
    L_bpps_U_subband = get_size(path_base, LOW + str(TRLs-1) + "_U_0001.j2c") * TO_BPPS_UV
    L_bpps_V_subband = get_size(path_base, LOW + str(TRLs-1) + "_V_0001.j2c") * TO_BPPS_UV
    #L_bpps_YUV_subband = L_bpps_Y_subband + L_bpps_U_subband + L_bpps_V_subband

    for Ncapa in range (1, Ncapas_T + 1) :
        pics = pictures # pictures se usa en subfuncion
        _RATES_Y = [[0] for x in xrange(TRLs)]
        _RATES_U = [[0] for x in xrange(TRLs)]
        _RATES_V = [[0] for x in xrange(TRLs)]

        # HIGH
        for z in range (1, TRLs) :

            pics = (pics + 1) / 2
            for image_number in range (0, pics-1) :
                str_image_number = '%04d' % image_number

                # por componente
                H_bpps_Y = get_size(path_base, HIGH + str(z) + "_Y_" + str_image_number + "\.j2c") * TO_BPPS_Y
                H_bpps_U = get_size(path_base, HIGH + str(z) + "_U_" + str_image_number + "\.j2c") * TO_BPPS_UV
                H_bpps_V = get_size(path_base, HIGH + str(z) + "_V_" + str_image_number + "\.j2c") * TO_BPPS_UV

                _RATES_Y[TRLs-z].append( H_bpps_Y / pow(math.sqrt(2), TRLs-z) )
                _RATES_U[TRLs-z].append( H_bpps_U / pow(math.sqrt(2), TRLs-z) )
                _RATES_V[TRLs-z].append( H_bpps_V / pow(math.sqrt(2), TRLs-z) )


        check_call("echo Y :: " + str(_RATES_Y), shell=True) # !!!
        check_call("echo U :: " + str(_RATES_U), shell=True)
        check_call("echo V :: " + str(_RATES_V), shell=True)
        #raw_input("")

    #_RATES_Y=[[2.044192],[2.2845934207],[1.350734,0.369476],[0.8642414643,0.8195452447,0.2022219328,0.2527772392],[0.50266325,0.50234775,0.49285825,0.09911625,0.102904,0.10045775,0.10029975,0.11410975]]
    #_RATES_U=[[2.210543],[0.6573328278],[1.37792,0.4221905],[0.8566527943,0.1963069846,0.1967535225,0.247643644],[0.4941405,0.48305325,0.48064625,0.099195,0.10314075,0.10590275,0.10590275,0.108507]]
    #_RATES_V=[[2.271149],[0.7823259721],[0.335543,0.4313445],[0.8197683369,0.2103688636,0.2332469499,0.2551209447],[0.4857165,0.49522575,0.1032985,0.09635425,0.09958975,0.10179925,0.1098485,0.11087425]]

    ###############################

    # for Ncapa in range (1, Ncapas_T + 1) :

    ###############################

    _COMBINATION = _CAPAS_COMPLETAS[:]
    #_COMBINATION = ([8] * TRLs) + ([Ncapas_M] * (TRLs-1))
    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

    '''
    la verde !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    _COMBINATION = _CAPAS_COMPLETAS[:]

    #_COMBINATION = [1, 1, 1, 0, 0, 1, 1, 1, 1] # !
    #kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer)

    # LOW
    L_bpps_Y_total = get_size(path_base, LOW + str(TRLs-1) + "_Y_0001.j2c") * 8.0 / (pixels_in_x * pixels_in_y)
    L_bpps_U_total = get_size(path_base, LOW + str(TRLs-1) + "_U_0001.j2c") * 8.0 / ((pixels_in_x/2) * (pixels_in_y/2))
    L_bpps_V_total = get_size(path_base, LOW + str(TRLs-1) + "_V_0001.j2c") * 8.0 / ((pixels_in_x/2) * (pixels_in_y/2))

    for n in range (1, Npuntos_T+1) :
         _RATES_Y = [ L_bpps_Y_total / Npuntos_T * n ]
         _RATES_U = [ L_bpps_U_total / Npuntos_T * n ]
         _RATES_V = [ L_bpps_V_total / Npuntos_T * n ]

         # HIGH
         for z in range (1, TRLs) :
             H_bpps_Y = get_size(path_base, HIGH + str(TRLs - z) + "_Y_[0-9][0-9][0-9][0-9]\.j2c") * 8.0 / (pixels_in_x * pixels_in_y)
             H_bpps_U = get_size(path_base, HIGH + str(TRLs - z) + "_U_[0-9][0-9][0-9][0-9]\.j2c") * 8.0 / ((pixels_in_x/2) * (pixels_in_y/2))
             H_bpps_V = get_size(path_base, HIGH + str(TRLs - z) + "_V_[0-9][0-9][0-9][0-9]\.j2c") * 8.0 / ((pixels_in_x/2) * (pixels_in_y/2))

             check_call("echo H_bpps_Y: " + str(H_bpps_Y), shell=True) # !
             exit (0)

             _RATES_Y.append( _RATES_Y[0] / (H_bpps_Y * math.sqrt(2) * z / _RATES_Y[0]) )
             _RATES_U.append( _RATES_U[0] / (H_bpps_U * math.sqrt(2) * z / _RATES_U[0]) )
             _RATES_V.append( _RATES_V[0] / (H_bpps_V * math.sqrt(2) * z / _RATES_V[0]) )


         check_call("echo Y :: " + str(_RATES_Y), shell=True) # !!!
         check_call("echo U :: " + str(_RATES_U), shell=True)
         check_call("echo V :: " + str(_RATES_V), shell=True)
         #raw_input("")


         _COMBINATION = _CAPAS_COMPLETAS[:] # _COMBINATION = [16, 16, 1]
         kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba (pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION)


    #SUB_raiz2_COMP_pond !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Npuntos_T = (Ncapas_T + 1) * 1 # Nº de puntos que se quieren sacar en la gráfica # = 50; Así saldrán muchos puntos             !
    TO_BPPS_Y = 8.0 / (pixels_in_x * pixels_in_y)
    TO_BPPS_UV = 8.0 / ((pixels_in_x/2) * (pixels_in_y/2))

    # LOW
    L_bpps_Y_subband = get_size(path_base, LOW + str(TRLs-1) + "_Y_0001.j2c") * TO_BPPS_Y
    L_bpps_U_subband = get_size(path_base, LOW + str(TRLs-1) + "_U_0001.j2c") * TO_BPPS_UV
    L_bpps_V_subband = get_size(path_base, LOW + str(TRLs-1) + "_V_0001.j2c") * TO_BPPS_UV
    #L_bpps_YUV_subband = L_bpps_Y_subband + L_bpps_U_subband + L_bpps_V_subband

    for n in range (1, Npuntos_T) :
        pics = pictures # pictures se usa en subfuncion
        _RATES_Y = [ [ L_bpps_Y_subband / Ncapas_T * n ] ] + [[] for x in xrange(TRLs-1)]
        _RATES_U = [ [ L_bpps_U_subband / Ncapas_T * n ] ] + [[] for x in xrange(TRLs-1)]
        _RATES_V = [ [ L_bpps_V_subband / Ncapas_T * n ] ] + [[] for x in xrange(TRLs-1)]

        # HIGH
        for z in range (1, TRLs) :
            pics = (pics + 1) / 2

            # por subbanda
            H_bpps_Y_subband = get_size(path_base, HIGH + str(z) + "_Y_[0-9][0-9][0-9][0-9]\.j2c") * TO_BPPS_Y
            H_bpps_U_subband = get_size(path_base, HIGH + str(z) + "_U_[0-9][0-9][0-9][0-9]\.j2c") * TO_BPPS_UV
            H_bpps_V_subband = get_size(path_base, HIGH + str(z) + "_V_[0-9][0-9][0-9][0-9]\.j2c") * TO_BPPS_UV

            H_bpps_Y_subband_pond = _RATES_Y[0][0] / pow(math.sqrt(2), TRLs-z)# * H_bpps_Y_subband / _RATES_Y[0][0]
            H_bpps_U_subband_pond = _RATES_U[0][0] / pow(math.sqrt(2), TRLs-z)# * H_bpps_U_subband / _RATES_U[0][0]
            H_bpps_V_subband_pond = _RATES_V[0][0] / pow(math.sqrt(2), TRLs-z)# * H_bpps_V_subband / _RATES_V[0][0]

            for image_number in range (0, pics-1) :
                str_image_number = '%04d' % image_number

                # por componente
                H_bpps_Y = get_size(path_base, HIGH + str(z) + "_Y_" + str_image_number + "\.j2c") * TO_BPPS_Y
                H_bpps_U = get_size(path_base, HIGH + str(z) + "_U_" + str_image_number + "\.j2c") * TO_BPPS_UV
                H_bpps_V = get_size(path_base, HIGH + str(z) + "_V_" + str_image_number + "\.j2c") * TO_BPPS_UV


                _RATES_Y[TRLs-z].append( H_bpps_Y_subband_pond * H_bpps_Y / H_bpps_Y_subband )
                _RATES_U[TRLs-z].append( H_bpps_U_subband_pond * H_bpps_U / H_bpps_U_subband )
                _RATES_V[TRLs-z].append( H_bpps_V_subband_pond * H_bpps_V / H_bpps_V_subband )


        check_call("echo Y :: " + str(_RATES_Y), shell=True) # !!!
        check_call("echo U :: " + str(_RATES_U), shell=True)
        check_call("echo V :: " + str(_RATES_V), shell=True)
        #raw_input("")


        _COMBINATION = _CAPAS_COMPLETAS[:] # _COMBINATION = [16, 16, 1]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba (pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION)
        '''



############################################
# Un slope X por cada punto de la curva RD #
############################################

def OneSlope_ForPoint (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _CAPAS_COMPLETAS) :
    _COMBINATION = _CAPAS_COMPLETAS[:]
    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)
    check_call("cat " + str(INFO) + "_detalle >> ../1slopeXpto", shell=True)
    exit (0)




################################
# 10. Subbandas Independientes #
################################

def Sub_Independents (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _CAPAS_COMPLETAS) :

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    snr_file      = None
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []
    _SUB_EVALUADA = []


    # 0. DEFINE QUE SUBBANDA SE ESTA EVALUANDO. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    for uu in range (0, (len(_CAPAS_COMPLETAS)/2)+1) : # para las texturas, los vectores no se evaluan
        _ENVIOS.append(_ENVIO_VACIO[:]) # Se añade para reiniciar las pendientes (se podria hacer de otra forma) !!!
        _ENVIOS.append(_ENVIO_VACIO[:])
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])                                # _SUB_EVALUADA
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])
        for u in range (0, _CAPAS_COMPLETAS[uu]) :
            _ENVIOS[len(_ENVIOS)-1][uu] += 1                                 # actualiza el ultimo elemento
            _SUB_EVALUADA[len(_SUB_EVALUADA)-1][uu] = 1                      # _SUB_EVALUADA
            if u < _CAPAS_COMPLETAS[uu]-1 :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])                   # Duplica ultimo elemento
                _SUB_EVALUADA.append(_SUB_EVALUADA[len(_SUB_EVALUADA)-1][:]) # _SUB_EVALUADA


    # 2. TESTEA LAS EVALUACIONES (extraccion + reconstruccion) resultando las pendientes (radian)
    # NOTA: mini optimizacion del codigo:
    # Se usan en las evaluaciones el vector vacio para que se inicialice la variable "radian = 0" en la funcion "lba".
    # Para evitar la reconstrucción de la nada, se podria inicializar la variable externamente a la funcion,
    # mientras se va llamando reiteradamente, cuando se cambia de subbanda.
    for u in range (0, len(_ENVIOS)) :

        # ACTUALIZA la comparacion del SNR cada vez que se cambie de subbanda en el lba (entre _ENVIO_VACIO)!!
        _subband_for_send = [[i for i, x in enumerate(_ENVIOS[u]) if x != e] for e in [0]]
        if _subband_for_send != [[]] :
            snr_file = "high_" + str(TRLs-_subband_for_send[0][0])
            if _subband_for_send == [[0]] :
                snr_file = "low_" + str(TRLs-1)
        else :
            snr_file = "low_0"


        # EVALUA
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # RESPECTO DEL PUNTO ANTERIOR, y no respecto del punto inicial. NO ES CODIGO DEL BRC (que se actualiza solo con los candidatos), esto es para las sub_independientes y UnaParaTodas_PtAnterior
        rmse1D_antes = rmse1D
        kbps_antes   = kbps_TM[1] # kbps @@@

        # Pondera las inclinaciones por las ganancias en caso de no haber usado ganancias para los slopes.
        #GAINS  = [1.0877939347, 2.1250255455, 3.8884779989, 5.8022196044]
        #radian = radian * GAINS[]

        # Recoge los resultados de las evaluaciones: el envio con su radian
        _EVALUACIONES.append([_ENVIOS[u][:], _SUB_EVALUADA[u][:], radian])


    # 4. ORDENA LOS TEST SEGUN SU PENDIENTE (radian)
    _EVALUACIONES.sort(key=lambda x:x[2], reverse=True) # Posicion por la que se ordena
    # PRINT (depuracion)
    check_call("mv " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    check_call("echo \"" + "\n# LAS EVALUACIONES TESTEADAS ANTES, AHORA ORDENADAS SEGUN PENDIENTE=RADIAN\n" + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    for u in range (0, len(_EVALUACIONES)) :
        check_call("echo \"" + str(_EVALUACIONES[u])  + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)


    # Elimina los puntos destinados únicamente al cálculo de ángulos y los puntos que resultan en angulo=0.
    u = 0
    longitud = len(_EVALUACIONES)
    while u < longitud : # No se puede usar un for, porque se esta cambiando la longitud del vector recorrido.
        if 0 == _EVALUACIONES[u][2] :
            _EVALUACIONES.pop(u)
            longitud -= 1
        else :
            u += 1


    # 4.5 GENERA VM
    _ENVIOS       = []
    _SUB_EVALUADA = []
    for u in range (TRLs, len(_CAPAS_COMPLETAS)) :   # Para los vectores
        _ENVIOS.append(_ENVIO_VACIO[:])              # _ENVIO
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])        # _SUB_EVALUADA
        _ENVIOS[len(_ENVIOS)-1][u] = 1               # Actualiza el ultimo elemento
        _SUB_EVALUADA[len(_SUB_EVALUADA)-1][u] = 1   # _SUB_EVALUADA
    # Introduce VM en _EVALUACIONES
    for u in range (0, len(_ENVIOS)) :
        _EVALUACIONES.insert(u+1, [_ENVIOS[u][:], _SUB_EVALUADA[u][:], "radian_no_calculado"])

    #print '\n'.join(map(str, _ENVIOS))
    #print '\n'.join(map(str, _SUB_EVALUADA))
    #print '\n'.join(map(str, _EVALUACIONES))


    # 5. TRADUCE A NOTACION DE ENVIO. Obviando capas vacias.
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]
    for u in range (0, len(_EVALUACIONES)) :
        if _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] < _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] :
            _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # Duplica ultimo elemento
            _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] = _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] # Añade capa al envio


    # PRINT (depuración)
    for u in range (0, len(_ENVIOS)) :
        check_call("echo \"" + str(_ENVIOS[u])  + "\" >> "
                   + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_optimizado"
                   , shell=True)

    #check_call("echo \"" + "_EVALUACIONES: " + str(_EVALUACIONES)  + "\"", shell=True)
    #exit (0)

    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)

    return AVERAGES, RMSEs




#########################################
# 12. Una subbanda para todas PtInicial #
#########################################

def OneSub_ForAll_PtInicial (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _CAPAS_COMPLETAS) :

    # Variables
    _EVALUACIONES = []

    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]
    for uu in range (0, len(_CAPAS_COMPLETAS)) :
        _ENVIOS.append(_CAPAS_COMPLETAS[:])
        for u in range (0, _CAPAS_COMPLETAS[uu]) :
            _ENVIOS[len(_ENVIOS)-1][uu] -= 1 # actualiza el ultimo elemento
            if u < _CAPAS_COMPLETAS[uu]-1 :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # duplica ultimo elemento


    # 2. TESTEA LAS EVALUACIONES (extraccion + reconstruccion) resultando las pendientes (radian)
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)
        # Recoge los resultados de las evaluaciones: el envio con su radian
        _EVALUACIONES.append([_COMBINATION[:], kbps, rmse1D, radian])

    '''
    # 3. OBVIA LAS CAPAS VACIAS (o casi vacias en este codigo)
    _EVALUACIONES.sort(key=lambda x:x[2]) # ordena por rmse1D

    auxRMSE = -1
    uu = 0
    longitud = len(_EVALUACIONES)
    while uu < longitud-1 : # recorre la lista identificando los rmse1D duplicados
        if auxRMSE == _EVALUACIONES[uu][2] :
            print("borra ", _EVALUACIONES[uu])
            _EVALUACIONES.pop(uu) # y los elimina
            longitud = len(_EVALUACIONES)
        else :
            auxRMSE = _EVALUACIONES[uu][2]
            print("nuevo auxRMSE ", auxRMSE)
            uu += 1
    '''

    # 4. ORDENA LOS TEST SEGUN SU PENDIENTE
    _EVALUACIONES.sort(key=lambda x:x[3]) # Posicion por la que se ordena
    # PRINT (depuracion)
    check_call("mv " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle " + str(INFO) + "_evaluaciones", shell=True)
    check_call("echo \"" + "\n# LAS EVALUACIONES TESTEADAS ANTES, AHORA ORDENADAS SEGUN PENDIENTE=RADIAN\n" + "\" >> " + str(INFO) + "_evaluaciones", shell=True)
    for u in range (0, len(_EVALUACIONES)) :
        check_call("echo \"" + str(_EVALUACIONES[u])  + "\" >> " + str(INFO) + "_evaluaciones", shell=True)
    _EVALUACIONES.pop(0) # Elimina la evaluacion del [0, ..., 0]. No es necesaria ya.



    # 5. TRADUCE A NOTACION DE ENVIO
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]
    # Capa que se debe añadir
    for u in range (0, len(_EVALUACIONES)) : # Capa que se debe añadir en Subbandas de TEXTURAS
        _subband_for_send = [[i for i, x in enumerate(_EVALUACIONES[u][0][:TRLs]) if x != e] for e in [_CAPAS_COMPLETAS[0]]]
        if _subband_for_send == [[]] : # Capa que se debe añadir en Subbandas de VECTORES
            _subband_for_send = [[i for i, x in enumerate(_EVALUACIONES[u][0][TRLs:]) if x != e] for e in [_CAPAS_COMPLETAS[TRLs]]]
            if _subband_for_send != [[]] : _subband_for_send[0][0] += TRLs # +TRLs -> los campos de movimiento estan en la segunda parte del vector
        # Añade a _ENVIOS el nuevo envio optimo
        if _subband_for_send != [[]] :
            _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # duplica ultimo elemento
            _ENVIOS[len(_ENVIOS)-1][_subband_for_send[0][0]] += 1 # actualiza el ultimo elemento
            _subband_for_send = [[]] # Limpia variable. No deberia ser necesario..
    # PRINT (depuracion)
    for u in range (0, len(_ENVIOS)) :
        check_call("echo \"" + str(_ENVIOS[u])  + "\" >> " + str(INFO) + "_optimizado", shell=True)


    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)





##########################################
# 13. Una subbanda para todas PtAnterior #
##########################################

def OneSub_ForAll_PtAnterior (_CAPAS_COMPLETAS, AVERAGES, RMSEs) : # Evaluaciones -> Optimizado -> Detalle

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []
    _SUB_EVALUADA = []


    # 0. DEFINE QUE SUBBANDA SE ESTA EVALUANDO. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    for uu in range (0, len(_CAPAS_COMPLETAS)) :
        _ENVIOS.append(_ENVIO_VACIO[:])                                      # _ENVIOS
        _ENVIOS.append(_CAPAS_COMPLETAS[:])
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])                                # _SUB_EVALUADA
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])
        for u in range (0, _CAPAS_COMPLETAS[uu]+1) :
            _ENVIOS[len(_ENVIOS)-1][uu] = u                                  # _ENVIOS
            _SUB_EVALUADA[len(_SUB_EVALUADA)-1][uu] = 1                      # _SUB_EVALUADA
            if u < _CAPAS_COMPLETAS[uu] :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])                   # _ENVIOS
                _SUB_EVALUADA.append(_SUB_EVALUADA[len(_SUB_EVALUADA)-1][:]) # _SUB_EVALUADA


    # NOTA: mini optimizacion del codigo:
    # Se usan en las evaluaciones el vector vacio para que se inicialice la variable "radian = 0" en la funcion "lba".
    # Para evitar la reconstrucción de la nada, se podria inicializar la variable externamente a la funcion,
    # mientras se va llamando reiteradamente, cuando se cambia de subbanda.
    # 2. TESTEA LAS EVALUACIONES (extraccion + reconstruccion) resultando las pendientes (radian)
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # RESPECTO DEL PUNTO ANTERIOR, y no respecto del punto inicial.
        rmse1D_antes = rmse1D
        kbps_antes   = kbps_TM[1] # kbps @@@



        # 2.5. No Pondera las pendientes de los vectores (comentando el código de OPCION 2)  # OPCION 1. Pendientes de VM no ponderados.
        # 2.5. Si Pondera las pendientes de los vectores                                     # OPCION 2. Pendientes de VM si ponderados.
        '''
        try:
            sub_vectores = _SUB_EVALUADA[u][TRLs:].index(1)
            radian       = radian / pow( math.sqrt(2), TRLs - 1 - sub_vectores )
        except ValueError:
            sub_vectores = -1
            '''


        # Recoge los resultados de las evaluaciones: el envio con su radian
        _EVALUACIONES.append([_ENVIOS[u][:], _SUB_EVALUADA[u][:], radian])



    # 4. ORDENA LOS TEST SEGUN SU PENDIENTE
    _EVALUACIONES.sort(key=lambda x:x[2], reverse=True) # Posicion por la que se ordena
    # PRINT (depuracion)
    check_call("mv " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    check_call("echo \"" + "\n# LAS EVALUACIONES TESTEADAS ANTES, AHORA ORDENADAS SEGUN PENDIENTE=RADIAN\n" + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    for u in range (0, len(_EVALUACIONES)) :
        check_call("echo \"" + str(_EVALUACIONES[u])  + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)


    # Elimina los puntos destinados únicamente al cálculo de ángulos y los puntos que resultan en angulo=0.
    u = 0
    longitud = len(_EVALUACIONES)
    while u < longitud : # no se puede usar un for, porque se esta cambiando la longitud del vector recorrido.
        if (0 in _EVALUACIONES[u][0]) or (0 == _EVALUACIONES[u][2]) :
            _EVALUACIONES.pop(u)
            longitud -= 1
        else :
            u += 1


    # En caso de que se envien vectores antes que alguna textura, adelanta el primer envio de texturas.
    for u in range (0, len(_EVALUACIONES)) :
        if 1 in _EVALUACIONES[u][1][:TRLs] : # El primer envio de texturas.
            if u != 0 :
                _EVALUACIONES.insert(0, _EVALUACIONES.pop(u)) # Se mueve el primer envio de texturas al inicio
            break



    # 5. TRADUCE A NOTACION DE ENVIO. Obviando capas vacias.
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]

    for u in range (0, len(_EVALUACIONES)) :
        if _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] < _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] :
            _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # Duplica ultimo elemento
            _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] = _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] # Añade capa al envio

    # PRINT (depuración)
    for u in range (0, len(_ENVIOS)) :
        check_call("echo \"" + str(_ENVIOS[u])  + "\" >> "
                   + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_optimizado"
                   , shell=True)


    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)


    return AVERAGES, RMSEs



##########################################################################################
# 13a. Una subbanda para todas PtAnterior. Con VM manualmente: VM después de su subbanda #
##########################################################################################

def OneSub_ForAll_PtAnterior_VMtrasSub (_CAPAS_COMPLETAS, AVERAGES, RMSEs) : # Evaluaciones -> Optimizado -> Detalle

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []
    _SUB_EVALUADA = []


    # 0. DEFINE QUE SUBBANDA SE ESTA EVALUANDO. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    for uu in range (0, TRLs) :                                              # len(_CAPAS_COMPLETAS) para todas las subbandas (también vectores)
        _ENVIOS.append(_ENVIO_VACIO[:])                                      # _ENVIOS
        _ENVIOS.append(_CAPAS_COMPLETAS[:])
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])                                # _SUB_EVALUADA
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])
        for u in range (0, _CAPAS_COMPLETAS[uu]+1) :
            _ENVIOS[len(_ENVIOS)-1][uu] = u                                  # _ENVIOS
            _SUB_EVALUADA[len(_SUB_EVALUADA)-1][uu] = 1                      # _SUB_EVALUADA
            if u < _CAPAS_COMPLETAS[uu] :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])                   # _ENVIOS
                _SUB_EVALUADA.append(_SUB_EVALUADA[len(_SUB_EVALUADA)-1][:]) # _SUB_EVALUADA

    # NOTA: mini optimizacion del codigo :
    # Se usan en las evaluaciones el vector vacio para que se inicialice la variable "radian = 0" en la funcion "lba".
    # Para evitar la reconstrucción de la nada, se podria inicializar la variable externamente a la funcion,
    # mientras se va llamando reiteradamente, al cambiar de subbanda.


    # 2. TESTEA LAS EVALUACIONES (extraccion + reconstruccion) resultando las pendientes (radian)
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # RESPECTO DEL PUNTO ANTERIOR, y no respecto del punto inicial.
        rmse1D_antes = rmse1D
        kbps_antes   = kbps_TM[1] # kbps @@@


        # Recoge los resultados de las evaluaciones: el envio con su radian
        _EVALUACIONES.append([_ENVIOS[u][:], _SUB_EVALUADA[u][:], radian])



    # 4. ORDENA LOS TEST SEGUN SU PENDIENTE
    _EVALUACIONES.sort(key=lambda x:x[2], reverse=True) # Posicion por la que se ordena
    # PRINT (depuracion)
    check_call("mv " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones", shell=True)
    check_call("echo \"" + "\n# LAS EVALUACIONES TESTEADAS ANTES, AHORA ORDENADAS SEGUN PENDIENTE=RADIAN\n" + "\" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones", shell=True)
    for u in range (0, len(_EVALUACIONES)) :
        check_call("echo \"" + str(_EVALUACIONES[u])  + "\" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones", shell=True)


    # Elimina los puntos destinados únicamente al cálculo de ángulos y los puntos que resultan en angulo=0.
    u = 0
    longitud = len(_EVALUACIONES)
    while u < longitud : # no se puede usar un for, porque se esta cambiando la longitud del vector recorrido.
        if (0 in _EVALUACIONES[u][0]) or (0 == _EVALUACIONES[u][2]) :
            _EVALUACIONES.pop(u)
            longitud -= 1
        else :
            u += 1


    # 4.5 INTRODUCE VM.
    # Genera VM.
    _EVALUACIONES_VM = []
    for uu in range (TRLs, len(_CAPAS_COMPLETAS)) :
        _EVALUACIONES_VM.append([_ENVIO_VACIO[:], _ENVIO_VACIO[:], "radian_no_calculado"])
        for u in range (1, _CAPAS_COMPLETAS[uu]+1) :
            _EVALUACIONES_VM[len(_EVALUACIONES_VM)-1][0][uu] = u                          # _ENVIOS
            _EVALUACIONES_VM[len(_EVALUACIONES_VM)-1][1][uu] = 1                          # _SUB_EVALUADA
            if u < _CAPAS_COMPLETAS[uu] :                                                 # Por si hubiera capas en los VM
                _EVALUACIONES_VM.append([_EVALUACIONES_VM[len(_EVALUACIONES_VM)-1][0][:], _ENVIO_VACIO[:], "radian_no_calculado"])

    #print("EVALUACIONES ANTES: " + str(_EVALUACIONES))    ####
    #print("EVALUACIONES_VM:    " + str(_EVALUACIONES_VM)) ####


    # Inserta los VM en la lista.
    for u in range (0, len(_EVALUACIONES)) :
        try :
            sub_evaluada = _EVALUACIONES[u][1][:TRLs-1].index(1)          # El primer envío de texturas.
            if None != _EVALUACIONES_VM[sub_evaluada] :
                _EVALUACIONES.insert(u+1, _EVALUACIONES_VM[sub_evaluada]) # Se mueve el vector de la lista _EVALUACIONES_VM a _EVALUACIONES.
                _EVALUACIONES_VM[sub_evaluada] = None
                u += 1
                if (TRLs-1) == _EVALUACIONES_VM.count(None) :
                    break
        except:
            pass

    #print("EVALUACIONES DESPUES: " + str(_EVALUACIONES))  ####
    #print("EVALUACIONES_VM:    " + str(_EVALUACIONES_VM)) ####


    # 5. TRADUCE A NOTACION DE ENVIO. Obviando capas vacias.
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]
    for u in range (0, len(_EVALUACIONES)) :
        if _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] < _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] :
            _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # Duplica ultimo elemento
            _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] = _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] # Añade capa al envio

    # PRINT (depuración)
    for u in range (0, len(_ENVIOS)) :
        check_call("echo \"" + str(_ENVIOS[u])  + "\" >> " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_optimizado", shell=True)



    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)


    return AVERAGES, RMSEs



##################################################################################
# 13b. Una subbanda para todas PtAnterior. Sólo hay texturas. Subbandas L y H+MV #
##################################################################################
def OneSub_ForAll_PtAnterior_SoloTexturas (_CAPAS_COMPLETAS, AVERAGES, RMSEs) : # Evaluaciones -> Optimizado -> Detalle

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []
    _SUB_EVALUADA = []


    # 0. DEFINE QUE SUBBANDA SE ESTA EVALUANDO. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    for uu in range (0, len(_CAPAS_COMPLETAS)) :
        _ENVIOS.append(_ENVIO_VACIO[:])                                      # _ENVIOS
        _ENVIOS.append(_CAPAS_COMPLETAS[:])
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])                                # _SUB_EVALUADA
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])
        for u in range (0, _CAPAS_COMPLETAS[uu]+1) :
            _ENVIOS[len(_ENVIOS)-1][uu] = u                                  # _ENVIOS
            _SUB_EVALUADA[len(_SUB_EVALUADA)-1][uu] = 1                      # _SUB_EVALUADA
            if u < _CAPAS_COMPLETAS[uu] :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])                   # _ENVIOS
                _SUB_EVALUADA.append(_SUB_EVALUADA[len(_SUB_EVALUADA)-1][:]) # _SUB_EVALUADA

    # NOTA: mini optimizacion del codigo:
    # Se usan en las evaluaciones el vector vacio para que se inicialice la variable "radian = 0" en la funcion "lba".
    # Para evitar la reconstrucción de la nada, se podria inicializar la variable externamente a la funcion,
    # mientras se va llamando reiteradamente, cuando se cambia de subbanda.
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 16, 16, 16, 16, 1, 1, 1, 1],
               [1, 16, 16, 16, 16, 1, 1, 1, 1],
               [2, 16, 16, 16, 16, 1, 1, 1, 1],
               [3, 16, 16, 16, 16, 1, 1, 1, 1],
               [4, 16, 16, 16, 16, 1, 1, 1, 1],
               [5, 16, 16, 16, 16, 1, 1, 1, 1],
               [6, 16, 16, 16, 16, 1, 1, 1, 1],
               [7, 16, 16, 16, 16, 1, 1, 1, 1],
               [8, 16, 16, 16, 16, 1, 1, 1, 1],
               [9, 16, 16, 16, 16, 1, 1, 1, 1],
               [10, 16, 16, 16, 16, 1, 1, 1, 1],
               [11, 16, 16, 16, 16, 1, 1, 1, 1],
               [12, 16, 16, 16, 16, 1, 1, 1, 1],
               [13, 16, 16, 16, 16, 1, 1, 1, 1],
               [14, 16, 16, 16, 16, 1, 1, 1, 1],
               [15, 16, 16, 16, 16, 1, 1, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 0, 16, 16, 16, 1, 1, 1, 1],
               [16, 1, 16, 16, 16, 1, 1, 1, 1],
               [16, 2, 16, 16, 16, 1, 1, 1, 1],
               [16, 3, 16, 16, 16, 1, 1, 1, 1],
               [16, 4, 16, 16, 16, 1, 1, 1, 1],
               [16, 5, 16, 16, 16, 1, 1, 1, 1],
               [16, 6, 16, 16, 16, 1, 1, 1, 1],
               [16, 7, 16, 16, 16, 1, 1, 1, 1],
               [16, 8, 16, 16, 16, 1, 1, 1, 1],
               [16, 9, 16, 16, 16, 1, 1, 1, 1],
               [16, 10, 16, 16, 16, 1, 1, 1, 1],
               [16, 11, 16, 16, 16, 1, 1, 1, 1],
               [16, 12, 16, 16, 16, 1, 1, 1, 1],
               [16, 13, 16, 16, 16, 1, 1, 1, 1],
               [16, 14, 16, 16, 16, 1, 1, 1, 1],
               [16, 15, 16, 16, 16, 1, 1, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 16, 0, 16, 16, 1, 1, 1, 1],
               [16, 16, 1, 16, 16, 1, 1, 1, 1],
               [16, 16, 2, 16, 16, 1, 1, 1, 1],
               [16, 16, 3, 16, 16, 1, 1, 1, 1],
               [16, 16, 4, 16, 16, 1, 1, 1, 1],
               [16, 16, 5, 16, 16, 1, 1, 1, 1],
               [16, 16, 6, 16, 16, 1, 1, 1, 1],
               [16, 16, 7, 16, 16, 1, 1, 1, 1],
               [16, 16, 8, 16, 16, 1, 1, 1, 1],
               [16, 16, 9, 16, 16, 1, 1, 1, 1],
               [16, 16, 10, 16, 16, 1, 1, 1, 1],
               [16, 16, 11, 16, 16, 1, 1, 1, 1],
               [16, 16, 12, 16, 16, 1, 1, 1, 1],
               [16, 16, 13, 16, 16, 1, 1, 1, 1],
               [16, 16, 14, 16, 16, 1, 1, 1, 1],
               [16, 16, 15, 16, 16, 1, 1, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 16, 16, 0, 16, 1, 1, 1, 1],
               [16, 16, 16, 1, 16, 1, 1, 1, 1],
               [16, 16, 16, 2, 16, 1, 1, 1, 1],
               [16, 16, 16, 3, 16, 1, 1, 1, 1],
               [16, 16, 16, 4, 16, 1, 1, 1, 1],
               [16, 16, 16, 5, 16, 1, 1, 1, 1],
               [16, 16, 16, 6, 16, 1, 1, 1, 1],
               [16, 16, 16, 7, 16, 1, 1, 1, 1],
               [16, 16, 16, 8, 16, 1, 1, 1, 1],
               [16, 16, 16, 9, 16, 1, 1, 1, 1],
               [16, 16, 16, 10, 16, 1, 1, 1, 1],
               [16, 16, 16, 11, 16, 1, 1, 1, 1],
               [16, 16, 16, 12, 16, 1, 1, 1, 1],
               [16, 16, 16, 13, 16, 1, 1, 1, 1],
               [16, 16, 16, 14, 16, 1, 1, 1, 1],
               [16, 16, 16, 15, 16, 1, 1, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 16, 16, 16, 0, 1, 1, 1, 1],
               [16, 16, 16, 16, 1, 1, 1, 1, 1],
               [16, 16, 16, 16, 2, 1, 1, 1, 1],
               [16, 16, 16, 16, 3, 1, 1, 1, 1],
               [16, 16, 16, 16, 4, 1, 1, 1, 1],
               [16, 16, 16, 16, 5, 1, 1, 1, 1],
               [16, 16, 16, 16, 6, 1, 1, 1, 1],
               [16, 16, 16, 16, 7, 1, 1, 1, 1],
               [16, 16, 16, 16, 8, 1, 1, 1, 1],
               [16, 16, 16, 16, 9, 1, 1, 1, 1],
               [16, 16, 16, 16, 10, 1, 1, 1, 1],
               [16, 16, 16, 16, 11, 1, 1, 1, 1],
               [16, 16, 16, 16, 12, 1, 1, 1, 1],
               [16, 16, 16, 16, 13, 1, 1, 1, 1],
               [16, 16, 16, 16, 14, 1, 1, 1, 1],
               [16, 16, 16, 16, 15, 1, 1, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 0, 16, 16, 16, 0, 1, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 16, 0, 16, 16, 1, 0, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 16, 16, 0, 16, 1, 1, 0, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [16, 16, 16, 16, 0, 1, 1, 1, 0],
               [16, 16, 16, 16, 16, 1, 1, 1, 1]]

    print ("\n ENVIOS: " + str(_ENVIOS))
    print ("\n SUB_EVALUADA: " + str(_SUB_EVALUADA))






    # 2. TESTEA LAS EVALUACIONES (extraccion + reconstruccion) resultando las pendientes (radian)
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # RESPECTO DEL PUNTO ANTERIOR, y no respecto del punto inicial.
        rmse1D_antes = rmse1D
        kbps_antes   = kbps_TM[1] # kbps @@@

        # 2.5. No Pondera las pendientes de los vectores (comentando el código de OPCION 2)  # OPCION 1. Pendientes de VM no ponderados.
        # 2.5. Si Pondera las pendientes de los vectores                                     # OPCION 2. Pendientes de VM si ponderados.
        try:
            sub_vectores = _SUB_EVALUADA[u][TRLs:].index(1)
            radian       = radian * pow( math.sqrt(2), TRLs - 1 - sub_vectores )
        except ValueError:
            sub_vectores = -1


        # Recoge los resultados de las evaluaciones: el envio con su radian
        _EVALUACIONES.append([_ENVIOS[u][:], _SUB_EVALUADA[u][:], radian])



    # 4. ORDENA LOS TEST SEGUN SU PENDIENTE
    _EVALUACIONES.sort(key=lambda x:x[2], reverse=True) # Posicion por la que se ordena
    # PRINT (depuracion)
    check_call("mv " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    check_call("echo \"" + "\n# LAS EVALUACIONES TESTEADAS ANTES, AHORA ORDENADAS SEGUN PENDIENTE=RADIAN\n" + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    for u in range (0, len(_EVALUACIONES)) :
        check_call("echo \"" + str(_EVALUACIONES[u])  + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)


    # Elimina los puntos destinados únicamente al cálculo de ángulos y los puntos que resultan en angulo=0.
    u = 0
    longitud = len(_EVALUACIONES)
    while u < longitud : # no se puede usar un for, porque se esta cambiando la longitud del vector recorrido.
        if (0 in _EVALUACIONES[u][0]) or (0 == _EVALUACIONES[u][2]) :
            _EVALUACIONES.pop(u)
            longitud -= 1
        else :
            u += 1


    # En caso de que se envien vectores antes que alguna textura, adelanta el primer envio de texturas.
    for u in range (0, len(_EVALUACIONES)) :
        if 1 in _EVALUACIONES[u][1][:TRLs] : # El primer envio de texturas.
            if u != 0 :
                _EVALUACIONES.insert(0, _EVALUACIONES.pop(u)) # Se mueve el primer envio de texturas al inicio
            break



    # 5. TRADUCE A NOTACION DE ENVIO. Obviando capas vacias.
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]

    for u in range (0, len(_EVALUACIONES)) :
        if _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] < _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] :
            _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # Duplica ultimo elemento
            _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] = _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] # Añade capa al envio

    # PRINT (depuración)
    for u in range (0, len(_ENVIOS)) :
        check_call("echo \"" + str(_ENVIOS[u])  + "\" >> "
                   + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_optimizado"
                   , shell=True)


    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)


    return AVERAGES, RMSEs



################################################################################
# 13c. Una subbanda para todas PtAnterior. Ponderación por motion_?_importance #
################################################################################

def OneSub_ForAll_PtAnterior_motionImportance (_CAPAS_COMPLETAS, AVERAGES, RMSEs) : # Evaluaciones -> Optimizado -> Detalle

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []
    _SUB_EVALUADA = []


    # 0. DEFINE QUE SUBBANDA SE ESTA EVALUANDO. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    for uu in range (0, len(_CAPAS_COMPLETAS)) :
        _ENVIOS.append(_ENVIO_VACIO[:])                                      # _ENVIOS
        _ENVIOS.append(_CAPAS_COMPLETAS[:])
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])                                # _SUB_EVALUADA
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])
        for u in range (0, _CAPAS_COMPLETAS[uu]+1) :
            _ENVIOS[len(_ENVIOS)-1][uu] = u                                  # _ENVIOS
            _SUB_EVALUADA[len(_SUB_EVALUADA)-1][uu] = 1                      # _SUB_EVALUADA
            if u < _CAPAS_COMPLETAS[uu] :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])                   # _ENVIOS
                _SUB_EVALUADA.append(_SUB_EVALUADA[len(_SUB_EVALUADA)-1][:]) # _SUB_EVALUADA

    # NOTA: mini optimizacion del codigo:
    # Se usan en las evaluaciones el vector vacio para que se inicialice la variable "radian = 0" en la funcion "lba".
    # Para evitar la reconstrucción de la nada, se podria inicializar la variable externamente a la funcion,
    # mientras se va llamando reiteradamente, cuando se cambia de subbanda.



    # Carga los ficheros de importancia de los VM (2.5)
    motion_importance = []
    for sub in range (1, TRLs) :
        f = open(MOTION + str(sub) + "_importance_sub", 'r')
        motion_importance.insert(0, map(float, f.readlines())) # [motion_4, motion_3, motion_2, motion_1]
        f.close()


    # 2. TESTEA LAS EVALUACIONES (extraccion + reconstruccion) resultando las pendientes (radian)
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # RESPECTO DEL PUNTO ANTERIOR, y no respecto del punto inicial.
        rmse1D_antes = rmse1D
        kbps_antes   = kbps_TM[1] # kbps @@@


        # 2.5. Pondera las pendientes de los vectores
        try :
            sub_vectores = _SUB_EVALUADA[u][TRLs:].index(1) # sub_vectores=0 elevado=4, 1 3, 2 2, 3 1.
            radian       = radian / pow( (1 - motion_importance[sub_vectores][iGOP-1]) + 1, TRLs - 1 - sub_vectores )      # OPCION 1. 13c_div_1MenosImportanciaMas1_elevadoSub
            #radian      = radian / pow( motion_importance[sub_vectores][iGOP-1] + 1, TRLs - 1 - sub_vectores )            # OPCION 2. 13c_div_ImportanciaMas1_elevadoSub
            #radian      = radian /      motion_importance[sub_vectores][iGOP-1] + 1                                       # OPCION 3. 13c_div_ImportanciaMas1

        except ValueError :
            sub_vectores = -1


        # Recoge los resultados de las evaluaciones: el envio con su radian
        _EVALUACIONES.append([_ENVIOS[u][:], _SUB_EVALUADA[u][:], radian])


    # 4. ORDENA LOS TEST SEGUN SU PENDIENTE
    _EVALUACIONES.sort(key=lambda x:x[2], reverse=True) # Posicion por la que se ordena
    # PRINT (depuracion)
    check_call("mv " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    check_call("echo \"" + "\n# LAS EVALUACIONES TESTEADAS ANTES, AHORA ORDENADAS SEGUN PENDIENTE=RADIAN\n" + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    for u in range (0, len(_EVALUACIONES)) :
        check_call("echo \"" + str(_EVALUACIONES[u])  + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)


    # Elimina los puntos destinados únicamente al cálculo de ángulos y los puntos que resultan en angulo=0.
    u = 0
    longitud = len(_EVALUACIONES)
    while u < longitud : # no se puede usar un for, porque se esta cambiando la longitud del vector recorrido.
        if (0 in _EVALUACIONES[u][0]) or (0 == _EVALUACIONES[u][2]) :
            _EVALUACIONES.pop(u)
            longitud -= 1
        else :
            u += 1


    # En caso de que se envien vectores antes que alguna textura, adelanta el primer envio de texturas.
    for u in range (0, len(_EVALUACIONES)) :
        if 1 in _EVALUACIONES[u][1][:TRLs] : # El primer envio de texturas.
            if u != 0 :
                _EVALUACIONES.insert(0, _EVALUACIONES.pop(u)) # Se mueve el primer envio de texturas al inicio
            break



    # 5. TRADUCE A NOTACION DE ENVIO. Obviando capas vacias.
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]

    for u in range (0, len(_EVALUACIONES)) :
        if _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] < _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] :
            _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # Duplica ultimo elemento
            _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] = _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] # Añade capa al envio

    # PRINT (depuración)
    for u in range (0, len(_ENVIOS)) :
        check_call("echo \"" + str(_ENVIOS[u])  + "\" >> "
                   + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_optimizado"
                   , shell=True)


    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)

    return AVERAGES, RMSEs



###################################################################################################################################
# 13d. Una subbanda para todas PtAnterior. Reducción de M_max hasta L. Y reducción de Mx proporcionalmente a la primera reducción #
###################################################################################################################################

def OneSub_ForAll_PtAnterior_escalaProporcionalVM (_CAPAS_COMPLETAS, AVERAGES, RMSEs) : # Evaluaciones -> Optimizado -> Detalle

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []
    _SUB_EVALUADA = []


    # 0. DEFINE QUE SUBBANDA SE ESTA EVALUANDO. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    for uu in range (0, len(_CAPAS_COMPLETAS)) :
        _ENVIOS.append(_ENVIO_VACIO[:])                                      # _ENVIOS
        _ENVIOS.append(_CAPAS_COMPLETAS[:])
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])                                # _SUB_EVALUADA
        _SUB_EVALUADA.append(_ENVIO_VACIO[:])
        for u in range (0, _CAPAS_COMPLETAS[uu]+1) :
            _ENVIOS[len(_ENVIOS)-1][uu] = u                                  # _ENVIOS
            _SUB_EVALUADA[len(_SUB_EVALUADA)-1][uu] = 1                      # _SUB_EVALUADA
            if u < _CAPAS_COMPLETAS[uu] :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])                   # _ENVIOS
                _SUB_EVALUADA.append(_SUB_EVALUADA[len(_SUB_EVALUADA)-1][:]) # _SUB_EVALUADA

    # NOTA: mini optimizacion del codigo:
    # Se usan en las evaluaciones el vector vacio para que se inicialice la variable "radian = 0" en la funcion "lba".
    # Para evitar la reconstrucción de la nada, se podria inicializar la variable externamente a la funcion,
    # mientras se va llamando reiteradamente, cuando se cambia de subbanda.



    # Carga los ficheros de importancia de los VM (2.5)
    motion_importance = []
    for sub in range (1, TRLs) :
        f = open(MOTION + str(sub) + "_importance_sub", 'r')
        motion_importance.insert(0, map(float, f.readlines())) # [motion_4, motion_3, motion_2, motion_1]
        f.close()


    # 2. TESTEA LAS EVALUACIONES (extraccion + reconstruccion) resultando las pendientes (radian)
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # RESPECTO DEL PUNTO ANTERIOR, y no respecto del punto inicial.
        rmse1D_antes = rmse1D
        kbps_antes   = kbps_TM[1] # kbps @@@


        # 2.5. Reduce las pendientes de los vectores

        # Pendiente de capa1_L
        try :
            # if
            _SUB_EVALUADA[u][:1].index(1)
            _ENVIOS      [u][:1].index(1)
            # do
            radian_L1    = radian
        except ValueError :
            pass

        # Escala la pendiente de M_máxima
        try :
            # IF
            _SUB_EVALUADA[u][TRLs:TRLs+1].index(1)
            _ENVIOS      [u][TRLs:TRLs+1].index(1)
            # DO
            radian_Mmax  = radian
            #radian      = radian_L1 - 0.0000000001 # Un valor muy pequeño cualquiera                               # OPCIÓN 1
            #radian      = radian_L1 * radian                                                                       # OPCIÓN 2
            radian       = radian_L1 *  motion_importance[0][iGOP-1]                                                # OPCIÓN 3 <- la mejor
            #radian      = radian_L1 * (motion_importance[0][iGOP-1] + 1)                                           # OPCIÓN 4
        except ValueError :
            pass

        # Escala los M_noMáxima proporcionalmente a la escala sufrida por M_máxima
        try :
            # IF
            sub_vectores = _SUB_EVALUADA[u][TRLs+1:].index(1)
            _ENVIOS[u][TRLs+1+sub_vectores:TRLs+1+sub_vectores+1].index(1)
            # DO
            #radian      =  (radian * radian_L1) / radian_Mmax                                                      # OPCIÓN 1
            #radian      = ((radian * radian_L1) / radian_Mmax) * radian                                            # OPCIÓN 2
            radian       = ((radian * radian_L1) / radian_Mmax) *  motion_importance[sub_vectores+1][iGOP-1]        # OPCIÓN 3 <- la mejor
            #radian      = ((radian * radian_L1) / radian_Mmax) * (motion_importance[sub_vectores+1][iGOP-1] + 1)   # OPCIÓN 4
        except ValueError :
            pass

        # Recoge los resultados de las evaluaciones: el envio con su radian
        _EVALUACIONES.append([_ENVIOS[u][:], _SUB_EVALUADA[u][:], radian])



    # 4. ORDENA LOS TEST SEGUN SU PENDIENTE
    _EVALUACIONES.sort(key=lambda x:x[2], reverse=True) # Posicion por la que se ordena
    # PRINT (depuracion)
    check_call("mv " + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_detalle "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    check_call("echo \"" + "\n# LAS EVALUACIONES TESTEADAS ANTES, AHORA ORDENADAS SEGUN PENDIENTE=RADIAN\n" + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)
    for u in range (0, len(_EVALUACIONES)) :
        check_call("echo \"" + str(_EVALUACIONES[u])  + "\" >> "
                     + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_evaluaciones"
                     , shell=True)


    # Elimina los puntos destinados únicamente al cálculo de ángulos y los puntos que resultan en angulo=0.
    u = 0
    longitud = len(_EVALUACIONES)
    while u < longitud : # no se puede usar un for, porque se esta cambiando la longitud del vector recorrido.
        if (0 in _EVALUACIONES[u][0]) or (0 == _EVALUACIONES[u][2]) :
            _EVALUACIONES.pop(u)
            longitud -= 1
        else :
            u += 1


    # En caso de que se envien vectores antes que alguna textura, adelanta el primer envio de texturas.
    for u in range (0, len(_EVALUACIONES)) :
        if 1 in _EVALUACIONES[u][1][:TRLs] : # El primer envio de texturas.
            if u != 0 :
                _EVALUACIONES.insert(0, _EVALUACIONES.pop(u)) # Se mueve el primer envio de texturas al inicio
            break



    # 5. TRADUCE A NOTACION DE ENVIO. Obviando capas vacias.
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0]]

    for u in range (0, len(_EVALUACIONES)) :
        if _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] < _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] :
            _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:]) # Duplica ultimo elemento
            _ENVIOS[len(_ENVIOS)-1][_EVALUACIONES[u][1].index(1)] = _EVALUACIONES[u][0][_EVALUACIONES[u][1].index(1)] # Añade capa al envio

    # PRINT (depuración)
    for u in range (0, len(_ENVIOS)) :
        check_call("echo \"" + str(_ENVIOS[u])  + "\" >> "
                   + str(INFO) + "_GOP" + str(iGOP) + "de" + str(GOPs) + "_optimizado"
                   , shell=True)


    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)

    return AVERAGES, RMSEs


###################################################################################################################
# 14. Envio de subbandas por igual [1,1,...], [2,2,...]. Usando slopes según el doble de importancia por subbanda #
###################################################################################################################

def sub_por_igual (_CAPAS_COMPLETAS, AVERAGES, RMSEs) : # Evaluaciones -> Optimizado -> Detalle

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []

    # 0. DEFINE QUE SUBBANDA SE ESTA EVALUANDO. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    _ENVIOS = [[0, 0, 0, 0, 0, 0, 0, 0, 0],
               [1, 1, 1, 1, 1, 1, 1, 1, 1],
               [2, 2, 2, 2, 2, 1, 1, 1, 1],
               [3, 3, 3, 3, 3, 1, 1, 1, 1],
               [4, 4, 4, 4, 4, 1, 1, 1, 1],
               [5, 5, 5, 5, 5, 1, 1, 1, 1],
               [6, 6, 6, 6, 6, 1, 1, 1, 1],
               [7, 7, 7, 7, 7, 1, 1, 1, 1],
               [8, 8, 8, 8, 8, 1, 1, 1, 1],
               [9, 9, 9, 9, 9, 1, 1, 1, 1],
               [10, 10, 10, 10, 10, 1, 1, 1, 1],
               [11, 11, 11, 11, 11, 1, 1, 1, 1],
               [12, 12, 12, 12, 12, 1, 1, 1, 1],
               [13, 13, 13, 13, 13, 1, 1, 1, 1],
               [14, 14, 14, 14, 14, 1, 1, 1, 1],
               [15, 15, 15, 15, 15, 1, 1, 1, 1],
               [16, 16, 16, 16, 16, 1, 1, 1, 1]]

    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)


    return AVERAGES, RMSEs


#####################################
# Punto 2. del PAPER0. For Subbands #
##################################### Niveles subbandas Todo L4 capa a capa, M4, todo H3 capa a capa, M3, todo H2 capa a capa, M2, ...
                                    # 1capa_L4, 2capa_L4, 3capa_L4, ... M4, 1capa_H4, 2capa_H4, 3capa_H4, ... , M3,
def for_Subbands (_CAPAS_COMPLETAS, AVERAGES, RMSEs) :

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []

    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    _ENVIOS.append(_ENVIO_VACIO[:])
    for uu in range (0, TRLs) :
        for u in range (0, _CAPAS_COMPLETAS[uu]+1) :
            _ENVIOS[len(_ENVIOS)-1][uu] = u
            if u < _CAPAS_COMPLETAS[uu] :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])
            if u == _CAPAS_COMPLETAS[uu] and uu < TRLs-1 :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])
                _ENVIOS[len(_ENVIOS)-1][uu+TRLs] = 1

    #print '\n'.join(map(str, _ENVIOS))

    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)

    return AVERAGES, RMSEs

###################################
# Punto 3. del PAPER0. For Layers #
################################### Niveles de capas, capa a capa: todas las primeras capas de cada subbanda, todos los vectores, las segundas capas, las terceras ...
                                  # 1capa_L4, M4, 1capa_H4, M3, 1capa_H3, M2, 1capa_H2, M1, 1capa_H1, 2capa_L4, 2capa_H4, 2capa_H3, 2capa_H2, 2capa_H1, 3capa_L4, 3capa_H4, ....
def for_Layers (_CAPAS_COMPLETAS, AVERAGES, RMSEs) :

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []

    # 1. DEFINE LAS EVALUACIONES. Inicializacion de _ENVIOS (variable que describe los envios, ahora para las evaluaciones)
    _ENVIOS.append(_ENVIO_VACIO[:])
    _ENVIOS.append(_ENVIO_VACIO[:])
    for u in range (1, Ncapas_T+1) :
        for uu in range (0, TRLs) :
            _ENVIOS[len(_ENVIOS)-1][uu] = u
            if _ENVIOS[len(_ENVIOS)-1][TRLs-1] < Ncapas_T :
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])
            if uu < TRLs-1 and 0 == _ENVIOS[len(_ENVIOS)-1][uu+TRLs] :
                _ENVIOS[len(_ENVIOS)-1][uu+TRLs] = 1
                _ENVIOS.append(_ENVIOS[len(_ENVIOS)-1][:])

    #print '\n'.join(map(str, _ENVIOS))

    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)


    return AVERAGES, RMSEs


######################################
# Punto 4. del PAPER0. Gains Layers #
###################################### Enviar capas de cada subbanda segun GAINS.

def Gains_Layers (_CAPAS_COMPLETAS, AVERAGES, RMSEs) :

    # Variables de lba (python pide declararlas)
    kbps_TM = kbps_ALL = rmse1D = kbps_antes = rmse1D_antes = radian = radian_candidato = kbps_candidato = rmse1D_candidato = emptyLayer = KBPS_DATA = CANDIDATO_KBPS = 0
    _CANDIDATO = _CANDIDATO_REDUCES = _CANDIDATO_REDUCES_normalized = []

    # Variables
    _ENVIO_VACIO  = ([0] * len(_CAPAS_COMPLETAS))
    _ENVIOS       = []
    _EVALUACIONES = []

    # GAINS 5TRLs = [1.0877939347, 2.1250255455, 3.8884779989, 5.8022196044] = [1, 2, 4, 6]
    #            [1,2,4,6]


    _ENVIOS = [[0,0,0,0,0,0,0,0,0],
               [1,0,0,0,0,0,0,0,0],
               [1,0,0,0,0,1,0,0,0],
               [1,1,0,0,0,1,0,0,0],
               [2,1,0,0,0,1,0,0,0],
               [2,2,0,0,0,1,0,0,0],
               [2,2,0,0,0,1,1,0,0],
               [2,2,1,0,0,1,1,0,0],
               [3,2,1,0,0,1,1,0,0],
               [3,3,1,0,0,1,1,0,0],
               [4,3,1,0,0,1,1,0,0],
               [4,4,1,0,0,1,1,0,0],
               [4,4,2,0,0,1,1,0,0],
               [4,4,2,0,0,1,1,1,0],
               [4,4,2,1,0,1,1,1,0],
               [5,4,2,1,0,1,1,1,0],
               [5,5,2,1,0,1,1,1,0],
               [6,5,2,1,0,1,1,1,0],
               [6,6,2,1,0,1,1,1,0],
               [6,6,3,1,0,1,1,1,0],
               [6,6,3,1,0,1,1,1,1],
               [6,6,3,1,1,1,1,1,1],
               [7,6,3,1,1,1,1,1,1],
               [7,7,3,1,1,1,1,1,1],
               [8,7,3,1,1,1,1,1,1],
               [8,8,3,1,1,1,1,1,1],
               [8,8,4,1,1,1,1,1,1],
               [8,8,4,2,1,1,1,1,1],
               [9,8,4,2,1,1,1,1,1],
               [9,9,4,2,1,1,1,1,1],
               [10,9,4,2,1,1,1,1,1],
               [10,10,4,2,1,1,1,1,1],
               [10,10,5,2,1,1,1,1,1],
               [11,10,5,2,1,1,1,1,1],
               [11,11,5,2,1,1,1,1,1],
               [12,11,5,2,1,1,1,1,1],
               [12,12,5,2,1,1,1,1,1],
               [12,12,6,2,1,1,1,1,1],
               [12,12,6,3,1,1,1,1,1],
               [12,12,6,3,2,1,1,1,1],
               [13,12,6,3,2,1,1,1,1],
               [13,13,6,3,2,1,1,1,1],
               [13,13,6,3,2,1,1,1,1],
               [14,13,6,3,2,1,1,1,1],
               [14,14,6,3,2,1,1,1,1],
               [14,14,7,3,2,1,1,1,1],
               [15,14,7,3,2,1,1,1,1],
               [15,15,7,3,2,1,1,1,1],
               [16,15,7,3,2,1,1,1,1],
               [16,16,7,3,2,1,1,1,1],
               [16,16,8,3,2,1,1,1,1], # GAINS 5TRLs = [1.953518472, 3.574645781, 5.333932668] = [2, 4, 5]
               [16,16,8,4,2,1,1,1,1], # GAINS 5TRLs = [1.829850003, 2.730423461] = [2, 3]
               [16,16,9,4,2,1,1,1,1],
               [16,16,9,4,3,1,1,1,1],
               [16,16,10,4,3,1,1,1,1],
               [16,16,10,5,3,1,1,1,1],
               [16,16,11,5,3,1,1,1,1],
               [16,16,12,5,3,1,1,1,1],
               [16,16,12,6,3,1,1,1,1],
               [16,16,12,6,4,1,1,1,1],
               [16,16,13,6,4,1,1,1,1],
               [16,16,14,6,4,1,1,1,1],
               [16,16,14,7,4,1,1,1,1],
               [16,16,15,7,4,1,1,1,1],
               [16,16,15,7,5,1,1,1,1],
               [16,16,16,7,5,1,1,1,1],
               [16,16,16,8,5,1,1,1,1],
               [16,16,16,8,6,1,1,1,1], # GAINS 5TRLs = [1.492156984] = [1]
               [16,16,16,8,7,1,1,1,1],
               [16,16,16,8,8,1,1,1,1],
               [16,16,16,9,8,1,1,1,1],
               [16,16,16,9,9,1,1,1,1],
               [16,16,16,10,9,1,1,1,1],
               [16,16,16,10,10,1,1,1,1],
               [16,16,16,11,10,1,1,1,1],
               [16,16,16,11,11,1,1,1,1],
               [16,16,16,12,11,1,1,1,1],
               [16,16,16,12,12,1,1,1,1],
               [16,16,16,13,12,1,1,1,1],
               [16,16,16,13,13,1,1,1,1],
               [16,16,16,14,13,1,1,1,1],
               [16,16,16,14,14,1,1,1,1],
               [16,16,16,15,14,1,1,1,1],
               [16,16,16,15,15,1,1,1,1],
               [16,16,16,16,15,1,1,1,1],
               [16,16,16,16,16,1,1,1,1]]


    # . COMPROBACION DEL ENVIO OPTIMIZADO
    for u in range (0, len(_ENVIOS)) :
        _COMBINATION = _ENVIOS[u][:]
        kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

        # Recoge AVERAGES #
        AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)

    return AVERAGES, RMSEs




##################################################
# AVERAGES de GOPs 1 hasta N. Media no ponderada #
##################################################
#GOPs=2
#AVERAGES = [[1], [2,3,4], [5,6,7]]                                                     # kbps
#RMSEs    = [[0], [2,3,4], [5,6,7]]                                                     # rmse

def averages_1toN (AVERAGES, RMSEs) :
    AVERAGES.append([])                         # Media no ponderada de los gops 1 hasta N en kbps
    RMSEs.append   ([])                         # Media no ponderada de los gops 1 hasta N en rmse
    for kbps in range (0, len(AVERAGES[1])) :
        AVERAGES[len(AVERAGES)-1].append(0)                                                 # kbps
        RMSEs   [len(RMSEs   )-1].append(0)                                                 # rmse
        for gop in range (1, len(AVERAGES)-1) :
            try :
                AVERAGES[len(AVERAGES)-1][kbps] += AVERAGES[gop][kbps]                      # kbps
                RMSEs   [len(RMSEs   )-1][kbps] += RMSEs   [gop][kbps]                      # rmse
            except IndexError :
                AVERAGES[len(AVERAGES)-1].pop(kbps)                                         # kbps
                RMSEs   [len(RMSEs   )-1].pop(kbps)                                         # rmse
                return AVERAGES, RMSEs
        AVERAGES[len(AVERAGES)-1][kbps] = (1.0 * AVERAGES[len(AVERAGES)-1][kbps]) / GOPs    # kbps
        RMSEs   [len(RMSEs   )-1][kbps] = (1.0 * RMSEs   [len(RMSEs   )-1][kbps]) / GOPs    # rmse
    return AVERAGES, RMSEs


###########################################
# AVERAGES de GOPs 0 y N. Media ponderada #
###########################################
#pictures = 17
#AVERAGES=[[1], [2, 3, 4], [5, 6], [3.5, 4.5]]

def averages_0yN (AVERAGES) :
    pictures    = GOPs * GOP_size + 1 # ! deben ser todas las imagenes de todos los gops
    ponderacion = (pictures - 1.0) / pictures
    AVERAGES.append([])
    for kbps in range (0, len(AVERAGES[len(AVERAGES)-2])) :
        AVERAGES[len(AVERAGES)-1].append(0)
        AVERAGES[len(AVERAGES)-1][kbps] = (AVERAGES[0][kbps] * (1 - ponderacion)) + (AVERAGES[len(AVERAGES)-2][kbps] * ponderacion)
    return AVERAGES
# [[1], [2, 3, 4], [5, 6, 7], [3.5, 4.5, 5.5], [3.352941176470588, 4.294117647058823, 5.235294117647059]]


########################################
# AVERAGES de GOPs a fichero (gnuplot) #
########################################
#from subprocess   import check_call
#INFO     = "info"
#AVERAGES = [[1], [2, 3, 4], [5, 6, 7], [3.5, 4.5, 5.5], [3.352941176470588, 4.294117647058823, 5.235294117647059]]
#RMSEs    = [[0], [2, 3, 4], [5, 6, 7], [3.3, 4.2, 5.2]]

def averages_file (AVERAGES, RMSEs) :
    # PRINT en bruto
    check_call("echo \"\nAVERAGES\n" + str(AVERAGES) + "\" >> " + str(INFO) + "_" + str(GOPs) + "GOPs" + "_averages", shell=True)
    check_call("echo \"\nRMSEs   \n" + str(RMSEs)    + "\" >> " + str(INFO) + "_" + str(GOPs) + "GOPs" + "_averages", shell=True)
    # PRINT para gnuplot
    for u in range (0, len(AVERAGES[len(AVERAGES)-1])) :
        try :
            average = str(AVERAGES[len(AVERAGES)-1][u])
            rmse    = str(RMSEs   [len(RMSEs   )-1][u])
            check_call("echo \"" + average + "\t " + rmse + "\" >> " + str(INFO) + "_" + str(GOPs) + "GOPs" + "_averages_gnuplot", shell=True)
        except IndexError :
            break

    # Tras archivar las medias, inicializa variables. (No necesario..)
    AVERAGES         = [[] for x in xrange (GOPs + 1)]
    RMSEs            = [[] for x in xrange (GOPs + 1)]
    return AVERAGES, RMSEs


################################################################
#                           MAIN                               #
################################################################

# RUTAS
p = sub.Popen("echo $PWD", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
out, err     = p.communicate()
path_base    = out[:-1]
path_extract = path_base + "/extract"
path_tmp     = path_base + "/tmp"

# Inicialization
N_subbands = (TRLs * 2) - 1
gop        = GOP()
GOP_size   = gop.get_size(TRLs)
pictures   = GOPs * GOP_size + 1
#fields    = pictures / 2
duration   = pictures / (FPS * 1.0)
snr_file   = "low_0" # Fichero con el que se compara para el snr

# Variables
H_max      = 1
M_max      = TRLs
Nclevels_T = 0 # Cantidad máxima de reduces disponibles. También supeditado a la divisibilidad entera del nº de blocks_in_x y blocks_in_y.
Nclevels_M = 0 # 1
Ncapas_M   = 1

#Ncapas_T        = # -clayers que se usó en el kdu_compress
#max_iteraciones = (TRLs * Ncapas_T * (Nclevels_T+1)) + (((TRLs-1) * Ncapas_M) * (Nclevels_M+1))

# Parámetros de función
_RATES_Y = [[0] for x in xrange (TRLs)]
_RATES_U = [[0] for x in xrange (TRLs)]
_RATES_V = [[0] for x in xrange (TRLs)]

pics = pictures
for z in range (1, TRLs) :
    pics = (pics + 1) / 2
    for image_number in range (0, pics-2) :
        _RATES_Y[TRLs-z].append( 0 )
        _RATES_U[TRLs-z].append( 0 )
        _RATES_V[TRLs-z].append( 0 )



_CAPAS_COMPLETAS = ([Ncapas_T] * TRLs) + ([Ncapas_M] * (TRLs-1))
RMSEs            = [[] for x in xrange (GOPs + 1)] # rmse: [[GOP0],                                   <- Tantos 0    como puntos en la curva.
                                                   #        [GOP1], ..., [GOPn],                      <- Tantos RMSE como puntos en la curva de cada GOP.
                                                   #        [Media no ponderada del GOP 1 hasta N]]

AVERAGES         = [[] for x in xrange (GOPs + 1)] # kbps: [[GOP0],                                   <- Tantos kbps como puntos en la curva de cada GOP0.
                                                   #        [GOP1], ..., [GOPn],                      <- Tantos kbps como puntos en la curva de cada GOP.
                                                   #        [Media no ponderada del GOP 1 hasta N],
                                                   #        [Media si ponderada del GOP 0 y     N]]
# Ej. AVERAGES[iGOP][kbps_punto].
#
# Ej para 1 GOP [[10860.9, 22089.8], [2530.2, 3472.6], [2530.2, 3472.6], [3020.2, 4567.7]]
#               [[     GOP0       ], [     GOP1     ], [   Media 1aN  ], [  Media Final ]]
#               [[Punto1 , Punto2 ], [Punto1, Punto2], [Punto1, Punto2], [Punto1, Punto2]]
#
# La curva del GOP1: AVERAGES[1][0] <- Punto1 de la curva.
#                    AVERAGES[1][1] <- Punto2 de la curva.
# La curva media del vídeo: AVERAGES[3][0] <- Punto1 de la curva.
#                           AVERAGES[3][1] <- Punto2 de la curva.



# Variables de lba (python pide declararlas)
KBPS_DATA        = ""
CANDIDATO_KBPS   = ""

kbps_antes       = 0
kbps_candidato   = [0, 0]
kbps_TM          = [0, 0]
kbps_ALL         = 0

rmse1D           = 0
rmse1D_antes     = MAX_VALUE
rmse1D_candidato = 0

radian_candidato = -MAX_VALUE
radian           = 0

emptyLayer       = 0

_CEROS           = [0] * N_subbands
_CAPAS           = [0] * N_subbands
_COMBINATION     = [0] * N_subbands
_CANDIDATO       = [0] * N_subbands
#_CAPAS_VACIAS = # para la optimización

# Esta forma de inicializar un list funciona para un list pero no para un list de lists
_COMBINATION_REDUCES            = ([Nclevels_T+1] * TRLs) + ([Nclevels_M+1] * (TRLs-1)) # +1 pq el BRC primero modifica y despues evalua
_CANDIDATO_REDUCES              = _COMBINATION_REDUCES[:]
_REDUCES_normalizer             = ([Nclevels_T] * TRLs) + ([Nclevels_M] * (TRLs-1))
_CANDIDATO_REDUCES_normalized   = []
_COMBINATION_REDUCES_normalized = []

# Inicializa _REDUCES
_REDUCES = map(int, discard_SRLs.split(','))

error = False
if len(_REDUCES) != N_subbands :
    check_call("echo discard_SRLs: its length must be " + str(N_subbands) + " with TRL=" + str(TRLs) + ".", shell=True) # Types
    error = True
#if que no supere Nclevels_M ni Nclevels_T

if error == True :
    _REDUCES = [0] * N_subbands #_REDUCES = ([Nclevels_T] * TRLs) + ([Nclevels_M] * (TRLs-1))
    check_call("echo discard_SRLs default = " + str(_REDUCES) + "   Press ENTER to continue...", shell=True) # Types

if BRC == MAX_VALUE :
    INFO = str(path_base) + "/info_" + str(TRLs) + "_" + ','.join(map(str, _CAPAS_COMPLETAS)) + "." + ''.join(map(str, _REDUCES))
else :
    INFO = str(path_base) + "/info_" + str(TRLs) + "_" + str(BRC) + "_" + ','.join(map(str, _CAPAS_COMPLETAS)) + "." + ''.join(map(str, _REDUCES))

_COMBINATION_REDUCES = _REDUCES[:]
_REDUCES_normalizer  = _REDUCES[:]
_CANDIDATO_REDUCES   = _REDUCES[:]

# Desnormaliza _CANDIDATO_REDUCES
for i in range (0, len(_REDUCES)) :
    if _REDUCES[i] > 0 :
        _CANDIDATO_REDUCES[i] += 1








############################### ############################### ###############################
############################### ############################### ###############################
#           MAIN              # #           MAIN              # #           MAIN              #
############################### ############################### ###############################
############################### ############################### ###############################


####################################################
# UNA TRANSCODIFICACIÓN DIRECTA DEL VIDEO COMPLETO #
#################################################### FALTA DEPURAR !!
'''
#_COMBINATION = [1, 1, 1, 1, 1, 1, 1, 1, 1]
#_COMBINATION = _CAPAS_COMPLETAS[:]
iGOPs = 1
GOPs_to_expand = GOPs
p = sub.Popen("mv " + str(path_base) + "/low_0 " + str(path_base) + "/low_0" + str(iGOP)
              , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
out, err = p.communicate()
#kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba (pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES)
#exit (0)
'''

###############################
###############################
#           BRC               #
###############################
###############################

p = sub.Popen("mv " + str(path_base) + "/low_0 " + str(path_base) + "/low_0_original"
              , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
out, err = p.communicate()


############################################
# TRATA EL VIDEO POR SUBCONJUNTOS DE GOP/s #
############################################
for iGOP in range (1, GOPs+1) : # iGOP = 1 quiere decir que se trata el GOP 1 (el GOP = 0, sólo contiene la primera L)
    # Imagen Inicial y Final del GOP tratado (iGOP)
    FIRST_picture_ofGOP =  (iGOP - 1) * GOP_size
    pictures            =   iGOP      * GOP_size + 1

    # 3º y 4º
    #FIRST_picture_ofGOP =  (3   - 1) * GOP_size
    #pictures            =   4        * GOP_size + 1

    # 1º, 2º y 3º
    #FIRST_picture_ofGOP =  0
    #pictures            =  3         * GOP_size + 1


    GOPs_to_expand = ((pictures-1) - FIRST_picture_ofGOP) / GOP_size # Para extraer 1 sólo GOP sería igual a 1 para el expand

    ######################################################
    # PARTE EL VIDEO ORIGINAL SEGÚN LO/s GOP/s TRATADO/s #
    ######################################################

    p = sub.Popen("dd"
                  + " if="    + str(path_base) + "/low_0_original"
                  + " of="    + str(path_base) + "/low_0" + str(iGOP)
                  + " skip="  + str(GOP_size * (iGOP - 1))                # nº imagenes de un GOP * iGOP
                  + " bs="    + str(int(pixels_in_x * pixels_in_y * 1.5)) # tamaño de una imágen
                  + " count=" + str((GOP_size * GOPs_to_expand) + 1)      # GOPs_to_expand
                  , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    out, err = p.communicate()


    ###########################################
    # UNA TRANSCODIFICACIÓN DIRECTA GOP A GOP #
    ########################################### Consiste en 1 única transcodificación. Sin aplicar ningún tipo de ordenación entre capas.

    #_COMBINATION = [1, 1, 1, 1, 1, 1, 1, 1, 1]
    _COMBINATION = _CAPAS_COMPLETAS[:]
    kbps_TM, kbps_ALL, rmse1D, kbps_antes, rmse1D_antes, radian, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, KBPS_DATA, CANDIDATO_KBPS = lba(FIRST_picture_ofGOP, pictures, kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _COMBINATION, _COMBINATION_REDUCES, snr_file)

    # Recoge AVERAGES #
    AVERAGES, RMSEs = save_AVERAGES (iGOP, AVERAGES, RMSEs, kbps_TM, rmse1D)



    #########################
    # MÉTODOS DE ORDENACIÓN #
    #########################

    ########## 6.   BRC Fuerza Bruta #
    #AVERAGES, RMSEs = BRC_BruteForce (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## 7.   Control BR -rate a componente #
    #OneRate_ForComponent (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS)

    ##########      Un slope X por cada punto de la curva RD #
    #OneSlope_ForPoint (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _CAPAS_COMPLETAS)

    ########## 10.  Subbandas Independientes #
    #Sub_Independents (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _CAPAS_COMPLETAS)

    ########## 12.  Una subbanda para todas PtInicial #
    #OneSub_ForAll_PtInicial (kbps_antes, rmse1D_antes, radian_candidato, kbps_candidato, rmse1D_candidato, _CANDIDATO, _CANDIDATO_REDUCES, _CANDIDATO_REDUCES_normalized, emptyLayer, CANDIDATO_KBPS, _CAPAS_COMPLETAS)

    ########## 13.  Una subbanda para todas PtAnterior #
    ##########      Existen 2 sub-OPCIONES (ver código).
    #AVERAGES, RMSEs = OneSub_ForAll_PtAnterior (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## 13a. Una subbanda para todas PtAnterior. Con VM manualmente: VM después de su subbanda #
    ##########      Existe  1 sub-OPCION   (ver código).
    #AVERAGES, RMSEs = OneSub_ForAll_PtAnterior_VMtrasSub (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## 13b. Una subbanda para todas PtAnterior. Sólo hay texturas. Subbandas L y H+MV #
    ##########      Existen 2 sub-OPCIONES (ver código).
    #AVERAGES, RMSEs = OneSub_ForAll_PtAnterior_SoloTexturas (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## 13c. Una subbanda para todas PtAnterior. Ponderación por motion_?_importance #
    ##########      Existen 3 sub-OPCIONES (ver código).
    #AVERAGES, RMSEs = OneSub_ForAll_PtAnterior_motionImportance (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## 13d. Una subbanda para todas PtAnterior. Reducción de Mmax hasta L. Y reducción de Mx proporcionalmente a la primera reducción #
    ##########      Existen 4 sub-OPCIONES (ver código).
    #AVERAGES, RMSEs = OneSub_ForAll_PtAnterior_escalaProporcionalVM (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## 14.  Envio de subbandas por igual [1,1,...], [2,2,...]. Usando slopes según el doble de importancia por subbanda #
    #AVERAGES, RMSEs = sub_por_igual (_CAPAS_COMPLETAS, AVERAGES, RMSEs)


    ########## Punto 2. del PAPER0. For Subbands #
    #AVERAGES, RMSEs = for_Subbands (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## Punto 3. del PAPER0. For Layers #
    #AVERAGES, RMSEs = for_Layers (_CAPAS_COMPLETAS, AVERAGES, RMSEs)

    ########## Punto 4. del PAPER0. Gains Layers #
    #AVERAGES, RMSEs = Gains_Layers (_CAPAS_COMPLETAS, AVERAGES, RMSEs)


########################################
########## RECOGE AVERAGE DE CADA iGOP #
AVERAGES, RMSEs = averages_1toN (AVERAGES, RMSEs)
AVERAGES        = averages_0yN  (AVERAGES)
AVERAGES, RMSEs = averages_file (AVERAGES, RMSEs)



'''
Double_layers
================
    _ENVIOS = [[0,0,0,0,0,0,0],
               [1,0,0,0,0,0,0],
               [2,0,0,0,0,0,0],
               [2,0,0,0,1,0,0],
               [2,1,0,0,1,0,0],
               [3,1,0,0,1,0,0],
               [4,1,0,0,1,0,0],
               [4,2,0,0,1,0,0],
               [4,2,0,0,1,1,0],
               [4,2,1,0,1,1,0],
               [5,2,1,0,1,1,0],
               [6,2,1,0,1,1,0],
               [6,3,1,0,1,1,0],
               [7,3,1,0,1,1,0],
               [8,3,1,0,1,1,0],
               [8,4,1,0,1,1,0],
               [8,4,2,0,1,1,0],
               [8,4,2,0,1,1,1],
               [8,4,2,1,1,1,1],
               [9,4,2,1,1,1,1],
               [10,4,2,1,1,1,1],
               [10,5,2,1,1,1,1],
               [11,5,2,1,1,1,1],
               [12,5,2,1,1,1,1],
               [12,6,2,1,1,1,1],
               [12,6,3,1,1,1,1],
               [13,6,3,1,1,1,1],
               [14,6,3,1,1,1,1],
               [14,7,3,1,1,1,1],
               [15,7,3,1,1,1,1],
               [16,7,3,1,1,1,1],
               [16,8,3,1,1,1,1],
               [16,8,4,1,1,1,1],
               [16,8,4,2,1,1,1],
               [16,9,4,2,1,1,1],
               [16,10,4,2,1,1,1],
               [16,10,5,2,1,1,1],
               [16,11,5,2,1,1,1],
               [16,12,5,2,1,1,1],
               [16,12,6,2,1,1,1],
               [16,12,6,3,1,1,1],
               [16,13,6,3,1,1,1],
               [16,14,6,3,1,1,1],
               [16,14,7,3,1,1,1],
               [16,15,7,3,1,1,1],
               [16,16,7,3,1,1,1],
               [16,16,8,3,1,1,1],
               [16,16,8,4,1,1,1],
               [16,16,9,4,1,1,1],
               [16,16,10,4,1,1,1],
               [16,16,10,5,1,1,1],
               [16,16,11,5,1,1,1],
               [16,16,12,5,1,1,1],
               [16,16,12,6,1,1,1],
               [16,16,13,6,1,1,1],
               [16,16,14,6,1,1,1],
               [16,16,14,7,1,1,1],
               [16,16,15,7,1,1,1],
               [16,16,16,7,1,1,1],
               [16,16,16,8,1,1,1],
               [16,16,16,9,1,1,1],
               [16,16,16,10,1,1,1],
               [16,16,16,11,1,1,1],
               [16,16,16,12,1,1,1],
               [16,16,16,13,1,1,1],
               [16,16,16,14,1,1,1],
               [16,16,16,15,1,1,1],
               [16,16,16,16,1,1,1]]

'''
