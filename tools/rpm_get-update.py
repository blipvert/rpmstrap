#! /usr/bin/env python

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

import os
import fnmatch
import commands
import re
import getopt
import sys
import rpmdiff_lib
import progress_bar

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

def process(rpm_to_dir, rpm_from_dir, mirror, dontcopy, verbose, recurse, progress):

    if verbose: print ">process(..)"

    error_log = []

    col = commands.getoutput("echo \"$COLUMNS\"")
    try:
        columns = int(col)
    except:
        columns = 60
    pb = progress_bar.pb("Progress: ", "-", columns, sys.stderr)

    rpm_from_files = grab_rpm_files(rpm_from_dir, recurse)
    rpm_to_files = grab_rpm_files(rpm_to_dir, recurse)
    rpmdiff_inst = rpmdiff_lib.rpmdiff(verbose, progress, pb)

    rpm_from_dict = rpmdiff_inst.generate_rpm_dict(rpm_from_files)
    rpm_to_dict = rpmdiff_inst.generate_rpm_dict(rpm_to_files)

    i = 0.0
    for rpm in rpm_from_dict.keys():
        i = i + 1.0
        if progress:
            percentage = i / len(rpm_from_dict.keys())
            pb.progress(percentage)

        # check if the update exists
        if not rpm_to_dict.has_key(rpm):
            # First, attempt to grab from mirror
            cmd = ("wget -nd -P \"%s\" \"%s/%s-*.rpm\"") % (rpm_to_dir, mirror, rpm)
            if verbose: print ">> " + cmd
            output = commands.getoutput(cmd)
            if (not len(list_files(rpm_to_dir, ("%s-*.rpm" % rpm), False))):
                if not dontcopy:
                    # Okay, download didn't work, let's just copy the file over and log it
                    cmd = ("cp %s %s/.") % (rpm_from_dict[rpm]['filename'], rpm_to_dir)
                    if verbose: print">> File could not download, default to copy original"
                    output = commands.getoutput(cmd)
                else:
                    if verbose: print">> File could not download"
                error_log.append("Problem with %s for %s arch. Could not find in mirror." % (rpm, arch))

    if len(error_log):
        print >> sys.stderr, "ERRORS\n"
        i = 0
        for line in error_log:
            i += 1
            print "[%d] %s" % (i, line)


def usage():
    print "rpm_get-update.py -"
    print " Given a pile of RPMs for a current platform, and a pile of RPMs for an"
    print "updated platform, will check if the updated platform has all the same package"
    print "names as the original. If not, will attempt to download them from a URL."
    print "Note: URL MUST BE FTP (HTTP WILL NOT WORK)"
    print "\nUSAGE:"
    print "     get-arch.py [options] <RPM_OLD_DIR> <RPM_NEW_DIR> <MIRROR>"
    print "\nWhere [options] may be one of the following:"
    print "\t-r | --recursive\tRecursively import"
    print "\t-v | --verbose\tBe verbose in processing"
    print "\t-p | --progress\tShow progress bar"
    print "\t-d | --dontcopy\tDont copy original on failure (defaults to copying)"

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "rvpd", ["recursive", "verbose", "progress", "dontcopy"])
    except getopt.GetoptError:
       # print help information and exit:
        usage()
        sys.exit(2)

    verbose = 0
    recurse = 0
    progress = 0
    dontcopy = 0

    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = 1
        if o in ("-r", "--recursive"):
            recurse = 1
        if o in ("-p", "--progress"):
            progress = 1
        if o in ("-d", "--dontcopy"):
            dontcopy = 1

    try:
        mirror = sys.argv[-1]
        rpm_to_dir = sys.argv[-2]
        rpm_from_dir = sys.argv[-3]
        if verbose:
            print "Using:"
            print "\t'%s' for RPM_OLD_DIR" % rpm_from_dir
            print "\t'%s' for RPM_NEW_DIR" % rpm_to_dir
            print "\t'%s' for MIRROR" % mirror
    except:
        usage()
        sys.exit(2)

    process(rpm_to_dir, rpm_from_dir, mirror, dontcopy, verbose, recurse, progress)

if __name__ == "__main__":
    main()

# vim:set ai et sts=4 sw=4 tw=80:
