from pattern.en import suggest
import string
import javalang
import os
import json
import operator
import numpy as np
import distance
from collections import Counter
from sklearn.cluster import AffinityPropagation, DBSCAN
# from java_line import *
from util import split_by_nonalpha, is_invalid_char
from java_tokenizer import tokenize
import difflib
import Levenshtein
from java_tokenizer import tokenize

def construct_model():
    words = Counter()
    line_structures = Counter()
    for file in os.listdir("../Models"):
        if not file.endswith(".json"):
            continue
        
        print file
        with open("../Models/%s" % file) as fin:
            model = Counter(json.load(fin))

        if file.endswith("-line.json"):
            line_structures = line_structures + model
        else:
            words = words + model

    with open("java-lines.json", "w") as fout:
        json.dump(line_structures, fout, indent=4)
    
    with open("java-words.json", "w") as fout:
        json.dump(words, fout, indent=4)

def parser_one_line(line):
    try:
        tokens = list(javalang.tokenizer.tokenize(line))

        line_structure = []
        for t in tokens:
            cls_type = type(t).__name__
            if cls_type in ["Separator", "Operator", "Keyword", "Modifier", "BasicType", "Annotation"]:
                line_structure.append(t.value)
            else:
                if cls_type == "Identifier" and t.value[0].isupper():
                    line_structure.append("IDU")
                else:
                    line_structure.append("IDL") # Identifier starting with lower char, string, int, float, ...

            # if cls_type not in ["Separator", "Operator", "Annotation"]:
            #     words.append(t.value)

        return ' '.join(line_structure), [t.value for t in tokens]
    except Exception as e:
        words = split_by_nonalpha(line)
        # words = [w for w in words if w!=" " and not is_invalid_char(w)]
        return None, words

def main():
    s1 = "obj1"
    s2 = "obji"

    print Levenshtein.ratio(s1, s2)
            # print c, ord(c)
        

    # tokens = tokenize(s1)
    # for t in tokens:
    #     print t.value.encode("utf8"), type(t.value.encode("utf8"))
    # for op, spos, dpos in Levenshtein.editops(s2, s1):
    #     print op, spos, dpos
    #     if op == "replace":
    #         print s1[dpos]
    #     elif op == "insert":
    #         print s1[dpos]
    #     elif op == "delete":
    #         print s2[spos]

    
    # s1 = "g.fillRect(0, 0, WIDTH, HEIGHT) ;I"
    # tokens = tokenize(s1)
    # print reformat_tokens(tokens)

    # with open("java-lines.json") as fin:
    #     line_structures = json.load(fin)

    # lines = []
    # with open("lines_test.txt") as fin:
    #     for line in fin.readlines():
    #         lines.append(line.strip())

    # N = len(lines)
    # line_similarity = np.zeros((N, N), np.float)
    # for i in range(N):
    #     bi = lines[i]
    #     for j in range(i, N):
    #         bj = lines[j]
    #         # print bi, bj, distance.levenshtein(bi, bj), max(len(bi), len(bj))
    #         line_similarity[i, j] = line_similarity[j, i] = 1 - distance.levenshtein(bi, bj) * 1.0 / max(len(bi), len(bj))
    
    # print line_similarity
    # for idx, line in enumerate(lines):
    #     print line
    #     tokens = tokenize(line, ignore_errors=True)
    #     print tokens
        
        # if struct is not None:
        #     num = line_structures[struct] if struct in line_structures else 0
        
        #     print struct, num
        # else:
        #     print struct
        
        # print '\n'
    # affprop = AffinityPropagation(affinity="precomputed", damping=0.5)
    # affprop.fit(line_similarity) 

    # for idx, cluster_id in enumerate(np.unique(affprop.labels_)):
    #     line_ids, = np.nonzero(affprop.labels_==cluster_id)
    #     for li in line_ids:
    #         print lines[li]
    #     print '\n'
            # try:
            #     tokens = list(javalang.parse.tokenize(line))
            # except Exception as e:
            #     continue
            
            # ls = get_line_structure(tokens)
            # ls = " ".join(ls)

            # if ls not in line_structures or line_structures[ls] <= 0:
            #     continue

            # print line
    
        # for struct in struct_map:
        #     num = line_structures[struct] if struct in line_structures else 0
        #     print struct, struct_map[struct], num

if __name__ == '__main__':
    main()