#!/bin/sh

# Download base image if needed
if [ ! -e robot-trans.png ]; then
    wget https://github.com/robotframework/robotframework/blob/master/doc/images/robot-trans.png
fi

# Cut base image and save it as PNM and as alpha channel
cut="28 57 180 180"
pngtopnm -mix robot-trans.png | pamcut $cut > robot.pnm
pngtopnm -alpha robot-trans.png | pamcut $cut | ppmtopgm > alpha.pgm

# Create input images (and alpha channels) for icon in different sizes
for size in 16 32 48; do
    pnmscale -xysize $size $size robot.pnm > tmp.pnm
    pnmquant 16 tmp.pnm > $size.pnm  # pnmquant fails to work with stdin
    pnmscale -xysize $size $size alpha.pgm > $size.pgm
done

# Create the icon
ppmtowinicon -andpgms \
    16.pnm 16.pgm \
    32.pnm 32.pgm \
    48.pnm 48.pgm \
    > robot.ico
echo "Created robot.ico"

# Cleanup
rm *.pnm *.pgm
