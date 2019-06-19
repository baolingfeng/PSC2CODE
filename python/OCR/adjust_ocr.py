import os
import json
import Levenshtein
import copy
import networkx as nx
from collections import defaultdict
from pattern.en import suggest
import difflib
from sklearn.cluster import AffinityPropagation, DBSCAN
from JavaLine import JavaLine
from lm import JAVA_WORDS, JAVA_LINE_STRUCTURE, DICT_WORDS, WORD_MEAN_2, LINE_MEAN_2
from audio import translate_srt_script
from util import *
from setting import *


def read_Google_Vision_result(json_file):
    # print json_file
    with open(json_file) as fin:
        res = json.load(fin)

        if 'fullTextAnnotation' not in res['responses'][0]:
            return []

        full_text = res['responses'][0]['fullTextAnnotation']['text']
        blocks = res['responses'][0]['textAnnotations'][1:]

        lines = []
        line = [blocks[0]]
        blocks = blocks[1:]
        for idx, block in enumerate(blocks):
            text = block['description']
            p = block['boundingPoly']['vertices'][0]
            y = p['y'] if 'y' in p else 0
            x = p['x'] if 'x' in p else 0

            pre_p = line[-1]['boundingPoly']['vertices'][0]
            pre_y = pre_p['y'] if 'y' in pre_p else 0

            if abs(pre_y - y) < 5:
                line.append(block)
            else:
                lines.append(line)
                line = [block]

        if len(line) > 0:
            lines.append(line)

        full_lines = full_text.split('\n')
        ret = []
        for lid, line in enumerate(lines):
            y1s = [b['boundingPoly']['vertices'][0]['y']
                   for b in line if 'y' in b['boundingPoly']['vertices'][0]]
            y1 = min(y1s) if len(y1s) > 0 else 0
            y2s = [b['boundingPoly']['vertices'][3]['y']
                   for b in line if 'y' in b['boundingPoly']['vertices'][3]]
            y2 = max(y2s) if len(y2s) > 0 else 0

            p = line[0]['boundingPoly']['vertices'][0]
            # y1 = p['y'] if 'y' in p else 0
            x1 = p['x'] if 'x' in p else 0

            p2 = line[-1]['boundingPoly']['vertices'][3]
            # y2 = p2['y'] if 'y' in p2 else 0
            x2 = p2['x'] if 'x' in p2 else 0

            # if y1 < -1:
            #     continue

            if len(full_lines) != len(lines):
                s = ""
                for idx, block in enumerate(line):
                    p = block['boundingPoly']['vertices'][2]
                    x = p['x'] if 'x' in p else 0
                    sep = ""
                    if idx < len(line) - 1:
                        next_block = line[idx+1]
                        next_p = next_block['boundingPoly']['vertices'][0]
                        next_x = next_p['x'] if 'x' in next_p else 0

                        # print block['description'], next_block['description'], x, next_x
                        if abs(next_x - x) > 5:
                            sep = " "

                    s = s + block['description'] + sep
            else:
                s = full_lines[lid]

            if lid == 0 and s.find(".java") > 0:
                continue

            ret.append([correct_non_ascii(s), (x1, y1, x2, y2)])

        return ret


def generate_doc(lines):
    if len(lines) == 0:
        return ""

    mean_h = sum([line.pos[3] - line.pos[1]
                  for line in lines]) * 1.0 / len(lines)
    min_x = min([line.pos[0] for line in lines])
    max_x = max([line.pos[0] for line in lines])

    data = np.arange(len(lines), dtype=int).reshape(-1, 1)
    dbscan = DBSCAN(eps=5, min_samples=1, metric=lambda X, Y: abs(
        lines[int(X[0])].pos[0]-lines[int(Y[0])].pos[0]))
    clusters = dbscan.fit(data)

    line_clusters = []
    for idx, cluster_id in enumerate(np.unique(clusters.labels_)):
        line_ids, = np.nonzero(clusters.labels_ == cluster_id)
        line_clusters.append(line_ids)

    line_clusters = sorted(line_clusters, key=lambda x: lines[x[0]].pos[0])
    doc = ""
    for idx, line in enumerate(lines):
        for cid, cluster in enumerate(line_clusters):
            if idx in cluster:
                break

        doc += '\t' * cid + line.line_nospace + "\n"
        if idx < len(lines) - 1:
            # print mean_h, lines[idx+1].pos[1] - line.pos[3]
            doc += '\n' * \
                (int(round((abs(lines[idx+1].pos[1] - line.pos[3])) / mean_h)))

    return doc


def diff_text(lines1, lines2):
    diff = difflib.ndiff(lines1, lines2)

    diff = list(diff)
    deleted = []
    added = []
    changes = []
    for i, x in enumerate(diff):
        if x.startswith("- "):
            deleted.append(i)
            changes.append(x)
        elif x.startswith("+ "):
            added.append(i)
            changes.append(x)

    diff_result = {}
    diff_result['changes'] = changes
    diff_result['deleted'] = len(deleted)
    diff_result['added'] = len(added)

    if len(changes) > 1:
        scroll_down = (deleted == range(len(deleted)) and added ==
                       range(len(diff)-len(added), len(diff)))
        scroll_up = (added == range(len(added)) and deleted ==
                     range(len(diff)-len(deleted), len(diff)))

        diff_result['scroll'] = True
        if scroll_down or scroll_up:
            print 'scroll', scroll_down, scroll_up
            diff_result['new_tex'] = '\n'.join([x[2:] for x in diff])

    return diff_result


def diff_lines(lines1, lines2, detail=True):
    lengths = [[0 for j in range(len(lines2)+1)] for i in range(len(lines1)+1)]
    for i, x in enumerate(lines1):
        for j, y in enumerate(lines2):
            if Levenshtein.ratio(x.line_nospace, y.line_nospace) > 0.9:
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])

    lcs_lines = []
    x, y = len(lines1), len(lines2)
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            y -= 1
        else:
            lcs_lines.insert(0, (x-1, y-1))
            x -= 1
            y -= 1

    sim = len(lcs_lines) * 1.0 / min(len(lines1), len(lines2)
                                     ) if len(lines1) > 0 and len(lines2) > 0 else 0
    if not detail:
        return sim

    # if len(lcs_lines) == 0:
    lcs_lines.append((len(lines1), len(lines2)))

    delta = []
    pre_x, pre_y = 0, 0
    all_deleted = []
    all_inserted = []
    for x, y in lcs_lines:
        deleted = range(pre_x, x)
        inserted = range(pre_y, y)

        all_deleted.extend(deleted)
        for d in deleted:
            delta.append("- " + lines1[d].line_nospace)

        all_inserted.extend(inserted)
        for i in inserted:
            delta.append("+ " + lines2[i].line_nospace)

        # if x < len(lines1):
        #     delta += "  " + lines1[x].line_nospace + "\n"

        pre_x = x+1
        pre_y = y+1

    return sim, lcs_lines[0:-1], all_deleted, all_inserted, '\n'.join(delta)


class GoogleOCRParser:
    def __init__(self, video_name, srt_file):
        self.video_name = video_name
        self.ocr_folder = os.path.join(ocr_dir, video_name)
        self.srt_file = srt_file
        self.init_from_folder(self.ocr_folder)

    def is_correct_word(self, w):
        w = w.strip()
        if w in JAVA_WORDS and JAVA_WORDS[w] > 1:
            return True

        if w in self.audio_word_set:
            return True

        if w.lower() in DICT_WORDS or w.startswith("\\"):
            return True

        if w[0] == '"' and w[-1] == '"' or (w[0] == "'" and w[-1] == "'"):
            w2 = w[1:-1].strip()
            if w2 == "":
                return True

            for ww in w2.split():
                if not self.is_correct_word(ww):
                    return False
            return True

        split_words = camel_case_split(w)
        if len(split_words) == 1:
            return False

        for ww in split_words:
            if not self.is_correct_word(ww):
                return False
        return True

    def init_from_folder(self, ocr_folder):
        print 'reading OCR results...', ocr_folder
        docs = []

        self.video_words = defaultdict(int)
        self.video_lines = defaultdict(int)
        for f in os.listdir(ocr_folder):
            if not f.endswith('.json'):
                continue

            # frame = int(f.split("_")[0])
            frame = int(f[0:-5])
            lines = []
            lines_pos = []
            for line, pos in read_Google_Vision_result("%s/%s" % (ocr_folder, f)):
                # print line
                words = line.split()
                if len(words) > 0 and words[0].isdigit():
                    words = words[1:]
                line = ' '.join(words)

                line = JavaLine(line, pos)
                if len(line.line_nospace) < 3:
                    continue

                self.video_lines[line] += 1

                words = line.get_words()
                for w in words:
                    self.video_words[w.encode("utf8")] += 1

                lines.append(line)
                lines_pos.append(pos)

            docs.append({'lines': lines, 'frame': frame})

        self.line_set = list(self.video_lines.keys())
        self.word_set = list(self.video_words.keys())

        self.audios, self.audio_word_set = translate_srt_script(self.srt_file)

        self.correct_word_set = [
            w.encode("utf8") for w in self.word_set if self.is_correct_word(w)]
        self.incorrect_word_set = [
            w.encode("utf8") for w in self.word_set if not self.is_correct_word(w)]
        # print self.incorrect_word_set

        self.docs = sorted(docs, key=lambda x: x['frame'])
        print 'Total ORCed frame:', len(self.docs)

    def correct_words(self):
        # print self.incorrect_word_set
        corrected = {}
        # uncorrected = []
        for w in self.incorrect_word_set:
            candidates = sorted([w2 for w2 in self.correct_word_set if Levenshtein.ratio(w, w2) >= 0.75 and Levenshtein.distance(w.lower(
            ), w2.lower()) <= 2], key=lambda x: (Levenshtein.distance(x.lower(), w.lower()), Levenshtein.distance(x, w), -self.video_words[x]))

            if len(candidates) > 0:
                # print w, ' ==> ', candidates[0]
                corrected[w] = candidates[0]
            # else:
                # uncorrected.append(w)

        incorrect_lines = [
            line for line in self.line_set if line.struct not in JAVA_LINE_STRUCTURE]
        correct_lines = [
            line for line in self.line_set if line.struct in JAVA_LINE_STRUCTURE]

        corrected_lines = {}
        for line in incorrect_lines:
            candidates = sorted([line2 for line2 in correct_lines if Levenshtein.ratio(
                line.line_nospace, line2.line_nospace) > 0.66], key=lambda x: (Levenshtein.distance(x.line, line.line)))

            if len(candidates) > 0:
                corrected_lines[line] = candidates[0]
                # print line, ' ==> ', candidates

        incorrect_word_set2 = set()
        true_corrected = {}
        for doc in self.docs:
            for line in doc['lines']:
                if line in corrected_lines:
                    # print 'before correct line', line, " /// ", corrected_lines[line]
                    line.reset_tokens(corrected_lines[line].tokens)

                for tid, w in line.incorrect_words(self.incorrect_word_set):
                    if w in corrected:
                        line.reset_token(tid, corrected[w])
                        true_corrected[w] = corrected[w]
                
                incorrect_word_set2 |= set([w for w in line.get_words() if not self.is_correct_word(w)])

        uncorrected = list(set(self.incorrect_word_set) & incorrect_word_set2)
        corrected2 =  list((set(self.incorrect_word_set) - incorrect_word_set2) - set(corrected.keys()))
        with open(os.path.join(self.ocr_folder, "parse", "correct.json"), "w") as fout:
            json.dump({"words": true_corrected, "len_words": len(true_corrected.keys()),
                    #   "lines": [(l.line, corrected_lines[l].line) for l in corrected_lines], 
                        "uncorrected": uncorrected, 
                        "len_uncorrected": len(uncorrected),
                        "corrected2": corrected2,
                        "total_correct": len(self.correct_word_set)},
                        fout, indent=4)

    def cluster_docs(self):
        rule1 = r'public class .*'
        rule2 = r'(^public )?(abstract )?class .*'
        for doc in self.docs:
            for line in doc['lines']:
                if re.match(rule1, line.line):
                    i = line.line.split().index("class")
                    cls_name = line.line.split()[i+1]
                    doc['class'] = cls_name[:-
                                            1] if cls_name.endswith("{") else cls_name
                    break
                elif re.match(rule1, line.line):
                    i = line.line.split().index("class")
                    cls_name = line.line.split()[i+1]
                    doc['class'] = cls_name[:-
                                            1] if cls_name.endswith("{") else cls_name

        def doc_metric(X, Y):
            doc1 = self.docs[int(X[0])]
            doc2 = self.docs[int(Y[0])]

            r = 1
            if 'class' in doc1 and 'class' in doc2:
                if doc1['class'].lower() == doc2['class'].lower():
                    r = 2
                else:
                    # print 'class diff', doc1['class'], doc2['class']
                    r = 0.3

            sim = diff_lines(doc1['lines'], doc2['lines'], detail=False)
            dist = 1 - sim * r if sim * r < 1 else 0

            return dist

        self.file_names = {}
        if len(self.docs) <= 0:
            return

        data = np.arange(len(self.docs), dtype=int).reshape(-1, 1)
        dbscan = DBSCAN(eps=0.5, min_samples=1,
                        metric=lambda X, Y: doc_metric(X, Y))
        clusters = dbscan.fit(data)

        noname = 1
        for idx, cluster_id in enumerate(np.unique(clusters.labels_)):
            if cluster_id == -1:
                continue

            doc_ids, = np.nonzero(clusters.labels_ == cluster_id)

            class_names = defaultdict(int)
            for did in doc_ids:
                self.docs[did]['cluster_id'] = cluster_id
                if 'class' in self.docs[did]:
                    class_names[self.docs[did]['class']] += 1

            class_names = [(k, class_names[k]) for k in class_names]
            if len(class_names) > 0:
                class_names = sorted(
                    class_names, key=lambda x: x[1], reverse=True)
                self.file_names[cluster_id] = class_names[0][0]
            else:
                self.file_names[cluster_id] = "Unknown File %d" % noname
                noname += 1

        print 'detected file', self.file_names

    def generate_actions(self):
        self.docs = [doc for doc in self.docs if 'cluster_id' in doc]
        actions = []
        new_docs = {}
        for idx, doc in enumerate(self.docs):
            new_doc = {}
            new_doc['cluster'] = doc['cluster_id']
            new_doc['lines'] = generate_doc(doc['lines'])
            new_docs[doc['frame']] = new_doc

            if idx == len(self.docs) - 1:
                continue

            next_doc = self.docs[idx+1]
            action = {}
            action['frame1'] = doc['frame']
            action['frame2'] = next_doc['frame']
            action['display_time'] = second_to_str(next_doc['frame'])
            action['cluster1'] = doc['cluster_id']
            action['cluster2'] = next_doc['cluster_id']
            if doc['cluster_id'] != next_doc['cluster_id']:
                action['type'] = 'switch'
                actions.append(action)
            else:
                sim, lcs_lines, deleted, inserted, delta = diff_lines(
                    doc['lines'], next_doc['lines'])

                if len(deleted) > 1 and len(inserted) > 0:
                    if deleted == range(0, len(deleted)) and inserted == range(len(next_doc['lines'])-len(inserted), len(next_doc['lines'])):
                        print 'Scroll down', deleted, inserted, doc['frame'], next_doc['frame']
                        continue
                    elif inserted == range(0, len(inserted)) and deleted == range(len(doc['lines'])-len(deleted), len(doc['lines'])):
                        print 'Scroll up', deleted, inserted, doc['frame'], next_doc['frame']
                        continue

                if len(deleted) > 0 or len(inserted) > 0:
                    action['type'] = 'edit'
                    action['delta'] = delta
                    action['deleted'] = len(deleted)
                    action['inserted'] = len(inserted)
                    actions.append(action)

        res = {}
        res['frames'] = [doc['frame'] for doc in self.docs]
        res['docs'] = new_docs
        res['actions'] = actions
        res['file_names'] = self.file_names
        # res['file_num'] = len()
        if not os.path.exists(os.path.join(self.ocr_folder, "parse")):
            os.mkdir(os.path.join(self.ocr_folder, "parse"))
        with open(os.path.join(self.ocr_folder, "parse", "result.json"), "w") as fout:
            json.dump(res, fout, indent=4)

    def select_lines(self, lines):
        new_lines = []
        for line in lines:
            new_line = line.correct(
                self.correct_word_set, self.incorrect_word_set)
            new_lines.append(new_line)

        new_lines2 = []
        for line in new_lines:

            if line.struct in JAVA_LINE_STRUCTURE:
                new_lines2.append(line)

        if len(new_lines2) > 0:
            new_lines2 = sorted(
                new_lines2, key=lambda x: JAVA_LINE_STRUCTURE[x.struct], reverse=True)
            return new_lines2[0]
        else:
            temp = sorted([(line, new_lines.count(line)) for line in set(
                new_lines)], key=lambda x: x[1], reverse=True)
            return temp[0][0]

    def cluster_lines(self):
        def line_sim(X, Y):
            line1 = self.line_set[int(X[0])]
            line2 = self.line_set[int(Y[0])]

            incorrect1 = [w for w in line1.get_words(
            ) if w in self.incorrect_word_set]
            incorrect2 = [w for w in line2.get_words(
            ) if w in self.incorrect_word_set]

            # if  len(incorrect1) == 0 and len(incorrect2) == 0:
            #     return 1

            line11 = ''.join([e for e in line1.line_nospace if e.isalnum()])
            line22 = ''.join([e for e in line2.line_nospace if e.isalnum()])

            edit = Levenshtein.distance(line11, line22)
            # ratio = Levenshtein.ratio(line11, line22)
            if edit >= 3:
                return 1

            return 1 - Levenshtein.ratio(line1.line_nospace, line2.line_nospace)

        if not os.path.exists(os.path.join(self.ocr_folder, "parse")):
            os.mkdir(os.path.join(self.ocr_folder, "parse"))

        data = np.arange(len(self.line_set), dtype=int).reshape(-1, 1)
        dbscan = DBSCAN(eps=0.1, min_samples=1, metric=line_sim)
        # dbscan = DBSCAN(eps=0.15, min_samples=1, metric=lambda X, Y: 1 - Levenshtein.ratio(
        #     self.line_set[int(X[0])].line_nospace, self.line_set[int(Y[0])].line_nospace))
        clusters = dbscan.fit(data)

        fout = open(os.path.join(self.ocr_folder, "parse", "lines.txt"), "w")
        self.cluster_lines = {}
        self.lines_cluster = {}
        lines = self.line_set
        for idx, cluster_id in enumerate(np.unique(clusters.labels_)):
            line_ids, = np.nonzero(clusters.labels_ == cluster_id)

            clines = [lines[lid] for lid in line_ids]
            cline = self.select_lines(clines)

            self.cluster_lines[cluster_id] = (clines, cline)
            for lid in line_ids:
                self.lines_cluster[lines[lid]] = cluster_id

            text_lines = sorted(
                [line.line_nospace for line in clines], key=lambda x: len(x), reverse=True)
            fout.write("%d\n" % idx)
            fout.write("\n".join(text_lines))
            fout.write("\n--------------------\n")
            fout.write(cline.line_nospace)
            fout.write("\n\n")

        for doc in self.docs:
            doc['lines_cluster'] = []
            doc['lines2'] = []
            for line in doc['lines']:
                line_cluster = self.lines_cluster[line]

                new_line = self.cluster_lines[line_cluster][1]
                doc['lines2'].append(JavaLine(new_line.tokens, line.pos))

                doc['lines_cluster'].append(self.lines_cluster[line])

        data = np.arange(len(self.docs), dtype=int).reshape(-1, 1)
        dbscan = DBSCAN(eps=0.5, min_samples=1, metric=lambda X, Y: 1 - lcs_similarity(
            self.docs[int(X[0])]['lines_cluster'], self.docs[int(Y[0])]['lines_cluster']))
        clusters = dbscan.fit(data)
        rule = r'(^public )?class .*'
        file_names = {}
        noname = 1
        for idx, cluster_id in enumerate(np.unique(clusters.labels_)):
            doc_ids, = np.nonzero(clusters.labels_ == cluster_id)

            # print cluster_id, doc_ids, [self.docs[did]['lines_cluster'] for did in doc_ids]
            class_names = defaultdict(int)
            for did in doc_ids:
                self.docs[did]['cluster_id'] = cluster_id

                for line in self.docs[did]['lines2']:
                    if re.match(rule, line.line):
                        i = line.line.split().index("class")
                        cls_name = line.line.split()[i+1]
                        cls_name = cls_name[:-
                                            1] if cls_name.endswith("{") else cls_name
                        class_names[cls_name] += 1
                        break

            print 'detected class:', class_names
            class_names = [(k, class_names[k]) for k in class_names]
            if len(class_names) > 0:
                class_names = sorted(
                    class_names, key=lambda x: x[1], reverse=True)
                file_names[cluster_id] = class_names[0][0]
            else:
                file_names[cluster_id] = "Unknown File %d" % noname
                noname += 1

        res = {}
        res['frames'] = [doc['frame'] for doc in self.docs]
        res['docs'] = {}
        res['actions'] = []
        res['file_names'] = file_names
        res['file_num'] = len(np.unique(clusters.labels_))
        for idx, doc in enumerate(self.docs):
            new_doc = {}
            new_doc['cluster'] = doc['cluster_id']
            # [line.line_nospace for line in doc['lines2']]
            new_doc['lines'] = generate_doc(doc['lines2'])
            res['docs'][doc['frame']] = new_doc

            if idx == len(self.docs) - 1:
                continue

            next_doc = self.docs[idx+1]
            if doc['cluster_id'] != next_doc['cluster_id']:
                print 'stwich file', doc['frame'], next_doc['frame']
                action = {}
                action['type'] = 'switch'
                action['frame1'] = doc['frame']
                action['frame2'] = next_doc['frame']
                action['cluster1'] = doc['cluster_id']
                action['cluster2'] = next_doc['cluster_id']
                action['display_time'] = second_to_str(next_doc['frame'])
                res['actions'].append(action)
            else:
                text1 = [line.line_nospace for line in doc['lines2']]
                text2 = [line.line_nospace for line in next_doc['lines2']]

                diff = diff_text(text1, text2)
                if len(diff['changes']) > 0:
                    action = {}
                    action['type'] = 'edit'
                    action['frame1'] = doc['frame']
                    action['frame2'] = next_doc['frame']
                    action['cluster1'] = doc['cluster_id']
                    action['cluster2'] = next_doc['cluster_id']
                    action['display_time'] = second_to_str(next_doc['frame'])
                    action['delta'] = diff['changes']
                    res['actions'].append(action)
                    # print doc['frame'], next_doc['frame']
                    # print diff['changes']
                    # print '#########'

        with open(os.path.join(self.ocr_folder, "parse", "result.json"), "w") as fout:
            json.dump(res, fout, indent=4)

    def calc_line_similarity(self, line1, line2, word_similarity):
        for w1 in line1.get_words():
            max_sim = max([word_similarity[self.word_set.index(
                w1), self.word_set.index(w2)] for w2 in line2.get_words()])


def main():
    with open("verified_videos.txt") as fin:
        process_hashes = [line.strip() for line in fin.readlines()]

    from dbimpl import DBImpl
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select a.hash, a.title from videos a, playlists b where a.playlist = b.id and a.used = 1 and b.used = 1'
    num = 1
    for r in db.querymany(sql):
        video_hash, video_name = r
        video_name = video_name.strip()
        ocr_folder = os.path.join(ocr_dir, video_name+"_"+video_hash)

        if video_hash in process_hashes:
            print ocr_folder
            parser = GoogleOCRParser(video_name, ocr_folder)
            parser.correct_words()



if __name__ == '__main__':
    main()
