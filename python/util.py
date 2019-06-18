import numpy as np
# Import the base64 encoding library.
import base64
import requests
import re
# from pattern.en import suggest
import string
import Levenshtein
# import networkx as nx
import javalang


def hv_line_sim(line1, line2):
    x11, y11, x12, y12, frame_num = line1
    x21, y21, x22, y22, frame_num = line2

    if x11 == x12 and x21 == x22:
        return abs(x21 - x11)
    elif y11 == y12 and y21 == y22:
        return abs(y21 - y11)
    else:
        return np.inf

def overlap(min1, max1, min2, max2):
    """returns the overlap between two lines that are 1D"""
    if min1 < min2:
        min1, min2 = min2, min1
        max1, max2 = max2, max1
    
    if max2 < min1:
        return 0
    elif max1 > max2:
        return max2 - min1
    else:
        return max1 - min1

def hv_line_overlap_sim(line1, line2, len_ratio=0.8, overlap_ratio=0.8):
    x11, y11, x12, y12 = line1[0:4]
    x21, y21, x22, y22 = line2[0:4]
    
    if x11 == x12 and x21 == x22:
        # ratio = (y12 - y11) * 1.0  / (y22 - y21)
        # ratio = ratio if ratio < 1 else 1 / ratio
        
        # if ratio < len_ratio:
        #     return np.inf

        op = overlap(y11, y12, y21, y22)
        if op < 0:
            return np.inf

        ratio = (op * 1.0) / min(abs(y11 - y12), abs(y21 - y22))
        if ratio < overlap_ratio:
            return np.inf

        return abs(x21 - x11)
    elif y11 == y12 and y21 == y22:
        # ratio = (x12 - x11) * 1.0  / (x22 - x21)
        # ratio = ratio if ratio < 1 else 1 / ratio

        # if ratio < len_ratio:
        #     return np.inf

        op = overlap(x11, x12, x21, x22)
        if op < 0:
            return np.inf
        
        ratio = (op * 1.0) / min(abs(x11 - x12), abs(x21 - x22))
        if ratio < overlap_ratio:
            return np.inf

        return abs(y21 - y11)
    else:
        return np.inf

def frame_sim(img1, img2, height, width):
    img1 = img1.reshape(height, width)
    img2 = img2.reshape(height, width)

    print 1 - skimage.measure.compare_ssim(img1, img2)
    # return 1 - skimage.measure.compare_ssim(img1, img2)
    return skimage.measure.compare_nrmse(img1, img2)

def rect_sim(rect1, rect2):
    x1, y1, w1, h1 = rect1[0:4]
    x2, y2, w2, h2 = rect2[0:4]

    # print abs(w1-w2) * abs(h1-h2), abs(w1-w2), abs(h1-h2)
    return max(abs(w1-w2), abs(h1-h2))


def dump_numpy(o):
    if isinstance(o, np.int64): 
        return int(o)  
    else:
        return o.__str__()

def vh_intersection(vline, hline, limit=2):
    x1, y1, x2 ,y2 = vline
    x3, y3, x4, y4 = hline

    if x1 != x2 or y3 != y4:
        return False

    if not (x1+limit >= x3 and x1-limit <= x4 and y3+limit >= y1 and y3-limit <= y2):
        return False
    
    return True

def is_invalid_char(char):
    invalidChars = set(string.punctuation.replace("_", ""))
    return char in invalidChars

def is_invalid_string(s):
    invalidChars = set(string.punctuation.replace("_", ""))
    for char in s:
        if char in invalidChars:
            return True
    
    return False

def split_by_nonalpha(line):
    invalidChars = set(string.punctuation.replace("_", ""))
    words = line.split()
    
    res = []
    for idx, word in enumerate(words):  
        temp = ""
        for char in word:
            if not is_invalid_char(char):
                temp += char
            else:
                if temp != "":
                    res.append(temp)
                res.append(char)
                temp = ""
        
        if temp != "":
            res.append(temp)
        
        # if idx != len(words)-1:
        #     res.append(" ")

    return res

#    y1 y2 y3 y4
# x1 1  1  0  1
# x2 1  1  0  0
# x3 0  1  1  1
# x4 1  1  1  1
def find_rects(m):
    rects = []

    xstep, ystep = 1, 1
    xlen, ylen = m.shape

    for xstep in range(1, xlen):
        for ystep in range(1, ylen):
            for i in range(xlen - xstep):
                for j in range(ylen - ystep):
                    if m[i, j] == 1 and m[i, j+ystep] == 1 and \
                        m[i+xstep, j] == 1 and m[i+xstep, j+ystep] == 1:
                        
                        flag = False
                        for r in rects:
                            a, b, c, d = r
                            if a>=i and a<=i+xstep and b>=j and b<=j+ystep and \
                                c>=i and c<=i+xstep and d>=j and d<=j+ystep:
                                flag = True
                                break

                        if not flag:
                            rects.append([i, j, i+xstep, j+ystep])

    return rects



def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

def spell_check(word):
    candidates = suggest(word)

    if len(candidates) <= 0 and candidates[0][1] < 0.5:
        return False

    return candidates[0][0] == word

def default_equal(x, y):
    return x == y

def line_equal(x, y):
    r = Levenshtein.ratio(x.line_nospace, y.line_nospace)
    return r >= 0.9

def lcs(a, b, equal_function=None):
    if equal_function is None:
        equal_function = default_equal

    lengths = [[0 for j in range(len(b)+1)] for i in range(len(a)+1)]
    # row 0 and column 0 are initialized to 0 already
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if equal_function(x, y):
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])

    result = []
    x, y = len(a), len(b)
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            y -= 1
        else:
            # assert a[x-1] == b[y-1]
            # result = a[x-1] + result
            result.insert(0, a[x-1])
            x -= 1
            y -= 1
    return result

def lcs_similarity(a, b, equal_function=None):
    if len(a) == 0 or len(b) == 0:
        return 0
    return len(lcs(a, b, equal_function)) * 1.0 / min(len(a), len(b))


def correct_non_ascii(s):
    all_ascii = all(ord(c) < 128 for c in s)
    if not all_ascii:
        # print s, 'has special char'
        chars = []
        # print 'A non ascii line is detected:', s
        has_O = False
        for idx, c in enumerate(unicode(s)):
            if c == u"ー":
                chars.append('-')
            elif c == u"し":
                chars.append('L')
            elif c == u"Ξ":
                chars.append('=')
            elif c == u"。":
                chars.append('.')
            elif c == u"θ" or c == u"Θ":
                chars.append('0')
            elif c == u"ì" or c == u"ǐ":
                chars.append('i')
            elif c == u"ł":
                chars.append("l")
            elif c == u"þ":
                chars.append("h")
            elif c == u"ß":
                chars.append("s")
            elif c == u"ö":
                chars.append("a")
            # elif c == u"エ":
            elif ord(c) >= 128:
                print "A non ascii char", c, s
                chars.append(' ')
                continue
            else:
                chars.append(c)
        
        return "".join(chars)
    else:
        return s

def camel_case_split(a):
    return re.sub('([a-zA-Z])([A-Z0-9])', r'\1 \2', a).split()

def second_to_str(sec):
    hour = int(sec / 3600)
    minute = int((sec - hour * 3600) / 60)
    second = int(sec - hour * 3600 - minute * 60)
    
    if hour != 0:
        return "%02d:%02d:%02d" % (hour, minute, second)
    else:
        return "%02d:%02d" % (minute, second)


def main():
    pass

if __name__ == '__main__':
    main()