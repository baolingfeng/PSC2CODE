import diff_match_patch as dmp
import ocr, re, sys, numpy, json
import cv2
sys.path.append('../../python')
from dbimpl import DBImpl
from setting import *

MIN_INTERVAL = 30

video_hash = sys.argv[1]

db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
sql = 'select title, playlist from videos where hash = ?'
res = db.queryone(sql, video_hash)
video_name = res[0].strip()
video_playlist = res[1].strip()

video_file = video_name + "_" + video_hash

# vnum, fnum, fnumf = int(sys.argv[1]), 1, 1. #4321
# fps = [15.002999, 29.970030, 30, 23.976150, 30, 29.970030, 30.001780, 30, 29.970030, 29.970030, 30, 15, 23.976024, 30, 15, 30, 29.873960, 30, 15, 25.000918, 30][vnum-1]
#... print 'starting with frame', fnum, '\n'

video_file = video_name + "_" + video_hash + ".mp4"
video_path = os.path.join(video_dir, video_playlist, video_file)

if(not os.path.exists(video_path)):
    video_file = video_name + ".mp4"
    video_path = os.path.join(video_dir, video_playlist, video_file)

video = cv2.VideoCapture(video_path)
fps = video.get(cv2.CAP_PROP_FPS)
frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)

print('fps: %f / frame count: %d' % (fps, frame_count))
# fps = 30

fnum, fnumf = 1, 1
# path = '../public/extracts/video'+str(vnum)
path = '../public/extracts/%s' % (video_name + "_" + video_hash)

def compare(known, txt):
	d = dmp.diff_match_patch()
	diffs = d.diff_main(known, txt, False)
	d.diff_cleanupSemantic(diffs)
	l, total, change = [[]], 0, 0
	count, more = 0, 0
	for x in diffs:
		lines = re.split('\n|\\n', x[1])
		more = 1 if len(lines) > 1 else 0
		for p in range(len(lines)):
			part = lines[p]
			total += len(part)
			# is this too aggressive?!
			if len(part)>1: # ignore lookalikes
				if x[0] == 1:
					print '+', part.rstrip(),
					if l[-1] and l[-1][-1] == 'rem':
						l[-1].pop() # big changes?
					else: l[-1].append('add')
					change += len(part)
				elif x[0] == -1:
					print '-', part.rstrip(),
					l[-1].append('rem')
					change += len(part)
				else:
					print '~', part.rstrip(),
					l[-1].append('exc')

				if p != len(lines)-1:
					l.append([])
					print list(set(l[-2])),
					if 'rem' in l[-2] and 'exc' not in l[-2] and 'add' not in l[-2]: count = count-1
					if 'add' in l[-2] and 'exc' not in l[-2] and 'rem' not in l[-2]: count += 1
			if p != len(lines)-1: print
	# if 'exc' not in l[-1] and 'rem' not in l[-1]:
			# count += more
	print 'newlines', count
	return int(round(change*100./total)), d, diffs

output_code = []
output_time = [[0, 0]]
# start and end

buffer = ['']
change_measure, past_measure = [], []
total_frames, unmatched_measure = 0, []
read, th, inc, upd, txt = True, 0, 0, -1, ''
# while fnum < 216000:
while fnum < frame_count:
	s = 3 # read number of segments
	try:
		file = open(path+'/frame%d-segment1.txt' % fnum)
		file.close()
		#if not read: print
		# sys.stdout.write("\r100%\033[K")
		# previous count
		# print '\r%d: frame %d' % (len(buffer)-1, fnum),
		sys.stdout.flush()
		read = True
	except:# IOError:
		if read and fnum > th:
			# print #
			th += 5000
		# sys.stdout.write("\r100%\033[K")
		# previous count
		# print '\r%d: frame %d missing' % (len(buffer)-1, fnum),
		sys.stdout.flush()
		read = False
		#s = 0 #maybe

	# read text from each segment
	for snum in range(s):
		try: file = open(path+'/frame%d-segment%d.txt' % (fnum, snum))
		except: continue
		
		total_frames += 1
		txt = file.read()
		file.close()

		txt = txt.decode('ascii', 'ignore') # todo
		keywords = ocr.strict_check(txt)
		tag = 'main'
		if len(keywords) == 0:
			keywords = ocr.check_for_keywords(txt)
			if(len(keywords) > 0):
				tag = 'maybe'
			else:
				tag = 'unlikely'

		print('tag', tag)
		if txt != '' and tag == 'unlikely':
			f = open(path+'/%s/frame%d-segment%d.txt' % (tag, fnum, snum), 'w') #i
			f.write(txt)
			f.close()
		if txt != '' and tag != 'unlikely':
			if txt == buffer[-1]:
				output_time[-1][1] = (fnum-1)/24 # update end time
				f = open(path+'/%s/frame%d-segment%d.txt' % (tag, fnum, snum), 'w') #i
				# todo: move related files
				# f.write('<pre>' + txt.replace('\n', '<br/>') + '</pre>')
				f.write(txt)
				f.close()
			else:
			# if txt not in buffer:
				merged = False
				for i in range(min(len(buffer), 10)):
					print '<' + str(i+1) + '>'
					pc, d, diffs = compare(buffer[len(buffer)-i-1], txt)
					if pc == 0:
						past_measure.append(i+1)
						output_time[len(buffer)-i-1][1] = (fnum-1)/24
						buffer[len(buffer)-i-1] = txt
						merged = True
						break
					elif pc < 70:
						change_measure.append(pc)
						past_measure.append(i+1)
						inc += 1
						# update end time
						output_time[len(buffer)-i-1][1] = (fnum-1)/24
						# if upd != len(buffer)-i-1:
						#... print (fnum-1)/24, ': updated end time of interval', len(buffer)-i-1
							# upd = len(buffer)-i-1
						print '\nnow'
						# print buffer[len(buffer)-i-1]
						# print 'old'
						print txt
						buffer[len(buffer)-i-1] = txt # todo: account for scrolling
						# if i != 0: # update output code?
							# print 'update output code'
						merged = True
						break
					else:
						unmatched_measure.append(pc)
				if not merged:
					output_code.append([buffer[-1], snum])
					output_time.append([(fnum-1)/24, (fnum-1)/24])
					#... print (fnum-1)/24, ': starting interval', len(buffer), '(segment', str(snum)+')'
					buffer.append(txt)

				# if len(buffer) > 4:
					# todo: print '\nreached buffer capacity'
					# buffer.pop(0)

				# move related files too?
				f = open(path+'/%s/frame%d-segment%d.txt' % (tag, fnum, snum), 'w')
				# if merged: f.write(d.diff_prettyHtml(diffs))
				# else: f.write('<pre>' + txt.replace('\n', '<br/>') + '</pre>')
				f.write(txt)
				f.close()

	# go to next frame
	fnumf += fps
	fnum = int(round(fnumf))
# todo: if not merged
output_code.append([txt, -1])

# but not identical
print '\n\nframes with incremental changes:', inc
if change_measure: print 'average extent of edit (%):', round(numpy.mean(change_measure), 2)
if unmatched_measure: print 'average change on breaking (%):', round(numpy.mean(unmatched_measure), 2)
if past_measure: print 'average depth of successful lookback:', round(numpy.mean(past_measure), 2)
print len(buffer)-1
print '...'
print 'total frames:', total_frames

def eprint(t):
	sys.stderr.write(t)

eprint('{\n')

# width options (4 for 720p, 5 for 540p)
# eprint('"name": "Ruby Essentials for Beginners (Part 01)",\n"width": 4,\n"fps": '+str(fps)+',\n"duration": 1715,\n')
eprint('"name": %s,\n"width": 4,\n"fps": ' % video_name + str(fps) + ',\n"duration": %d,\n' % int(total_frames))

last = -1
li = len(output_time)-1 # last interval index
eprint('"start": [')
for i in range(len(output_time)):
	if i%10 == 0:
		eprint('\n\t')
	# eprint(str(output_time[i][0])+'/'+str(output_time[i][1])+', ')
	# eprint(str(output_time[i][0])+', ')
	#next = output_time[i+1][0] if i < li else 1886
	if last == -1 or output_time[i][0]-output_time[last][0] > MIN_INTERVAL:
		eprint(str(output_time[i][0])+', ')
		#print str(output_time[i][0])+'/'+str(output_time[i][0]-output_time[last][0])
		last = i

eprint('\n],\n')

last = -1
eprint('"code": [\n')
for i in range(len(output_code)):
	if last == -1 or output_time[i][0]-output_time[last][0] > MIN_INTERVAL:
		eprint('\t['+json.dumps(output_code[i][0])+'], \n')
		last = i
	# else:
	# 	eprint('\t,'+json.dumps(output_code[i][0])+'\n\n')

eprint('],\n')

last = -1
eprint('"l": [')
for i in range(len(output_time)):
	if i%10 == 0:
		eprint('\n\t')
	if last == -1 or output_time[i][0]-output_time[last][0] > MIN_INTERVAL:
		eprint('["Java"]'+', ')
		last = i
		# todo

eprint('\n]\n')

eprint('}')
