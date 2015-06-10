#!/bin/bash
# nohup srun -N 1 -n 1 -p ibmulticore H265.sh &

NAME=mobile_352x288x30x420x300.yuv
vb=100

while [ $vb -le 3000000 ]; do

    # COMPRESS & INFO #
    ./ffmpeg-git-20150518-64bit-static/ffmpeg -f rawvideo -s 352x288 -pix_fmt yuv420p -i DATA_IN/$NAME -tune psnr -c:v hevc -r 30 -vframes 129 -b:v $vb -psnr -an -y test.mp4 2> info_h265

    # RATE
    linea=`cat info_h265 | grep "x265" | grep "global"`
    linea=${linea##*kb/s:}
    rate=${linea%P*}

    # RMSE
    ./ffmpeg-git-20150518-64bit-static/ffmpeg -i test.mp4 -c:v rawvideo -pix_fmt yuv420p -y out.yuv
    rmse=`snr --file_A=test.mp4 --file_B=out.yuv 2> /dev/null | grep RMSE | cut -f3`

    # 
    echo -e $rate'\t'$rmse'\tvb '$vb >> info_h265.$NAME

    rm out.yuv test.mp4
    let vb=vb+10000

done


