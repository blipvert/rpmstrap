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

# This is just an example of what you could do with a post install
# script. Remember, everything that the suite scripts have access to
# you will have access to in these scripts. This includes every function
# and variable.

# For our example, we will first make the $TARGET environment more
# immediately useful:
cp -f /etc/resolv.conf $TARGET/etc/.
touch $TARGET/etc/fstab
mkdir -p $TARGET/proc
mount -t proc proc $TARGET/proc

# Next, let's get a DHCP client and install it (this is CentOS 4!)
# see http://mark.foster.cc/wiki/index.php/Centos-4_on_Xen
cd $TMP_DIR
wget http://mirror.centos.org/centos/4.1/os/i386/CentOS/RPMS/dhclient-3.0.1-12_EL.centos4.i386.rpm
rpm --install --root $TARGET dhclient-3.0.1-12_EL.centos4.i386.rpm
