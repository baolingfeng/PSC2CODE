#!/bin/bash

cd code; make; cd ..
echo -n "file name: " # without extension
read name
./code/segment 0.33 500 40000 images/${name}.ppm segments/${name}
