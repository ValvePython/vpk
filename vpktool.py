# Easy VPK extractor
# Use this script to extract vpk's into materials, models, etc.
# Author: Trevor Tomesh (github.com/trevortomesh)

import vpk
import os

inputPath = input('Path to VPK?: ')

try:
	pak1 = vpk.open(inputPath)

except:
	print("Can't find file at path"+inputPath)
	
outputPath = input('Path to output?: ')

for filepath in pak1:

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


