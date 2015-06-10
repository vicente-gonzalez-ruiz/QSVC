#!/bin/bash
 
set -x
 
# Set the directory to store the images
IMAGES_DIRECTORY=images
 
if [ ! -d "${IMAGES_DIRECTORY}" ]; then
  echo "Creando nuevo directorio: ${IMAGES_DIRECTORY}"
  mkdir -p ${IMAGES_DIRECTORY}
fi
 
# Set the source
URL=http://helioviewer.nascom.nasa.gov/jp2/AIA/2015/06/01/131/

# Get the list of images
lns=$(curl -s ${URL} | sed 's/.*href="\([^"]*\)".*/\1/' | grep ".jp2" | tail -n +4)
total=$(echo ${lns} | wc -w)
total=129
n=1
 
# Convert the list into an array
arr=($lns)
 
# Download the images
for (( i=1; i<=total; i++ ))
do
  echo "Downloading $i/$total..."
  wget ${URL}${arr[((i-1))]}
  num=`printf "%04d" $i`
  mv ${arr[((i-1))]} ${IMAGES_DIRECTORY}/$num.jp2
  
  # JP2 to YUV
  convert ${IMAGES_DIRECTORY}/$num.jp2 ${IMAGES_DIRECTORY}/$num.yuv
  cat ${IMAGES_DIRECTORY}/$num.yuv >> ${IMAGES_DIRECTORY}/sun.yuv

done

