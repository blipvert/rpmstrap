#!/bin/sh

# Copyright 2005 Progeny Linux Systems, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Author: Sam Hart

unset DEBUG LINK FROM_FILE CP_OPTS || true

PROGNAME=${0##*/}
CP_OPTS="-fau"

trace () {
    if [ -n "$DEBUG" ]; then
        echo -e >&2 "$PROGNAME: $*"
    fi
}

die () {
    echo -e >&2 "$PROGNAME: fatal error: $*"
    # Restore STDIN
    if [ -n "$FROM_FILE" ]; then
        exec <&6 6<&-
    fi
    exit 1
}

usage() {
    cat >&2 <<USAGE
Usage: $PROGNAME [options] target_dir
Reads output from rpmdiff.py from STDIN or from a file and creates
a migration distro into "target_dir"

Where options may be one of:

    -v|--verbose        Verbose output
    -h|--help           Display this usage message
    -f|--file           File containing rpmdiff.py output
    -l|--link           Link instead of copy (for speed, careful
                        on NFS mounts and the like)

USAGE
}

TEMP=$(getopt -n "$PROGNAME" --options vhf:l \
--longoptions verbose,\
help,\
file:\
link -- $*)

if [ $? -ne 0 ]; then
    die "Error while parsing options. See '$PROGNAME -h' for usage."
fi

eval set -- "$TEMP"

while :; do
    case "$1" in
        ## Functionality options
        -h|--help)
            usage
            exit
            ;;
        -v|--verbose)
            DEBUG=yes
            shift 1
            ;;
        -f|--file)
            if [ -n "$2" ]; then
                exec 6<&0
                exec < "$2"
                FROM_FILE=$2
                shift 2
            else
                die "Option requires argument: $1"
            fi
            ;;
        -l|--link)
            LINK=yes
            CP_OPTS="-flau"
            shift 1
            ;;
        --)
            shift 1
            ;;
        *)
            break
            ;;
    esac
done

if [ "$1" = "" ]; then
    usage
    die "Usage error, you must supply a target directory"
fi

TARGET_DIR=$1
mkdir -p $TARGET_DIR

while read LINE; do
    trace $LINE

    # Get the fields
    T_TYPE=$(echo $LINE | awk '{print $1}')
    F_FROM=$(echo $LINE | awk '{print $2}')
    F_TO=$(echo $LINE | awk '{print $3}')
    V_FROM=$(echo $LINE | awk '{print $4}')
    V_TO=$(echo $LINE | awk '{print $5}')

    case "$T_TYPE" in
        SAME)
            trace "cp $CP_OPTS $F_FROM $TARGET_DIR/."
            cp $CP_OPTS $F_FROM $TARGET_DIR/.
            ;;
        ADD)
            trace "cp $CP_OPTS $F_TO $TARGET_DIR/."
            cp $CP_OPTS $F_TO $TARGET_DIR/.
            ;;
        UPDATE)
            # Effectively add and update are the same
            # however, keeping them seperate in case
            # this ever changes
            trace "cp $CP_OPTS $F_TO $TARGET_DIR/."
            cp $CP_OPTS $F_TO $TARGET_DIR/.
            ;;
        REMOVE)
            # We do nothing here
            trace "Removing $F_FROM from target (not copying)"
            ;;
        *)
            trace "Problem in line '$LINE' - Unidentified type (could be comment, ignoring)"
            ;;
    esac
done

trace "Done. Restoring STDIN (if necessary)"

# Restore STDIN
if [ -n "$FROM_FILE" ]; then
    exec <&6 6<&-
fi
