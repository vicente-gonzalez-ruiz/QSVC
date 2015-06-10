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
import math
import subprocess as sub
from GOP import GOP
from subprocess import check_call
from subprocess import CalledProcessError
from MCTF_parser import MCTF_parser

HIGH = "high_"
LOW = "low_"
COMPONENTS = 4

discard_TRLs=0
discard_SRLs_Tex=0
discard_SRLs_Mot=0
new_slope = 45000
GOPs = 1
TRLs = 3
SRLs = 5
FPS = 30
BRC = 99999999

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
parser.add_argument("--BRC",
                    help="bit-rate control (kbps). (Default = {})".format(BRC))

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
if args.BRC:
    BRC = int(args.BRC)


#check_call("echo List_Clayers: " + str(List_Clayers) + " " +  str(TRLs), shell=True) #  + " >> output" !!!
#raw_input("Press ENTER to continue ...") # !







#############  ##############################  #################
#                         FUNCTIONS                            #
#############  ##############################  #################

#############  #################
#          kakadu              #
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
#         transcode            #
#############  #################

def transcode (pictures):

    #raw_input("pictures en el transcode: " + str(pictures)) # !
    #raw_input("_COMBINATION en el transcode: " + str(_COMBINATION)) # !

    check_call("rm -rf " + str(path_extract) + "; mkdir " + str(path_extract), shell=True)

    #############  MOTIONS  #############

    if discard_SRLs_Mot != 0 :
        check_call("mkdir " + str(path_extract) + "/mjc_reduced", shell=True)
        fields = pictures / 2
        subband = 1
        while subband < TRLs :

            #check_call("echo \"MOTION: " + str(_COMBINATION) + "   SUB:" + str(subband) + "   Clayer:" + str(_COMBINATION[((TRLs*2)-1)-subband]) + "\"", shell=True)
            #raw_input(" STOP ") # !

            if _COMBINATION[((TRLs*2)-1)-subband] != 0 :
                image_number = 0
                while image_number < fields * COMPONENTS :
                    filename = "/motion_residue_" + str(subband) + "_" + str('%04d' % image_number)
                    check_call("trace kdu_transcode Clayers=" + str(_COMBINATION[((TRLs*2)-1)-subband])
                               + " -i " + str(path_base) + filename + ".mjc"
                               + " -o " + str(path_extract) + "/mjc_reduced" + filename + ".mjc.j2c"
                               + " -reduce " + str(discard_SRLs_Mot), # Multiplicar *2^discard_levels para sacar el nuevo tamaño de bloque, para la llamada del expand.
                               shell=True)

                    image_number += 1
            subband += 1
            fields /= 2

        #check_call("ls -l " + str(path_extract) + "/mjc_reduced", shell=True)
        #raw_input(" STOP ") # !

        # Cambia j2c por mjc. fuzzy kdu_transcode
        for path, dirs, files in os.walk(str(path_extract) + "/mjc_reduced"):
            for fil in files:
                check_call("mv " + str(path_extract) + "/mjc_reduced/" + str(fil) + " " + str(path_extract) + "/" + str(fil[:-4]), shell=True)

        check_call("rm -rf " + str(path_extract) + "/mjc_reduced", shell=True) # fuzzy Python

    else :
        iteracion = 0
        for j in _COMBINATION[M_max:] :
            iteracion += 1
            if j != 0 :
                check_call("cp " + str(path_base) + "/motion_residue_" + str(TRLs - iteracion) + "_*.mjc " + str(path_extract), shell=True) # Motion

    #check_call("echo \"STOP \"", shell=True)
    #raw_input(" STOP ") # !

    #############  TEXTURES  #############

    # Procesa las subbandas de ALTA frecuencia.
    subband = 1
    while subband < TRLs:

        pictures = (pictures + 1) / 2 # !

        if _COMBINATION[TRLs-subband] != 0: #

            # Open the file with the size of each color image.
            file_sizes = open ("extract/" + HIGH + str(subband) + ".j2c", 'w')
            total = 0
            
            image_number = 0
            while image_number < (pictures - 1):
                str_image_number = '%04d' % image_number
                
                # Y
                filename = HIGH + str(subband) + "_Y_" + str_image_number 
                kdu_transcode (filename + ".j2c", _COMBINATION[TRLs-subband], discard_SRLs_Tex)
                Ysize = os.path.getsize("extract/" + filename + ".j2c") # Recompute file-size
                
                # U
                filename = HIGH + str(subband) + "_U_" + str_image_number 
                kdu_transcode (filename + ".j2c", _COMBINATION[TRLs-subband], discard_SRLs_Tex)
                Usize = os.path.getsize("extract/" + filename + ".j2c")
                
                # V
                filename = HIGH + str(subband) + "_V_" + str_image_number
                kdu_transcode (filename + ".j2c", _COMBINATION[TRLs-subband], discard_SRLs_Tex)
                Vsize = os.path.getsize("extract/" + filename + ".j2c")
                
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

    # Procesa la subbanda de BAJA frecuencia.

    if _COMBINATION[0] != 0: #

        # Open the file with the size of each color image.
        file_sizes = open ("extract/" + LOW + str(subband) + ".j2c", 'w')
        total = 0

        image_number = 0
        while image_number < pictures:
        
            str_image_number = '%04d' % image_number
        
            # Y
            filename = LOW + str(subband) + "_Y_" + str_image_number
            kdu_transcode (filename + ".j2c", _COMBINATION[0], discard_SRLs_Tex)
            Ysize = os.path.getsize("extract/" + filename + ".j2c")
        
            # U
            filename = LOW + str(subband) + "_U_" + str_image_number
            kdu_transcode (filename + ".j2c", _COMBINATION[0], discard_SRLs_Tex)
            Usize = os.path.getsize("extract/" + filename + ".j2c")
        
            # V
            filename = LOW + str(subband) + "_V_" + str_image_number
            kdu_transcode (filename + ".j2c", _COMBINATION[0], discard_SRLs_Tex)
            Vsize = os.path.getsize("extract/" + filename + ".j2c")
        
            # Total file-sizes
            size = Ysize + Usize + Vsize
            total += size
            file_sizes.write(str(total) + "\n")

            #check_call("echo TRLs: " + str(TRLs) + " subband: " + str(subband) + " List_Clayers[TRLs-subband]: " + str(List_Clayers[TRLs-subband]), shell=True) #  + " >> output" !!!
            #raw_input("Press ENTER to continue ...") # !

            image_number += 1
        
        file_sizes.close()



#############  #################
#           SIZE               #
#############  #################

def get_size (the_path, suffix):

    path_size = 0
    for path, dirs, files in os.walk(the_path):
        for fil in files:
            if fil.endswith(suffix) :
                filename = os.path.join(path, fil)
                path_size += os.path.getsize(filename)
        return path_size

    

#############  #################
#            LBA               #
#############  #################

def lba (kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO): # looking the best angle

    #raw_input("_COMBINATION en lba: " + str(_COMBINATION)) # !
    #raw_input("ANTES TRANSCODE") # !

    # EXTRACT
    transcode (pictures)
    check_call("cp " + str(path_base) + "/*type* " + str(path_extract), shell=True) # Types

    # INFO
    bytes_mjc = get_size(path_extract, ".mjc") # mcsj2k info --GOPs=$GOPs --TRLs=$TRLs
    bytes_j2c = get_size(path_extract, ".j2c")
    bytes_mj2k = get_size(path_extract, "")

    if bytes_mjc != 0 :
        kbps_mjc = bytes_mjc * 8.0 / duration / 1000
    else:
        kbps_mjc = 0
    if bytes_j2c != 0 :
        kbps_j2c = bytes_j2c * 8.0 / duration / 1000
    else:
        kbps_j2c = 0
    kbps = bytes_mj2k * 8.0 / duration / 1000


    # ENVIO
    check_call("rm -rf " + str(path_tmp) + "; mkdir " + str(path_tmp) + 
               "; echo \"ENVIO: \"; ls " + str(path_extract) +
               "; cp " + str(path_extract) + "/* " + str(path_tmp), shell=True)


    #raw_input("ANTES EXPAND") # !

    # EXPAND
    os.chdir(path_tmp)

    #1088p
    #check_call("mcj2k expand --GOPs=" + str(GOPs) + " --TRLs=" + str(TRLs) + " --SRLs=" + str(SRLs) + " --block_size=64 --block_size_min=64 --search_range=4 --pixels_in_x=1920 --pixels_in_y=1088 --subpixel_accuracy=" + str(discard_SRLs_Tex), shell=True)
    #check_call("mcj2k expand --GOPs=" + str(GOPs) + " --TRLs=" + str(TRLs) + " --SRLs=" + str(SRLs) + " --block_size=32 --block_size_min=32 --search_range=2 --pixels_in_x=1920 --pixels_in_y=1088 --subpixel_accuracy=" + str(discard_SRLs_Tex), shell=True)

    #CIF
    check_call("mcj2k expand --GOPs=" + str(GOPs) + " --TRLs=" + str(TRLs) + " --SRLs=" + str(SRLs) + " --block_size=16 --block_size_min=16 --search_range=4 --pixels_in_x=352 --pixels_in_y=288 --subpixel_accuracy=" + str(discard_SRLs_Tex), shell=True)
    #check_call("mcj2k expand --GOPs=" + str(GOPs) + " --TRLs=" + str(TRLs) + " --SRLs=" + str(SRLs) + " --block_size=32 --block_size_min=32 --search_range=2 --pixels_in_x=352 --pixels_in_y=288 --subpixel_accuracy=" + str(discard_SRLs_Tex), shell=True)


    #if hubo_cambio_res :
        #check_call("DownConvertStatic $RES_X_transcode $RES_Y_transcode low_0 $RES_X $RES_Y low_0_UP", shell=True)

    #raw_input("ANTES SNR") # !

    p = sub.Popen("snr --file_A=low_0 --file_B=../low_0 2> /dev/null | grep RMSE | cut -f 3", 
                  shell=True,
                  stdout=sub.PIPE,
                  stderr=sub.PIPE)
    out, err = p.communicate()
    #errcode = p.returncode
    rmse1D = float(out)

    #rmse2D=`snr2D --block_size=$block_size_snr --dim_X=$RES_X --dim_Y=$RES_Y --file_A=$DATA/$VIDEO.yuv --file_B=$data_dir/tmp/low_0_UP --FFT 2>  /dev/null | grep RMSE | cut -f 3` # FFT en 3D
    #rmse3D=`snr3D --block_size=$block_size_snr --dim_X=$RES_X --dim_Y=$RES_Y --dim_Z=5 --file_A=$DATA/$VIDEO.yuv --file_B=$data_dir/tmp/low_0_UP --FFT 2> /dev/null | grep RMSE | cut -f 3` # FFT en 3D

    os.chdir(path_base)


    # RADIAN

    radian = "" # fuzzy Python

    if _COMBINATION == _CEROS :
        rmse1D_antes = rmse1D
        kbps_antes = kbps
    else :
        if rmse1D_antes >= rmse1D :
            radian = math.atan ( abs(rmse1D_antes - rmse1D) / (kbps - kbps_antes) )
            if radian > radian_antes :
                kbps_candidato = kbps
                rmse1D_candidato = rmse1D
                radian_antes = radian
                _CANDIDATO = _COMBINATION[:]
        else :
            check_call("echo \"" + str(_COMBINATION) + "\t\t" + str(kbps_mjc) + "\t" + str(kbps_j2c) + "\t" + str(kbps) + "\t" + str(rmse1D) + "\t:: No rectángulo \" >> " + str(INFO) + "_detalle", shell=True)
            return kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO

    check_call("echo \"" + str(_COMBINATION) + "\t\t" + str(kbps_mjc) + "\t" + str(kbps_j2c) + "\t" + str(kbps) + "\t" + str(rmse1D) + "\t:: " + str(radian) + "\" >> " + str(INFO) + "_detalle", shell=True)
    return kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO
    #raw_input("Finis cuantum") # !



#############  ##############################  #################
#                        MAIN - BRC                            #
#############  ##############################  #################

# RUTAS
p = sub.Popen("echo $PWD", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
out, err = p.communicate()
path_base = out[:-1]
path_extract = path_base + "/extract"
path_tmp = path_base + "/tmp"

# Inicialization.
gop=GOP()
GOP_size = gop.get_size(TRLs)
pictures = GOPs * GOP_size + 1
fields = pictures / 2
duration = pictures / (FPS * 1.0)

# Variables
INFO = str(path_base) + "/info_" + str(TRLs) + "TRLs_" + str(BRC) + "BRC"
H_max = 1
M_max = TRLs
Ncapas_T = 8
Ncapas_M = 1
max_iteraciones = (TRLs * Ncapas_T) + ((TRLs-1) * Ncapas_M)

# Parámetros de función
kbps_antes = 0
rmse1D_antes = 0
radian_antes = 0
kbps_candidato = 0
rmse1D_candidato = 0

# Inicializa capas
N_subbandas = (TRLs*2)-1
_CEROS = [0] * N_subbandas
_CAPAS = [0] * N_subbandas
_COMBINATION = [0] * N_subbandas
_CANDIDATO = [0] * N_subbandas

##########
# MANUAL #
##########
'''
'''
radian_antes = -99
rmse1D_antes = -1


_COMBINATION = [8, 8, 8, 8, 8, 1, 1, 1, 1]
kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO = lba(kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO) # (0 ... 0)



exit (0)
#raw_input("")

##############
# AUTOMÁTICO #
##############

# Inicializa infos
check_call("rm -f " + str(INFO) + " " + str(INFO) + "_detalle", shell=True)


kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO = lba(kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO) # (0 ... 0)

while (_CANDIDATO[M_max-1] < Ncapas_T) and (kbps_candidato < BRC) : # H_min < Ncapas_T
    max_iteraciones -= 1
    if max_iteraciones < 0 :
        check_call("echo \"Evaluaciones completadas. Existen capas que no se han llegado a usar, porque no es provechoso hacerlo." + "\" >> " + str(INFO) + "_detalle", shell=True)
        exit (0)

    radian_antes = -99

    _CAPAS = _CANDIDATO[:] # actualiza _CAPAS
    #raw_input("actualiza _CAPAS: " + str(_CAPAS)) # !
    check_call("echo \"-> " + str(_CAPAS) + "\" >> " + str(INFO) + "_detalle; echo >> " + str(INFO) + "_detalle", shell=True)
    #check_call("echo \"kbps_antes:" + str(kbps_antes) + "  rmse1D_antes:" + str(rmse1D_antes) + " \" >> " + str(INFO) + "_detalle", shell=True)

    for z in range (0, len(_CAPAS)) : # recorre cada subbanda
        _COMBINATION = _CAPAS[:] # inicializa _COMBINATION
        #raw_input("inicializa _COMBINATION: " + str(_COMBINATION) + "con CAPAS: " + str(_CAPAS)) # !

        if (z < M_max) and (_CAPAS[z] < Ncapas_T) : # T available
            _COMBINATION[z] = _COMBINATION[z] + 1
            kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO = lba(kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO)

        if (z >= M_max) and (_CAPAS[z] < Ncapas_M) : # M available
            _COMBINATION[z] = _COMBINATION[z] + 1
            kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO = lba(kbps_antes, rmse1D_antes, radian_antes, kbps_candidato, rmse1D_candidato, _CANDIDATO)

    kbps_antes = kbps_candidato
    rmse1D_antes = rmse1D_candidato
    
    check_call("echo \"" + str(_CANDIDATO) + "\t\t" + str(kbps_candidato) + "\t" + str(rmse1D_candidato) + "\t:: " + str(radian_antes) + "\" >> " + str(INFO), shell=True)


# cd /home/cmaturana/scratch/data-MCSJ2K-subbanYcapas_TM-compress-expand.sh; mcj2k transcode --BRC=500 --TRLs=3 --GOPs=1
