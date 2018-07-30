import os
import glob

files = glob.glob(r"C:\Users\wangy\Desktop\stitchem")
for f in files:
    os.remove(f)