#! /usr/bin/env python

# $Progeny$
#
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
# Author : Sam Hart

import os
import fnmatch
import commands
import re
import getopt
import sys
import progress_bar
import rpmdiff_lib

def list_files(root, patterns='*', recurse=1, return_folders=0):
    """List all the files in a directory"""

    # Expand patterns from semicolon-separated string to list
    pattern_list = patterns.split(';')

    class Bunch:
        def __init__(self, **kwds): self.__dict__.update(kwds)
    arg = Bunch(recurse=recurse, pattern_list=pattern_list, return_folders=return_folders, results=[])

    def visit(arg, dirname, files):
        # Append to arg.results all relevant files
        for name in files:
            fullname = os.path.normpath(os.path.join(dirname, name))
            if arg.return_folders or os.path.isfile(fullname):
                for pattern in arg.pattern_list:
                    if fnmatch.fnmatch(name, pattern):
                        arg.results.append(fullname)
                        break
        # Block recursion if disallowed
        if not arg.recurse: files[:]=[]

    os.path.walk(root, visit, arg)

    return arg.results

def grab_rpm_files(directory, recurse=0, binpkg=1, srcpkg=0):
    """Given a directory, pull all the rpms from it"""

    rpm_files = []

    if srcpkg:
        for filename in list_files(directory, '*.srpm;*.src.rpm', recurse):
            rpm_files.append(filename)

    if binpkg:
        for filename in list_files(directory, '*.rpm', recurse):
            rpm_files.append(filename)

    return rpm_files

def run_compare(rpm_from, rpm_to, rpm_from_type, rpm_to_type, recurse, progress, verbose, binpkg, srcpkg, show_same):
    """ Run the comparison """

    col = commands.getoutput("echo \"$COLUMNS\"")
    try:
        columns = int(col)
    except:
        columns = 60
    pb = progress_bar.pb("Progress: ", "-", columns, sys.stderr)

    rdiff = rpmdiff_lib.rpmdiff(verbose, progress, pb)

    rpm_from_dict = {}
    rpm_to_dict = {}
    if rpm_from_type == 'dir':
        if progress: pb.set("Scanning %s :" % rpm_from)
        rpm_from_files = grab_rpm_files(rpm_from, recurse, binpkg, srcpkg)
        rpm_from_dict = rdiff.generate_rpm_dict(rpm_from_files)
        if progress: pb.set("Progress :")
        if progress: pb.clear()
    else:
        print "Error! No other supported types!"
        sys.exit(2)
    if rpm_to_type == 'dir':
        if progress: pb.set("Scanning %s :" % rpm_to)
        rpm_to_files = grab_rpm_files(rpm_to, recurse, binpkg, srcpkg)
        rpm_to_dict = rdiff.generate_rpm_dict(rpm_to_files)
        if progress: pb.set("Progress :")
        if progress: pb.clear()
    else:
        print "Error! No other supported types!"
        sys.exit(2)

    diff_results = rdiff.diff_rpm_dicts(rpm_from_dict, rpm_to_dict)
    if progress: pb.clear()
    print rdiff.produce_data_file(0, show_same)

def usage():
    print "\nrpmdiff - Compares two piles of RPMs."
    print "\nUsage:"
    print "\t\trpmdiff.py [options] <pile_from> <pile_to>\n"
    print "\t-h | --help\t\tThis usage message"
    print "\n\tTOGGLES\n"
    print "\t-p | --progress\t\tDisplay a progress bar"
    print "\t-b | --binary | --binpkg\n\t\t\tScan the binary RPMs in the directory (default)"
    print "\t-nb | --no-binary | --no-binpkg\n\t\t\tDo not scan the binary RPMs in the directory\n"
    print "\t-s | --source | --srcpkg\n\t\t\tScan the source RPMs in the directory"
    print "\t-ns | --no-source | --no-srcpkg\n\t\t\tDo not scan the source RPMs in the directory (default)\n"
    print "\t-r | --recursive\tScan directories recursively"
    print "\t-nr | --no-recursive\tDo not scan directories recursively (default)\n"
    print "\t-a | --same\t\tShow packages that remain the same"
    print "\t-na | --no-same\t\tDo not show packages that remain the same (default)\n"
    print "\n\n"
    print "If run in 'no-pretty' data mode (default), the output will be as follows:\n"
    print "T_TYPE\tPID\tFILE\tFROM\tTO"
    print "\nwhere:"
    print "\tT_TYPE\tThe transaction type (ADD, UPDATE, REMOVE, SAME)"
    print "\tPID\tThe package ID (only applicable in UPDATE and REMOVE)"
    print "\tFILE\tThe associated file (only applicable in ADD and UPDATE)"
    print "\tFROM\tThe version (only applicable in UPDATE and REMOVE)"
    print "\tTO\tTher version of the new package (only applicable in ADD and UPDATE)"
    print "\n\n"

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ahbpsr", ["help", "directory=", "progress", "binary", "no-binary", "source", "no-source", "recurse", "no-recurse", "binpkg", "no-binpkg", "srcpkg", "no-srcpkg", "recursive", "no-recursive", "same", "no-same"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    recurse = 0
    binpkg = 1
    srcpkg = 0
    show_same = 0
    progress = 0
    verbose = 0
    rpm_to = ""
    rpm_from = ""
    rpm_to_type = "dir"
    rpm_from_type = "dir"

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

        # Enable options
        if o in ("-p", "--progress"):
            progress = 1
        if o in ("-b", "--binary", "--binpkg"):
            binpkg = 1
        if o in ("-s", "--source", "--srcpkg"):
            srcpkg = 1
        if o in ("-r", "--recurse", "--recursive"):
            recurse = 1
        if o in ("-a", "--same"):
            show_same = 1

        # Disable options
        if o in ("--no-binary", "--no-binpkg"):
            binpkg = 0
        if o in ("--no-source", "--no-srcpg"):
            srcpkg = 0
        if o in ("--no-recurse", "--no-recursive"):
            recurse = 1
        if o in ("-na", "--no-same"):
            show_same = 0

    try:
        rpm_to = sys.argv[-1]
        rpm_from = sys.argv[-2]
    except:
        usage()
        sys.exit(2)

    run_compare(rpm_from, rpm_to, rpm_from_type, rpm_to_type, recurse, progress, verbose, binpkg, srcpkg, show_same)

if __name__ == "__main__":
    main()

# vim:set ai et sts=4 sw=4 tw=80:
