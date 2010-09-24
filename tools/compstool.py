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

from elementtree.ElementTree import ElementTree, Element, dump, fromstring
import os
import fnmatch
import commands
import re
import getopt
import sys
#import rpmdiff_lib
import progress_bar

class comps_opt:
    UNDEF = 0
    ERASE = 1
    ADD = 2

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

def get_names_from_dir(directory, recurse, pb, progress):
    """ Given a directory, pull all the rpm package names from the rpms in it """

    rpm_names = []

    rpm_files = grab_rpm_files(directory, recurse)

    i = 0.0
    for file in rpm_files:
        i = i + 1.0
        if progress:
            percentage = i / len(rpm_files)
            pb.progress(percentage)
        cmd = "rpm -qp --qf \"%%{name}\" %s" % file
        rpm_names.append(commands.getoutput(cmd))

    return rpm_names

def process(directory, option, file_out, use_file_out, xml_file, group, verbose, recurse, progress):
    if verbose: print "Inside process..."

    col = commands.getoutput("echo \"$COLUMNS\"")
    try:
        columns = int(col)
    except:
        columns = 60
    pb = progress_bar.pb("Progress: ", "-", columns, sys.stderr)

    tree = ElementTree(file=xml_file)
    elem = tree.getroot()

    if verbose: print "Getting rpm_names"

    rpm_names = get_names_from_dir(directory, recurse, pb, progress)

    if verbose: print "Processing names"

    if option == comps_opt.ERASE:
        """ Handle the ERASE operations """
        for subelem in elem:
            for subsub in subelem:
                p = 0.0
                for subsubsub in subsub:
                    p = p + 1.0
                    if progress:
                        percentage = p / len(subsub)
                        pb.progress(percentage)

                    if subsubsub.tag == 'packagereq' and subsubsub.text in rpm_names:
                        subsub.remove(subsubsub)
                        if verbose: print "Found %s, removing" % subsubsub.text
    elif option == comps_opt.ADD:
        """ Handle the ADD operations """
        text = "<group>\n"
        text += "<id>%s</id>\n" % group
        text += "<name>%s</name>\n" % group
        text += "<packagelist>\n"

        p = 0.0
        for name in rpm_names:
            p = p + 1.0
            if progress:
                percentage = p / len(rpm_names)
                pb.progress(percentage)

            text += "<packagereq type=\"mandatory\">%s</packagereq>\n" % name

        text += "</packagelist>\n"
        text += "</group>\n"
        node = fromstring(text)
        elem.append(node)
    else:
        die("Some unknown error has occured. Neither 'ADD' nor 'ERASE' was specified, somehow")

    if progress: pb.clear()

    if verbose: print "Ending, outputing XML"

    if use_file_out:
        ElementTree(tree).write(file_out)
    else:
        dump(tree)

def usage():
    print "compstool.py -"
    print " Given a comps.xml file, will perform various actions on the comps.xml"
    print "file.\n"
    print "\nUSAGE:"
    print "     compstool.py [options] comps.xml"
    print "\nWhere [options] may be one of the following:"
    print "\t-r | --recursive\tOperate recursively on directories"
    print "\t-v | --verbose\tBe verbose in processing"
    print "\t-p | --progress\tShow progress bar"
    print "\t-d | --dir\tUse <DIR> as source for RPMs (defaults to '.')"
    print "\t-e | --erase\tErase elements from comps.xml"
    print "\t-a | --add\tAdd elements to comps.xml"
    print "\t-f | --file\tOutput to file instead of STDOUT"
    print "\t-g | --group\tAdd the new files too a group (requires '-a')"

def die(text):
    print "%s: %s" % (sys.argv[0], text)
    usage()
    sys.exit(2)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "rvpd:eaf:g:", ["recursive", "verbose", "progress", "dir=", "erase", "add", "file=", "group="])
    except getopt.GetoptError:
        die("Error in options")

    verbose = 0
    recurse = 0
    progress = 0
    directory = "."
    option = comps_opt.UNDEF
    file_out = ""
    use_file_out = 0
    group = ""

    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = 1
        if o in ("-r", "--recursive"):
            recurse = 1
        if o in ("-p", "--progress"):
            progress = 1
        if o in ("-d", "--dir"):
            directory = a
        if o in ("-e", "--erase"):
            if option == comps_opt.UNDEF:
                option = comps_opt.ERASE
            else:
                die("'erase' and 'add' cannot be combined")
        if o in ("-a", "--add"):
            if option == comps_opt.UNDEF:
                option = comps_opt.ADD
            else:
                die("'erase' and 'add' cannot be combined")
        if o in ("-f", "--file"):
            file_out = a
            use_file_out = 1
        if o in ("-g", "--group"):
            group = a

    if len(sys.argv) < 2:
        usage()
        sys.exit(2)

    try:
        xml_file = sys.argv[-1]
        if verbose:
            print "Using:"
            print "xml_file : %s" % xml_file
    except:
        usage()
        sys.exit(2)

    if option == comps_opt.ADD and group == "":
        die("'add' requires a group set")

    process(directory, option, file_out, use_file_out, xml_file, group, verbose, recurse, progress)

if __name__ == "__main__":
    main()

# vim:set ai et sts=4 sw=4 tw=80: