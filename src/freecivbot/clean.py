import glob
import os

def clean_file(fname):
    fcopy = open(fname+".tmp", "w")
    forg = open(fname, "r")
    for line in forg:
        test_empty = line.replace("\t","").replace(" ","")
        if test_empty == "":
            print >> fcopy
            continue
        new_line = line.rstrip()
        if "" in line:
            new_line = new_line.replace("","")
        if " if " in new_line and new_line[-1]==":":
            if new_line.split(" if ")[1].lstrip()[0] == "(":
                new_line = new_line.replace("(","",1)
                pos = new_line.rindex(")")
                new_line = new_line[:pos] + new_line[pos+1:]
        print >> fcopy, new_line
    fin_str = "mv "+ fname + ".tmp " + fname
    os.system(fin_str)

for item in glob.glob("*"):
    if item[-3:] == ".py":
        clean_file(item)
    elif not "." in item:
        next_dir = item + os.sep
        for item2 in glob.glob(next_dir +"*.py"):
            clean_file(item2)
