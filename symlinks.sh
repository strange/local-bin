#!/bin/bash

# A simple script that automatically generates symlinks for the various scripts
# available in this package. The script must be run from the directory in which
# the files we're creating symlinks to reside.

SCRIPT=$(basename $0)

if [ ! -e "$PWD/$SCRIPT" ]
then
    echo "Script must be run from the directory in which the files we're " \
         "creating links to reside."
    exit 1
fi

TARGET_DIR="$HOME/bin"

if [ ! -e $TARGET_DIR ]
then
    mkdir $TARGET_DIR
fi

EXCLUDE=".gitignore .git README.txt $SCRIPT"

for FILE in `ls -A`
do
    if [[ "${EXCLUDE}" != *${FILE}* ]]
    then
        SOURCE="$PWD/$FILE"
        TARGET="$TARGET_DIR/$FILE"
        if [ $# -eq 1 ] && [ $1 = 'remove' ]
        then
            if [ -L $TARGET ]
            then
                rm $TARGET
            fi
        else
            if [ -e $TARGET ]
            then
                echo "A file named $TARGET already exists!"
            else
                ln -s $SOURCE $TARGET
            fi
        fi
    fi
done
