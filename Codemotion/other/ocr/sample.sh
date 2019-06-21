#!/bin/bash

echo "file name: $1" # without extension
for ((i = 0; i < $2; i++))
do
echo $1_segment$i.ppm
tesseract $1_segment$i.ppm text/$1_segment${i}_ws config.txt
done
