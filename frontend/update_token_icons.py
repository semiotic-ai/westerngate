import csv

from os import listdir
from os.path import isfile, join
tokens = [f.split('.')[0] for f in listdir("assets/icons") if isfile(join("assets/icons", f))]
print(tokens, sep=",")