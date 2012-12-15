#!/bin/bash

pushd `dirname "$0"` &> /dev/null

DJANGO_SETTINGS_MODULE=src.settings
export DJANGO_SETTINGS_MODULE

# set up our paths
PYTHONPATH=`pwd`/..:`pwd`/../external
export PYTHONPATH

# get ourselves back to the beginning so that the script path isn't relative to src, but relative to where we ran the command
popd &> /dev/null

command=$1
shift # rather than trying to predict the total # of arguments, lop off the command argument and invoke the rest of the arguments
python $command "$@"
