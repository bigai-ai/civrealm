# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import glob
import os


def clean_file(fname):
    fcopy = open(fname+".tmp", "w")
    forg = open(fname, "r")
    for line in forg:
        test_empty = line.replace("\t", "").replace(" ", "")
        if test_empty == "":
            print >> fcopy
            continue
        new_line = line.rstrip()
        if "" in line:
            new_line = new_line.replace("", "")
        if " if " in new_line and new_line[-1] == ":":
            if new_line.split(" if ")[1].lstrip()[0] == "(":
                new_line = new_line.replace("(", "", 1)
                pos = new_line.rindex(")")
                new_line = new_line[:pos] + new_line[pos+1:]
        print >> fcopy, new_line
    fin_str = "mv " + fname + ".tmp " + fname
    os.system(fin_str)


for item in glob.glob("*"):
    if item[-3:] == ".py":
        clean_file(item)
    elif not "." in item:
        next_dir = item + os.sep
        for item2 in glob.glob(next_dir + "*.py"):
            clean_file(item2)
