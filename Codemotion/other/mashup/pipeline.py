debug = True
times = [] #[2724.] #[135, 150, 625, 630, 645, 650, 655, 710, 730, 735]

#video_file = <video>; # fps = 23.976150; # output_path = "preview/resources2"
# video_file = "videos/Angular 2 for Beginners - Tutorial 1.mp4"; fps = 30.002146; output_path = "preview/resources3"
#video_file = "videos/Coding Challenge #52 - Random Walker.mp4"; # fps = 30.001050; # output_path = "preview/resources4"
#video_file = "videos/D3.js tutorial - 1 - Introduction.mp4"; # fps = 1; # output_path = "preview/resources"
#video_file = "videos/wat.mov"; # fps = 1; # output_path = "preview/resources_"
# video_file = "videos/Python Beginner Tutorial 1 (For Absolute Beginners).mp4"; fps = 30.001826; output_path = "preview/resources5"
video_file = "videos/Python Web Scraping Tutorial 2 (Getting Page Source).mp4"; fps = 30.001816; output_path = "preview/resources6"
#video_file = "videos/_"; # fps = 1; # output_path = "preview/resourcesX"

unit_indent = "   "

import cv2, os, re, subprocess, sys
import HTMLParser, operator, codecs
import math
parser = HTMLParser.HTMLParser()

video = cv2.VideoCapture(video_file)

frame = 0
success,image = video.read()
while success:
	frame += 1

	minute = int((frame/fps)/60)
	second = int(math.floor((frame/float(fps))%60))
	print '\rframe #'+str(frame)+' at', '%d:%02d:' % (minute, second),
	
	if round((frame-1) % fps) in [0, 30] or not debug: #or frame/24. in times # first frame each second
		os.system("rm "+output_path+"/frame%d* 2>/dev/null" % frame);

		# extract image frame
		cv2.imwrite(output_path+"/frame%d.ppm" % frame, image)
		cv2.imwrite(output_path+"/frame%d.jpg" % frame, image)
		
		# get segment images
		arguments = "0.33 500 40000 "+output_path+"/frame" + str(frame) + ".ppm" + " "+output_path+"/frame" + str(frame)
		seg_cmd = "./segment/code/segment " + arguments
		c = int(re.search(r'\d+', subprocess.check_output([seg_cmd], shell=True)).group())
		
		print "crunching...",
		sys.stdout.flush() # show incomplete line
		
		# run ocr and fix spacing
		for i in range(c):
			image = output_path+"/frame%d_segment%d.ppm " % (frame, i)
			output = output_path+"/frame%d_segment%d" % (frame, i)
			ocr_command = "tesseract " + image+output + " config.txt 2>/dev/null"
			os.system(ocr_command)

			# hocr output conversion
			res = [] # distance, code
			with open(output_path+"/frame%d_segment%d.hocr" % (frame, i)) as hocr_output:
				for line in hocr_output:
					# find x-coordinate of upper left corner
					location = re.search(r'(?<=bbox ).+?(?=\s)', line)
					
					# ignore tags and extract code
					text = re.sub(r'<[^>]*>', '', line)
					# fix special characters
					text = text.strip().decode("utf8")
					# dumb down smark quotes
					text = text.replace(u'\u201c', '"').replace(u'\u201d', '"')
					# decode HTML-safe sequences
					text = parser.unescape(text)
					
					# sanity check for location and extract
					is_text_empty = (text == re.search(r'\w*', line).group(0))
					if location != None and not is_text_empty:
						res.append([int(location.group(0)), text])

			# spacing adjustment

			if len(res) == 0:
				os.system("rm "+output_path+"/frame%d_segment%d.*" % (frame, i))
				if i == c-1:
					if subprocess.call("ls "+output_path+"/frame%d_segment*.ppm 1>/dev/null 2>/dev/null" % frame, shell=True) != 0:
						os.system("echo 0 > "+output_path+"/frame"+str(frame)+".txt")
						# os.system("mv "+output_path+"/frame%d.ppm "+output_path+"/frame%d_del.ppm" % (frame, frame))

			else:
				cv2.imwrite(output_path+"/frame%d_segment%d.jpg" % (frame, i), cv2.imread(output_path+"/frame%d_segment%d.ppm" % (frame, i)))

				os.system("rm "+output_path+"/frame%d_segment%d.hocr" % (frame, i))
				base = min(res, key=operator.itemgetter(0))[0]

				# yet to address case when 30,33,62 happens
				temp = [r for r in res if r[0] > base*1.09] # when base = 0
				if len(temp) == 0:
					lines = ""
					for r in res:
						lines += r[1] + "\n"

					# _dis[placed]
					f = codecs.open(output_path+"/frame%d_segment%d.txt" % (frame, i), 'w', 'utf-8') # _check.txt
					f.write(lines)

				else:
					tab = min(temp, key=operator.itemgetter(0))[0]-base

					res = [[int(round((r[0]-float(base))/tab)), r[1]] for r in res]
					indented_lines = ""
					for r in res:
						indented = ""
						for x in range(r[0]):
							indented += unit_indent
						indented += r[1]
						indented_lines += indented + "\n"

					# _ind[ented]
					f = codecs.open(output_path+"/frame%d_segment%d.txt" % (frame, i), 'w', 'utf-8')
					f.write(indented_lines)

		write_max_segments = "echo "+str(i)+" > "+output_path+"/frame"+str(frame)+".txt"
		os.system("rm "+output_path+"/*.ppm; if [ ! -f "+output_path+"/frame"+str(frame)+".txt ]; then "+write_max_segments+"; fi")
		print "done"

	success,image = video.read()
# end of while

# find outputs -empty | sed 's/^/rm /g'
# find outputs -empty | sed 's/.txt/.ppm/g' | sed 's/^/rm /g'

# find outputs -size -3c -delete
