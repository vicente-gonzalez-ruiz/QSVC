#!/bin/bash



if [ -z $DATA ]; then echo "Hi! \$DATA undefined!"; exit; fi

set -x

data_base=$PWD
# rm -rf tmp/ odd_* even_* high_?_* prediction_even_* motion_residue_?_* motion_? motion_filtered_* motion_residue_? low_?_ low_?.tmp low_? low_0_original low_?? low_?_* high_? high_?.tmp extract/

##############################	##############################
#                            VÍDEO                           #
##############################	##############################
#mobile_352x288x30x420x300.yuv
#coastguard_352x288x30x420x300.yuv
#akiyo_352x288x30x420x300.yuv
#crowd_run_3840x2160x50x420x500.yuv
#ducks_3840x2160x50x420x500.yuv
#oldTownCross_1280x720x50x420x500.yuv
#oldTownCross_3840x2160x50x420x500.yuv
#parkJoy_3840x2160x50x420x500.yuv

NAME=oldTownCross
RES_X=3840
RES_Y=2160
FPS=50
TOTAL_PICTURES=500

NAME=oldTownCross
RES_X=1408
RES_Y=1152
FPS=50
TOTAL_PICTURES=500

NAME=oldTownCross
RES_X=1280
RES_Y=720
FPS=50
TOTAL_PICTURES=500

NAME=null
RES_X=352
RES_Y=288
FPS=30
TOTAL_PICTURES=300

NAME=crowd_run
RES_X=3840
RES_Y=2160
FPS=50
TOTAL_PICTURES=500

NAME=random
RES_X=352
RES_Y=288
FPS=30
TOTAL_PICTURES=300

NAME=oldTownCross
RES_X=1920
RES_Y=1088
FPS=50
TOTAL_PICTURES=500

NAME=null
RES_X=1920
RES_Y=1088
FPS=50
TOTAL_PICTURES=500

NAME=sunflower
RES_X=1280
RES_Y=640
FPS=25
TOTAL_PICTURES=300

NAME=crew
RES_X=704
RES_Y=576
FPS=60
TOTAL_PICTURES=600

NAME=city
RES_X=704
RES_Y=576
FPS=30
TOTAL_PICTURES=300

NAME=akiyo
RES_X=352
RES_Y=288
FPS=30
TOTAL_PICTURES=300

NAME=coastguard
RES_X=352
RES_Y=288
FPS=30
TOTAL_PICTURES=300

NAME=ducks
RES_X=1920
RES_Y=1088
FPS=50
TOTAL_PICTURES=500

NAME=parkrun
RES_X=1280
RES_Y=736
FPS=50
TOTAL_PICTURES=504

NAME=mobile
RES_X=352
RES_Y=288
FPS=30
TOTAL_PICTURES=300

NAME=crowd_run
RES_X=1920
RES_Y=1088
FPS=50
TOTAL_PICTURES=500

##############################	##############################
#      		       PARÁMETROS ENTRADA  		     #
##############################	##############################
GOPs=8               # 8
TRLs=5               # 5
update_factor=0      # 0.25 # Con distinto de cero al enviar no enviar todos los gops comprimidos, la reconstrucción sale regular.
search_range=4
block_size=32        # CIF y 4CIF=32 # 720p=32 # FHD=64
block_overlaping=0   # 0
subpixel_accuracy=0  # 0

# # #
block_size_min=$block_size # Para ir decrementando los tamaños de bloques
all_SRLs=17                # =16+1
discard_SRLs_Tex=0         # <-- DISCARD SRLs TEXTURES. (subpixel_accuracy)
discard_SRLs_Mot=0         # <-- DISCARD SRLs MOTIONS. (Parece que mejor siempre = 0)


#############  #################
#    PARÁMETROS CALCULADOS     #
#############  #################
GOP_size=`echo "2^($TRLs-1)" | bc -l`
PICTURES=`echo "$GOPs*$GOP_size+1" | bc -l`
DURATION=`echo "$PICTURES/$FPS" | bc -l` #segundos

if [[ $PICTURES -gt $TOTAL_PICTURES ]]; then
    echo "Insuficientes frames en el video original ($TOTAL_PICTURES) para --GOPs=$GOPs --TRLs=$TRLs ($PICTURES frames)."
    exit 0
fi

available_SRLs=`echo "l($search_range)+2" | bc -l`
available_SRLs=`echo "$available_SRLs/1" | bc` # Nº de planos de bits totales a resolución nativa
if [[ $discard_SRLs_Tex > $available_SRLs ]]; then
    discard_SRLs_Tex=$available_SRLs # Nº de planos de bits descartados o Nº de resoluciones que se downsamplean
fi

block_size_snr=`echo "($RES_X*$RES_Y*1.5)/1" | bc` # block_size_snr=`echo "($RES_X*$RES_Y*1.5*$GOP_size)/1" | bc`
RES_X_transcode=`echo "$RES_X/(2^$discard_SRLs_Tex)" | bc`
RES_Y_transcode=`echo "$RES_Y/(2^$discard_SRLs_Tex)" | bc`

block_size_transcode=`echo "$block_size/(2^$discard_SRLs_Tex)" | bc`
block_size_min_transcode=`echo "$block_size_min/(2^$discard_SRLs_Tex)" | bc`

block_size_transcode=`echo "$block_size*(2^$discard_SRLs_Mot)" | bc`
block_size_min_transcode=`echo "$block_size_min*(2^$discard_SRLs_Mot)" | bc`

search_range_transcode=`echo "$search_range/(2^$discard_SRLs_Tex)" | bc`
SRLs=5 #`echo "$available_SRLs-$discard_SRLs_Tex" | bc` # Nº de planos de bits que se envian realmente (+ 1, el signo)

VIDEO=$NAME'_'$RES_X'x'$RES_Y'x'$FPS'x420x'$TOTAL_PICTURES
VIDEOdown=$NAME'_'$RES_X_transcode'x'$RES_Y_transcode'x'$FPS'x420x'$TOTAL_PICTURES
INFO=$data_dir'/../info_'$discard_SRLs_Tex'_'$discard_SRLs_Mot'.dat'

#echo "available_SRLs: " $available_SRLs #
#read word ; echo "Pulsa enter para continuar..." #


#############  #################
#          DESCARGA            #
#############  #################
if [[ ! -e $DATA/$VIDEO.yuv ]]; then
    echo "no esta"
else
    echo "si esta"
#    current_dir=$PWD
#    cd $DATA
#    wget http://www.hpca.ual.es/~vruiz/videos/$VIDEO.avi
#    ffmpeg -i $VIDEO.avi $VIDEO.yuv
#    cd $current_dir
fi


##########################
# RESOLUTION SCALABILITY #
##########################
discard_SRLs="0,0,0,0,0,0,0"
#discard_SRLs=1,1,1,1,0,0,0 # reduce Textures
#discard_SRLs=0,0,0,0,1,1,1 # reduce Motion
#discard_SRLs=0,0,0,0,2,2,2 # reduce Motion
#discard_SRLs=1,1,1,1,1,1,1 # reduce Textures y Motion

#######################
# QUALITY SCALABILITY #
#######################
Ncapas_T=16    # 2 4 8 16 32
Ncapas_M=1     # 1

#slope=42000 # 42000 46000

##############
# DIRECTORIO #
##############
data_dir=$data_base/data-${0##*/}.$NAME.$TRLs""trl_$Ncapas_T"_"$slope"_"$GOPs"GOPs__MJ2KbyDistortions"
cd $data_base
rm -rf $data_dir
mkdir $data_dir
ln -s $DATA/${VIDEO}.yuv $data_dir/low_0
cd $data_dir

##############################	##############################
#      		             MAIN        		     #
##############################	##############################

    ############
    # COMPRESS #
    ############
    # Motion con SLOPES manuales    --clayers_motion = 0
    # Motion con SLOPES automáticos --clayers_motion > 0
    #mcj2k compress --update_factor=$update_factor --nLayers=$Ncapas_T --quantization_texture=$slope --GOPs=$GOPs --TRLs=$TRLs --SRLs=$SRLs --block_size=$block_size --block_size_min=$block_size_min --search_range=$search_range --pixels_in_x=$RES_X --pixels_in_y=$RES_Y

    # cp /home/cmaturana/QSVC/research/paper0/gpt/data/crowdrun.5trl_16_42000_8GOPs__transcode_gops/info_snrFrames_GOPs info_snrFrames_GOPs_D
    cp ../info_snrFrames_GOPs_D .

    ###############################################
    # Search slope in MJ2K by distortion in MCJ2K #
    ###############################################
    mcj2k searchSlope_byDistortion_j2k --GOPs=$GOPs --TRLs=$TRLs --SRLs=$SRLs --nLayers=$Ncapas_T --pixels_in_x=$RES_X --pixels_in_y=$RES_Y --distortions=info_snrFrames_GOPs_D


set +x
