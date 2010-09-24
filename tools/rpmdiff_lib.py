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
#
# rpmdiff library

import commands
import progress_bar
import re

class rpmdiff:
    # CONSTANTS
    NA = 'NA'

    def __init__(self, verbose=0, progress=0, pb=progress_bar.pb):
        self.verbose = verbose
        self.progress = progress
        self.pb = pb
        self._data = []
        self._diff = {}
        self._diff['add'] = {}
        self._diff['update'] = {}
        self._diff['remove'] = {}
        self._diff['same'] = {}
        self._errors = []

    def clear(self):
        self._data = []
        self._diff = {}
        self._diff['add'] = {}
        self._diff['update'] = {}
        self._diff['remove'] = {}
        self._diff['same'] = {}
        self._errors = []


    def process_data(self, data):
        self._data = data
        for line in self._data:
            if not re.match(line[0], '#'):
                command_line = line.split("\t")
                if re.match(command_line[0], 'UPDATE'):
                    self.push_update(command_line)
                elif re.match(command_line[0], 'ADD'):
                    self.push_add(command_line)
                elif re.match(command_line[0], 'REMOVE'):
                    self.push_remove(command_line)
                elif re.match(command_line[0], 'SAME'):
                    self.push_same(command_line)
                else:
                    errormsg = ("Error in line: '" + line + "'", "NO TRANSACTION TYPE")
                    self.push_error(errormsg)

    def produce_data_file(self, human_readable=0, same=1):
        output = ""
        if human_readable:
            output = "human redable not yet ready"
        else:
            if same:
                output += "# Same Packages\n"
                for key in self._diff['same'].keys():
                    output += "SAME\t" + key + "\t" + self._diff['same'][key]['rpm'] + "\t" + self._diff['same'][key]['version'] + "\t" + self._diff['same'][key]['version'] + "\n"

            output += "# Update packages\n"
            for key in self._diff['update'].keys():
                output += "UPDATE\t" + key + "\t" + self._diff['update'][key]['rpm'] + "\t" + self._diff['update'][key]['from'] + "\t" + self._diff['update'][key]['to'] + "\n"

            output += "# Add packages\n"
            for key in self._diff['add'].keys():
                output += "ADD\t" + self.NA + "\t"+ self._diff['add'][key]['rpm'] + "\t" + self._diff['add'][key]['version'] + "\t" + self.NA + "\n"

            output += "# Remove packages\n"
            for key in self._diff['remove'].keys():
                output += "REMOVE\t" + key + "\t" + self.NA + "\t" + self._diff['remove'][key]['version'] + "\t" + self.NA + "\n"

        return output

    def push_error(self, errormsg):
        self.errors.append(errormsg)
        if self.verbose:
            for i in errormsg:
                print >> sys.stderr, i

    def push_update(self, line):
        pkg_id = line[1]
        new_rpm = line[2]
        version_from = line[3]
        version_to = line[4]
        self._diff['update'].setdefault(pkg_id, {})['rpm'] = new_rpm
        self._diff['update'].setdefault(pkg_id, {})['from'] = version_from
        self._diff['update'].setdefault(pkg_id, {})['to'] = version_to
        # Is an update ALWAYS a removal with an add?
        # if so, may want to use the following
        #self.push_remove(line)
        #self.push_add(line)

    def push_add(self, line):
        pkg_rpm = line[2]
        pkg_version = line[4]
        self._diff['add'].setdefault(pkg_rpm, {})['rpm'] = pkg_rpm
        self._diff['add'].setdefault(pkg_rpm, {})['version'] = pkg_version

    def push_remove(self, line):
        pkg_id = line[1]
        pkg_version = line[3]
        self._diff['remove'].setdefault(pkg_id, {})['id'] = pkg_id
        self._diff['remove'].setdefault(pkg_id, {})['version'] = pkg_version

    def push_same(self, line):
        pkg_id = line[1]
        pkg_rpm = line[2]
        pkg_version = line[3]
        self._diff['same'].setdefault(pkg_id, {})['id'] = pkg_id
        self._diff['same'].setdefault(pkg_id, {})['rpm'] = pkg_rpm
        self._diff['same'].setdefault(pkg_id, {})['version'] = pkg_version

    def get_adds(self):
        return self._diff['add']

    def get_removes(self):
        return self._diff['remove']

    def get_updates(self):
        return self._diff['update']

    def get_same(self):
        return self._diff['same']

    def get_errors(self):
        return self._errors

    def generate_rpm_dict(self, rpm_files):
        """Given a directory, generate a dict of the rpms"""

        rpm_dict = {}
        i = 0.0
        for filename in rpm_files:
            i = i + 1.0
            if self.progress:
                percentage = i / len(rpm_files)
                self.pb.progress(percentage)
            # Grab the revision information
            # XXX: Should we query for other information?
            # Would anything else be useful?
            cmd = "rpm -qp --qf \"%%{name} %%{version} %%{release} %%{arch}\" %s" % filename
            output = commands.getoutput(cmd)
            version_info = output.split(' ')
            pkg_canonical_name = version_info[0]
            pkg_version = version_info[1]
            pkg_release = version_info[2]
            pkg_arch = version_info[3]

            rpm_dict.setdefault(pkg_canonical_name, {})['version'] = pkg_version
            rpm_dict.setdefault(pkg_canonical_name, {})['release'] = pkg_release
            rpm_dict.setdefault(pkg_canonical_name, {})['file'] = filename
            rpm_dict.setdefault(pkg_canonical_name, {})['id'] = filename
            rpm_dict.setdefault(pkg_canonical_name, {})['type'] = self.NA
            rpm_dict.setdefault(pkg_canonical_name, {})['arch'] = pkg_arch

        if self.progress: self.pb.clear()

        return rpm_dict

    def diff_rpm_dicts(self, rpm_dict_from, rpm_dict_to):
        """ Given two rpm dicts, calculate the migrate path
        from one to the other """

        self.clear()

        diff_results = {}
        diff_results['same'] = []
        diff_results['add'] = []
        diff_results['update'] = []
        diff_results['remove'] = []

        # Compare the two
        i = 0.0
        for key in rpm_dict_to:
            i = i + 1.0
            if self.progress:
                percentage = i / len(rpm_dict_to)
                self.pb.progress(percentage)
            if rpm_dict_from.has_key(key):
                # We have a match, compare version info
                if re.match(str(rpm_dict_from[key]['arch']), str(rpm_dict_to[key]['arch'])) and re.match(str(rpm_dict_from[key]['version']), str(rpm_dict_to[key]['version'])) and re.match(str(rpm_dict_from[key]['release']), str(rpm_dict_to[key]['release'])):
                    # Good enough for me, we have a match
                    version = rpm_dict_from[key]['version'] + "-" + rpm_dict_from[key]['release']
                    line = ('SAME', rpm_dict_from[key]['id'], rpm_dict_to[key]['file'], version, self.NA)
                    self.push_same(line)
                    diff_results['same'].append(key)
                else:
                    version_from = rpm_dict_from[key]['version'] + "-" + rpm_dict_from[key]['release']
                    version_to = rpm_dict_to[key]['version'] + "-" + rpm_dict_to[key]['release']
                    line = ('UPDATE', rpm_dict_from[key]['id'], rpm_dict_to[key]['file'], version_from, version_to)
                    self.push_update(line)
                    diff_results['update'].append(key)
            else:
                # We have a pure add
                version_to = rpm_dict_to[key]['version'] + "-" + rpm_dict_to[key]['release']
                line = ('ADD', self.NA, rpm_dict_to[key]['file'], self.NA, version_to)
                diff_results['add'].append(key)

        # Now check for packages to remove
        # XXX : I am uncertain if creating an index and deleting the
        # elements we find would be more efficient than doing this
        # but since this is largely for me, I'm not sure I care - Sam
        i = 0.0
        for key in rpm_dict_from:
            i = i + 1.0
            if self.progress:
                percentage = i / len(rpm_dict_from)
                self.pb.progress(percentage)
            if not rpm_dict_to.has_key(key):
                # The package is no longer in the build
                version_from = rpm_dict_from[key]['version'] + "-"  + rpm_dict_from[key]['release']
                line = ('REMOVE', rpm_dict_from[key]['id'], self.NA, version_from, self.NA)
                self.push_remove(line)
                diff_results['remove'].append(key)

        if self.progress: self.pb.clear()

        return diff_results

# vim:set ai et sts=4 sw=4 tw=80: