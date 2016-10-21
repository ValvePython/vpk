# Easy VPK extractor
# Use this script to extract vpk's into materials, models, etc.
# Author: Trevor Tomesh (github.com/trevortomesh)

# usage: python3 vpktool.py [optional_args] [input path] [output path] 

import vpk
import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('inputPath')
parser.add_argument('outPath')
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")


args = parser.parse_args()
inputPath = args.inputPath
outputPath = args.outPath

try:
	pak1 = vpk.open(inputPath)

except:
	print("Can't find file at path: "+inputPath)
	sys.exit(0)
	

for filepath in pak1:

    if args.verbose:	
    	print("extracting: " + filepath)
    
    pakfile = pak1.get_file(filepath)
    pakfile = pak1[filepath]
    
    newFile = outputPath+filepath

    dirn = os.path.dirname(newFile)

    if not os.path.exists(dirn):
    	os.makedirs(dirn)

    fo = open(newFile,"w+")
    pakfile.save(newFile)
    fo.close()


