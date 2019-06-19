import os
import sys
# import javalang
from collections import defaultdict, Counter
import json
from JavaLine import JavaLine
from java_tokenizer import tokenize
sys.path.append('..')
from setting import *

def read_from_project(project_folder, model_folder="../Models"):
    # folder = "%s/%s" % (repo_folder, project)
    project = os.path.split(project_folder)[-1]
    print 'extract line structure from', project

    unigram_word = defaultdict(int)
    bigram_word = defaultdict(int)
    
    word_set = defaultdict(int)
    line_structures = defaultdict(int)
    for path, subdirs, files in os.walk(project_folder):
        for name in files:
            if not name.endswith(".java"):
                continue

            # print os.path.join(path, name)
            with open(os.path.join(path, name)) as fin:
                tokens = list(tokenize(fin.read()))
                if len(tokens) <= 0:
                    continue

                line_num = tokens[-1].position[0]
                for line in range(1, line_num+1):
                    line_tokens = [t for t in tokens if t.position[0] == line]
                    if len(line_tokens) <= 0:
                        continue

                    java_line = JavaLine(line_tokens)
                    line_structures[java_line.struct] += 1

                    words = java_line.get_filtered_words()
                    for w in words:
                        word_set[w] += 1

    with open("%s/%s.json" % (model_folder, project), "w") as fout:
        json.dump(word_set, fout, indent=4)

    with open("%s/%s-line.json" % (model_folder, project), "w") as fout:
        json.dump(line_structures, fout, indent=4)


def combine_all(model_folder):
    word_set = Counter({})
    line_structures = Counter({})

    for jsonfile in os.listdir(model_folder):
        if not jsonfile.endswith(".json"):
            continue
        
        with open(os.path.join(model_folder, jsonfile)) as fin:
            data = Counter(json.load(fin))

        if jsonfile.endswith("-line.json"):
            line_structures = line_structures + data
        else:
            word_set = word_set + data
    
    with open("java-words.json", "w") as fout:
        json.dump(word_set, fout, indent=4)

    with open("java-lines.json", "w") as fout:
        json.dump(line_structures, fout, indent=4)


def count_java_repos():
    repo_folder = "%s/JavaRepos" % working_dir
    model_folder = "../Models"
    # project = "gradle"
    # read_from_project(os.path.join(repo_folder, project))

    for project in os.listdir(repo_folder):
        if not os.path.isdir(os.path.join(repo_folder, project)):
            continue

        if os.path.exists('%s/%s.json' % (model_folder, project)):
            print 'exist', project
            continue

        try:
            read_from_project(os.path.join(repo_folder, project))
        except Exception as e:
            print 'error', project, e

def main():
    model_folder = "../Models"
    # count_java_repos()
    combine_all(model_folder)
    # read_from_project(os.path.join("%s/JavaRepos" % working_dir, "gradle"))

if __name__ == '__main__':
    main()
    # count_java_repos()
