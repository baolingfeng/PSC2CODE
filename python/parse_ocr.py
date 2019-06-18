import json
import os
import string
import distance
import Levenshtein
import numpy as np
import operator
import javalang
from collections import defaultdict
from util import *
from setting import *
import copy
import adjust_ocr


def read_Google_Vision_result(json_file):
    with open(json_file) as fin:
        res = json.load(fin)

        lines = []
        full_text = res['responses'][0]['fullTextAnnotation']['text']
        blocks = res['responses'][0]['textAnnotations'][1:]
        bidx = 0
        for line in full_text.split("\n"):
            if line.strip() == "" or line.strip() == "I":
                continue

            words = line.split()
            new_words = []
            start_p = None
            for widx, w in enumerate(words):
                removed = False
                for i in range(bidx, len(blocks)):
                    if w.find(blocks[i]['description']) >= 0:
                        p = blocks[i]['boundingPoly']['vertices'][0]
                        y = p['y'] if 'y' in p else 0
                        x = p['x'] if 'x' in p else 0
                        if y < -1:
                            removed = True

                        if widx == 0:
                            start_p = (x, y)
                            
                        break

                if not removed:
                    new_words.append(w)
                bidx = i

            line = correct_non_ascii(" ".join(new_words))
            if len(lines)>0 and abs(lines[-1][1][1]-start_p[1]) < 1:
                print 'merge line', line, lines[-1][1], start_p
                lines[-1][0] += line
            else:
                lines.append([line, start_p])

        return lines


def diff_lines(lines1, lines2):
    lengths = [[0 for j in range(len(lines2)+1)] for i in range(len(lines1)+1)]
    for i, x in enumerate(lines1):
        for j, y in enumerate(lines2):
            if x.line_nospace == y.line_nospace:
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])

    result = []
    x, y = len(lines1), len(lines2)
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            y -= 1
        else:
            result.insert(0, (x-1, y-1))
            x -= 1
            y -= 1

    delta = ""
    pre_x, pre_y = 0, 0
    for x, y in result:
        deleted = range(pre_x, x)
        inserted = range(pre_y, y)

        for d in deleted:
            delta += "- " + lines1[d].line_nospace + "\n"
        
        for i in inserted:
            delta += "+ " + lines2[i].line_nospace + "\n"
        
        delta += "  " + lines1[x] + "\n"


    x = [r[0] for r in result]
    y = [r[1] for r in result]
    deletes = [i for i in range(len(lines1)) if i not in x]
    inserts = [i for i in range(len(lines2)) if i not in y]
    
    N = len(result)
    changes = []
    for i in range(N):
        if i == 0:
            if x[i] > 0 or y[i] > 0:
                changes.append((range(x[i]), range(y[i])))
        elif i == N - 1:
            if x[i] < len(lines1)-1 or y[i] < len(lines2)-1:
                changes.append(
                    (range(x[i]+1, len(lines1)), range(y[i]+1, len(lines2))))
        else:
            if x[i] + 1 != x[i+1] or y[i] + 1 != y[i+1]:
                changes.append((range(x[i]+1, x[i+1]), range(y[i]+1, y[i+1])))

    return result, changes

def main():
    from JavaLine import JavaLine
    target = ("Java Programming Tutorial - 17 - Constructors", "tPFuVRbUTwA")
    # cluster = 0

    ocr_folder = os.path.join(ocr_dir, target[0]+"_"+target[1])

    lines = adjust_ocr.read_Google_Vision_result(os.path.join(ocr_folder, "1.json"))
    jlines = []
    for line, pos in lines:
        jlines.append(JavaLine(line, pos))


    print adjust_ocr.generate_doc(jlines)

if __name__ == '__main__':
    main()
