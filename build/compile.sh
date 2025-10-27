# Script to compile the modified EddyPro source code
# Written by June Skeeter

rootdir=$1

echo $rootdir
    
rm -rf $rootdir$"/bin" $rootdir$"/obj"
cd $rootdir/prj
make rp
make fcc
cp $rootdir$"build/7z/7za" $rootdir$"/bin/"

