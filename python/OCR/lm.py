import os
import json
import numpy as np
import sys
sys.path.append('..')
from setting import *

with open(os.path.join(code_dir, "OCR", "java-lines.json")) as fin:
    JAVA_LINE_STRUCTURE = json.load(fin)

with open(os.path.join(code_dir, "OCR", "java-words.json")) as fin:
    JAVA_WORDS = json.load(fin)

with open(os.path.join(code_dir, "OCR", "words")) as fin:
    DICT_WORDS = set([line.strip().lower() for line in fin.readlines()])


LINE_MEAN = np.mean([JAVA_LINE_STRUCTURE[k] for k in JAVA_LINE_STRUCTURE])
WORD_MEAN = np.mean([JAVA_WORDS[k] for k in JAVA_WORDS])
LINE_MEDIAN = np.median([JAVA_LINE_STRUCTURE[k] for k in JAVA_LINE_STRUCTURE])
WORD_MEDIAN = np.median([JAVA_WORDS[k] for k in JAVA_WORDS])

LINE_MEAN_2 = np.mean([JAVA_LINE_STRUCTURE[k] for k in JAVA_LINE_STRUCTURE if JAVA_LINE_STRUCTURE[k] > 5])
WORD_MEAN_2 = np.mean([JAVA_WORDS[k] for k in JAVA_WORDS if JAVA_WORDS[k] > 5])
LINE_MEDIAN_2 = np.median([JAVA_LINE_STRUCTURE[k] for k in JAVA_LINE_STRUCTURE if JAVA_LINE_STRUCTURE[k] > 5])
WORD_MEDIAN_2 = np.median([JAVA_WORDS[k] for k in JAVA_WORDS if JAVA_WORDS[k] > 5])

def main():
    print LINE_MEAN, WORD_MEAN, LINE_MEDIAN, WORD_MEDIAN
    print LINE_MEAN_2, WORD_MEAN_2, LINE_MEDIAN_2, WORD_MEDIAN_2

if __name__ == '__main__':
    main()