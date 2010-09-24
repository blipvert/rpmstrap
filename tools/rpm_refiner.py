#! /usr/bin/env python

# rpm-refiner.py
#  Given a pile of RPMs will check dependency closure, will attempt to figure out
# their installation order. This is intended for those times that rpm-solver.py
# fails.
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
# Author: Sam Hart

import rpm_solver
import getopt
import commands
import sys
import tempfile

def get_rpm_name(path, rpm):
    """ Given a filename, get the RPM name """

    cmd = "rpm -qp --qf \"%%{name}\" %s/%s" % (path, rpm)
    return commands.getoutput(cmd)

def process(rpm_dir, recursive, progress, verbose, pdk_output, work_dir):
    """ Main process if ran from command line """

    solver = rpm_solver.rpm_solver(progress, verbose)
    solver.init_db(rpm_dir, None, recursive, work_dir)
    needed, problems = solver.dep_closure()

    if len(needed):
        print "Error! The following packages are needed for dependency closure:\n"
        for pkg in needed:
            print "\t" + str(pkg)

        sys.exit(2)

    if len(problems):
        print "Error! The following problems were encountered:\n"
        for pkg in problems:
            print "\t" + str(pkg)
        sys.exit(2)

    # Okay we do stuff
    if pdk_output:
        ordered = solver.order_solver(0)
    else:
        ordered = solver.order_solver(1)
    ordered.reverse()
    tmp_dir = tempfile.mkdtemp()

    i = 0
    allnames=""
    new_order = []
    tmp_order = []
    while len(ordered):
        name = ordered.pop()
        tmp_order.append(name)
        if verbose:
            print "---------\nTrying %s" % name
        allnames = ""
        for tmp_name in tmp_order:
            fullname = "%s/%s" % (rpm_dir, tmp_name)
            allnames = "%s %s" % (allnames, fullname)

        cmd = "rpm --install --root %s %s" % (tmp_dir, allnames)
        if verbose > 1:
            print cmd
        (status, output) = commands.getstatusoutput(cmd)
        if verbose > 2:
            print status
            print output
        if not status:
            new_order.append(tmp_order)
            tmp_order = []

    if len(tmp_order):
        new_order.append(tmp_order)

    for sub_order in new_order:
        for name in sub_order:
            if pdk_output:
                p_name = get_rpm_name(rpm_dir, name)
                print ("<rpm><name>%s</name><meta><pass>%d</pass></meta></rpm>" % (p_name, i))
            else:
                print ("%d:%s" % (i, name))
        i = i + 1

def usage():
    print "rpm_refiner.py -"
    print "  Given a directory of RPMs, attempt to order their"
    print "installation or determine if they have dependency closure."
    print "This uses rpm_solver.py. Basically, use this when rpm_solver.py"
    print "cannot resolve circular dependencies.\n"
    print "\nUSAGE:"
    print "     rpm_refiner.py [options] <RPM_DIR>"
    print "\nWhere [options] may be one of the following:"
    print "\t-v | --verbose\tBe verbose in processing"
    print "\t-p | --progress\tUse progress bar"
    print "\t-r | --recursive\tScan RPM_DIR recursively"
    print "\t-k | --pdk\t\tProduce PDK ready XML snippits"
    print "\t-w | --work\t\tSupply a work dir (typically chroot) for rpmdb"
    print "\n\n"


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vprkw:", ["verbose", "progress", "recursive", "pdk", "work="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    verbose = 0
    progress = 0
    recursive = 0
    pdk_output = 0
    work_dir = tempfile.mkdtemp()

    if len(sys.argv) < 2:
        usage()
        sys.exit(2)

    rpm_dir = sys.argv[-1]

    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = verbose + 1

        if o in ("-p", "--progress"):
            progress = 1

        if o in ("-r", "--recursive"):
            recursive = 1

        if o in ("-k", "--pdk"):
            pdk_output = 1

        if o in ("-w", "--work"):
            work_dir = a

    if verbose > 1: print "WARNING: Excessive debugging"

    process(rpm_dir,recursive, progress, verbose, pdk_output, work_dir)

if __name__ == "__main__":
    main()

# vim:set ai et sts=4 sw=4 tw=80:
