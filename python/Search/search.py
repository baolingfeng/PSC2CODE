import os
import json
from dbimpl import DBImpl
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
sys.path.append('..')
from setting import *
from util import correct_non_ascii
from OCR.adjust_ocr import GoogleOCRParser, diff_lines
from OCR.JavaLine import JavaLine
from OCR.lm import JAVA_WORDS, JAVA_LINE_STRUCTURE

db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
sql = 'select a.hash, a.title from videos a, playlists b where a.playlist = b.id and a.used = 1 and b.used = 1'
res = db.querymany(sql)

video_folders = []
video_hash_map = {}
for video_hash, video_title in res:
    video_folders.append((video_title.strip(), video_hash))
    video_hash_map[video_hash] = video_title

# baseline 
def construct_index_with_noise():
    all_docs = []
    video_track = {}
    num = 0

    all_frame_docs = []
    frame_track = {}
    frame_num = 0
    for video_title, video_hash in video_folders:
        video_folder = video_title + '_' + video_hash
        ocr_path = os.path.join(ocr_dir, video_folder)
        
        print video_folder
        video_docs = []
        with open(os.path.join(ocr_path, "parse", "result.json")) as fin:
            res = json.load(fin)
            for frame in res['frames']:
                doc_words = []
                for line in res['docs'][str(frame)]['lines'].split('\n'):
                    jline = JavaLine(line)
                    doc_words.extend(jline.get_words())

                video_docs.append(' '.join(doc_words))
                all_frame_docs.append(' '.join(doc_words))
                frame_track[frame_num] = (video_hash, frame)
                frame_num += 1
            
        noise_folder = os.path.join(ocr_dir, video_folder, 'noise')
        if os.path.exists(noise_folder):
            print 'text in noise frames'
            for f in os.listdir(noise_folder):
                if f.endswith('.json'):
                    frame = int(f[0:-5])
                    with open(os.path.join(noise_folder, f)) as fin:
                        res = json.load(fin)
                        if 'responses' not in res  or 'fullTextAnnotation' not in res['responses'][0]:
                            continue

                        full_text = res['responses'][0]['fullTextAnnotation']['text']
                        # full_text = correct_non_ascii(full_text)
                        is_java_code = False
                        doc_words = []
                        for line in full_text.split('\n'):
                            jline = JavaLine(line)
                            if jline.struct in JAVA_LINE_STRUCTURE:
                                is_java_code = True

                            doc_words.extend([w for w in jline.get_words() if w in JAVA_WORDS])
                        
                        # ignore frames that do not cotain Java code
                        if is_java_code:
                            video_docs.append(' '.join(doc_words))
                            all_frame_docs.append(' '.join(doc_words))
                            frame_track[frame_num] = (video_hash, frame)
                            frame_num += 1
        
        all_docs.append(' '.join(video_docs))
        video_track[num] = (video_hash)
        num += 1
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_docs)
    pickle.dump(tfidf_matrix, open("tfidf_noise.pkl", "wb"))
    pickle.dump(vectorizer.get_feature_names(), open("features_noise.pkl", "wb"))
    pickle.dump(video_track, open("video_track_noise.pkl", "wb"))

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_frame_docs)
    pickle.dump(tfidf_matrix, open("tfidf_noise_frames.pkl", "wb"))
    pickle.dump(vectorizer.get_feature_names(), open("features_noise_frames.pkl", "wb"))
    pickle.dump(frame_track, open("frame_noise_track.pkl", "wb"))

def construct_index():
    all_docs = []
    video_track = {}
    num = 0

    all_frame_docs = []
    frame_track = {}
    frame_num = 0

    for video_title, video_hash in video_folders:
        video_folder = video_title + '_' + video_hash
        ocr_path = os.path.join(ocr_dir, video_folder)
        
        print video_folder
        with open(os.path.join(ocr_path, "parse", "result.json")) as fin:
            res = json.load(fin)
            video_docs = []
            for frame in res['frames']:
                doc_words = []
                for line in res['docs'][str(frame)]['lines'].split('\n'):
                    jline = JavaLine(line)
                    doc_words.extend(jline.get_words())

                video_docs.append(' '.join(doc_words))
                all_frame_docs.append(' '.join(doc_words))
                frame_track[frame_num] = (video_hash, frame)
                frame_num += 1
            
            all_docs.append(' '.join(video_docs))
            video_track[num] = (video_hash)
            num += 1

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_docs)
    pickle.dump(tfidf_matrix, open("tfidf.pkl", "wb"))
    pickle.dump(vectorizer.get_feature_names(), open("features.pkl", "wb"))
    pickle.dump(video_track, open("video_track.pkl", "wb"))

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_frame_docs)
    pickle.dump(tfidf_matrix, open("tfidf_frames.pkl", "wb"))
    pickle.dump(vectorizer.get_feature_names(), open("features_frames.pkl", "wb"))
    pickle.dump(frame_track, open("frame_track.pkl", "wb"))



def tf_idf():
    tfidf_matrix = pickle.load(open("tfidf_noise.pkl", "rb"))
    features = pickle.load(open("features_noise.pkl", "rb"))
    video_track = pickle.load(open("video_track_noise.pkl", "rb"))

    fout = open("scores_noise.txt", "w")

    num = tfidf_matrix.shape[0]
    for n in range(num):

        print video_track[n]
        feature_index = tfidf_matrix[n,:].nonzero()[1]
        tfidf_scores = zip(feature_index, [tfidf_matrix[n, x] for x in feature_index])
        tfidf_scores = sorted([(w, s) for w, s in [(features[i], s) for (i, s) in tfidf_scores]], key=lambda  x: x[1], reverse=True)

        fout.write('%s\n' % video_track[n])
        fout.write(', '.join([ts[0].encode('utf8') for ts in tfidf_scores]) + '\n')
        fout.write(', '.join([str(ts[1]) for ts in tfidf_scores]) + '\n\n')

    fout.close()


def search(query, method=1):
    if method == 1:
        tfidf_matrix = pickle.load(open("tfidf_noise.pkl", "rb"))
        features = pickle.load(open("features_noise.pkl", "rb"))
        video_track = pickle.load(open("video_track_noise.pkl", "rb"))

        tfidf_matrix_frames = pickle.load(open("tfidf_noise_frames.pkl", "rb"))
        features_frames = pickle.load(open("features_noise_frames.pkl", "rb"))
        frame_track = pickle.load(open("frame_noise_track.pkl", "rb"))
    else:
        tfidf_matrix = pickle.load(open("tfidf.pkl", "rb"))
        features = pickle.load(open("features.pkl", "rb"))
        video_track = pickle.load(open("video_track.pkl", "rb"))

        tfidf_matrix_frames = pickle.load(open("tfidf_frames.pkl", "rb"))
        features_frames = pickle.load(open("features_frames.pkl", "rb"))
        frame_track = pickle.load(open("frame_track.pkl", "rb"))

    keywords = query.lower().split()

    video_scores = {}
    for w in keywords:
        try:
            f = features.index(w)
        except Exception as e:
            print 'error:', e
            continue
        
        video_index = tfidf_matrix[:,f].nonzero()[0]
        # print 'the number of found docs:', len(doc_index)

        for d in video_index:
            if d not in video_scores:
                video_scores[d] = {}
            video_scores[d][w] = tfidf_matrix[d, f]

    video_scores = sorted([(d, video_scores[d]) for d in video_scores], key=lambda x : (len(x[1].keys()), sum([x[1][w] for w in x[1]])), reverse=True)
    
    fout = open("searchresults/%s-%d.txt" % ('-'.join(keywords), method), "w")
    for i in range(20):
        d, s = video_scores[i]
        print video_track[d]

        video_hash = video_track[d]
        frame_words = {}
        for n in frame_track:
            # print frame_track[n]
            h, f = frame_track[n]
            if h != video_hash:
                continue
            
            feature_index = tfidf_matrix_frames[n,:].nonzero()[1]
            tokens = [features_frames[idx] for idx in feature_index]

            for w in keywords:
                if w in tokens:
                    if w in frame_words:
                        frame_words[w].append(f)
                    else:
                        frame_words[w] = [f]
        
        fout.write('%s\n' % video_hash)
        for w in frame_words:
            fout.write('%s: %s\n' % (w, ','.join([str(f) for f in frame_words[w]])))
        fout.write('\n')
    fout.close()

def main():
    # our approach
    search('Date getTime', method=1)
    # baseline
    search('Date getTime', method=0)

if __name__ == '__main__':
    main()