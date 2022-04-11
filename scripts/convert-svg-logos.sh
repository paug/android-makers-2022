# This bash script converts all existing svg logo files into png ones and save them in the 'pngs' folder. 
# It will also copy the existing png of images/logos to the pngs folder for safety.
# It requires rsvg (brew install librsvg).
#
# You should use it from the root folder of the android-makers project like that:
# ./scripts/convert-svg-logos.sh
#


cd images/logos
find . -type f -maxdepth 1 -name "*.png" -exec bash -c 'cp "$0" "pngs/$0"' {} \;
find . -type f -name "*.svg" -exec bash -c 'rsvg-convert -w 1024 "$0" > "pngs/$0".png' {} \;