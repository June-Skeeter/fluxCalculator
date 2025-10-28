# Script to compile the modified EddyPro source code
# Written by June Skeeter

# !/bin/bash
rootdir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd )

if [ $# -gt 0 ]; then
    if [ $1 = "build" ]; then
        rm -rf $rootdir$"/bin/linux" $rootdir$"/obj"
        cd $rootdir/prj
        make rp
        make fcc
        cp $rootdir$"/build/7z/7za" $rootdir$"/bin/"
    fi
    # if [[ $1 = "run" || $2 = "run" ]]; then
    #     echo "Running test script"
    #     # cd $rootdir$"/eddypro-engine"

    #     # $rootdir$"/eddypro-engine/bin/linux/eddypro_rp" -s linux $rootdir$"/custom/BinTest_linux.eddypro"

    #     # $rootdir$"/eddypro-engine/bin/linux/eddypro_rp" -s linux $rootdir$"/custom/SCL_mod_mini.eddypro"

    #     # $rootdir$"/eddypro-engine/bin/linux/eddypro_rp" -s linux $rootdir$"/custom/SCL_ecf32.eddypro"
    # fi
fi
