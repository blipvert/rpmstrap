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

# This program is insanely hackish, but I really don't have the time
# to figure out how to do it properly. Use at your own risk.

import ftplib
import sys
import urlparse

def parse_names(namelist):
    donelist = []

    # Get ready for some magic foo that will
    # probably be bug ridden and horrible
    # Kill this part. Fix it. PLEASE
    # FIXME
    for a in namelist:
        b = ''.join(a.split('.')[0:-(len(a.split('.'))-1)])
        donelist.append(b.split('-')[0:-1])
    return donelist

def process(details, url):
    (host, path) = urlparse.urlparse(url)[1:3]

    ftp = ftplib.FTP(host)
    text = ftp.login()
    text = ftp.cwd(path)
    ftp_population = ftp.nlst()

    ftp_population_names = parse_names(ftp_population)

    for a in details:
        (passnum, rpm) = a.strip().split(':')
        # First, check if rpm is in ftp as is
        if rpm in ftp_population:
            print "%s:%s" % (passnum, rpm)
        else:
            b = ''.join(rpm.split('.')[0:-(len(a.split('.'))-1)])
            file_data = b.split('-')[0:-1]
            #file_data = parse_names([rpm])
            #print file_data
            if file_data in ftp_population_names:
                # ERE I AM, JH
                # Ok, so how do we get back at the full package name in ftp_population?
                print "%s:%s" % (passnum, ftp_population[ftp_population_names.index(file_data)])
            else:
                print "%s:%s XXX THIS LINE HAS PROBLEMS" % (passnum, rpm)

    #print ftp_population_names[2]

def usage():
    print "\nsuite_upgrader - Attempts to provide an upgrade for a suite script"
    print "\nUsage:"
    print "\t\trpmstrap --suite-details suite | suite_upgrader.py ftp://URL/PATH"
    print "\n\n"

def main():
    try:
        url = sys.argv[-1]
    except:
        usage()
        sys.exit(2)

    suite_details = sys.stdin.readlines()

    process(suite_details, url)

if __name__ == "__main__":
    main()
