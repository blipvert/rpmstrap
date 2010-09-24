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
# Author: Sam Hart
# Very basic progress bar

import sys

class pb:
    def __init__(self, prefix="Progress :", prog_char="-", col=60, outnode=sys.stdout):
        self.f = outnode
        self.prog_char = prog_char
        self.col = col
        self.spinner = ["|", "/", "-", "\\"]
        self.spin_count = 0
        self.prefix = prefix

    def set(self, prefix="Progress :"):
        self.prefix = prefix

    def clear(self):
        self.f.write("\r")
        for i in range(0, self.col):
            self.f.write(" ")

        self.f.write("\r")
        self.f.flush()

    def progress(self, percentage):
        """Count must be out of 100%"""

        if percentage > 1.0:
            percentage = 1.0

        self.f.write(("\r%s 0 |") % self.prefix)
        width = self.col - len(("\r%s 0  100    |") % self.prefix) + 1
        count = width * percentage

        i = 1
        while i < count:
            self.f.write(self.prog_char)
            i = i + 1

        if count < width:
            self.f.write(">")
            while i < width:
                self.f.write(" ")
                i = i + 1

        if self.spin_count >= len(self.spinner):
            self.spin_count = 0

        self.f.write(self.spinner[self.spin_count])
        self.spin_count = self.spin_count + 1

        self.f.write(" 100 ")
        self.f.flush()

# vim:set ai et sts=4 sw=4 tw=80: