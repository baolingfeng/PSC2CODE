	red = (0,0,255) #p!
	lightgray = (150,150,150) #p!

	debug = False

	import sys
	input = sys.argv[1]
	output = sys.argv[1]+'-segment'
	fraction = 1./10 # distance (as fraction of smaller dimension) to cluster within

	import cv2
	import numpy as np
	from auxiliary import *

	img = cv2.imread(input)
	demo = img.copy() if True else np.zeros(img.shape, np.uint8) # not a copy?
	if debug: demo += 255
	radius = min(img.shape[0], img.shape[1])*fraction
	corners = [(0,0), (0,img.shape[0]), (img.shape[1],0), (img.shape[1],img.shape[0])]

	# step: detect lines in frame [o/p: lines] | third parameter (of canny) 150
	#############################
	edgy = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 50, 20, apertureSize = 3)
	# cv2.imwrite('step1.jpg', edgy) #p!
	minLineLength, maxLineGap = 100, 10
	lines = cv2.HoughLinesP(edgy, 1, np.pi/180, 100, minLineLength, maxLineGap)
	# print 'lines'
	# for line in lines[0]:
	# 	print line,
	# print

	def drawPoint((x,y), color=white, thickness=4, image=demo):
		cv2.circle(image, (x,y), thickness, color, -1, 8)
		# cv2.circle(image, (x,y), radius, color, 0, 8) # "locator"

	# step: find (end points of) less tilted horizontal or vertical lines [o/p: points]
	##############################################
	points = []
	def slope(p1, p2, axis='x'):
		if axis == 'x':
			return (p1[1]-p2[1])/(float(p1[0])-p2[0])
		else:
			return (p1[0]-p2[0])/(float(p1[1])-p2[1])
	def smallSlope(p1, p2, axis, theta=15): # tilted less than theta
		not_perpendicular = (p1[0]-p2[0] if axis == 'x' else p1[1]-p2[1])
		return not_perpendicular and abs(slope(p1, p2, axis)) < np.sin(theta*np.pi/180)
	if lines is not None:
		for x1,y1,x2,y2 in lines[0]:
			# later: slightly more relaxed angle acceptable?
			along_y = abs(y1-y2) > 0.2*img.shape[0] and smallSlope((x1,y1), (x2,y2), 'y', 11)
			along_x = abs(x1-x2) > 0.2*img.shape[1] and smallSlope((x1,y1), (x2,y2), 'x')
			if along_x or along_y:
				points.extend([(x1,y1), (x2,y2)])
				# cv2.line(demo, (x1,y1), (x2,y2), white, 5) # draw an outline for clarity
				# cv2.line(demo, (x1,y1), (x2,y2), red, 2) #p!
				if debug:
					cv2.line(demo, (x1,y1), (x2,y2), randomColor(), 2)
	# also include corners of entire image
	# for p in corners:
		# drawPoint(p, white, 5)
	# points.extend(corners) # todo | useful?
	# cv2.imwrite('step2.jpg', demo) #p!

	# step: heuristic clustering of points [o/p: clusters]
	############################
	def put(p, g, measure=d2):
		global radius
		if g != []:
			added = False
			index = -1
			for c in g: # cluster, group
				index += 1
				for point in c:
					if measure(p, point) < radius**2:
						g[index].append(p)
						added = True
						break
				if added:
					break
			if not added:
				g.append([p])
		else:
			g.append([p])
	clusters = []
	for p in points:
		put(p, clusters)

	# step: choose representative point of cluster [o/p: ends]
	##############################################
	ends = []
	def closestCorner(p):
		return minima([(corner, d2(p, corner)) for corner in corners])[0]
	# later: handle ambiguous case
	for c in clusters:
		color = randomColor()
		closestCorners = []
		rep = ()
		for p in c:
			# drawPoint(p, color)
			# cv2.circle(demo, p, 9, red, -1, 8) #p!
			# cv2.circle(demo, p, 7, lightgray, -1, 8) #p!
			# cv2.circle(demo, p, 6, red, -1, 8) #p!
			# cv2.circle(demo, p, 5, lightgray, -1, 8) #p!
			co = closestCorner(p)
			if co[0] not in closestCorners:
				closestCorners.append(co[0])
				rep = (p, co[1])
			elif co[1] > rep[1]:
				rep = (p, co[1])
		# if len(closestCorners) != 1:
			# print 'flunked case: multiple corners close to cluster'
		corner = closestCorners[0]
		ends.append(rep[0])
		##if debug or True: # temporary
			##drawPoint(rep[0], white, 7)
		# drawPoint(rep[0], red, 16) #p! added for paper
		# drawPoint(rep[0], red, 10) #p!
	# cv2.imwrite('step3_whole.jpg', demo) #p!
	# cv2.imwrite('step3_crop.jpg', demo) #p!

	# convex hull (ignore)
	def showPolygon(poly, debug=False):
		for i in range(len(poly)):
			p1 = (poly[i-1][0][0],poly[i-1][0][1])
			p2 = (poly[i][0][0],poly[i][0][1])
			if not debug:
				# cv2.line(demo, p1, p2, red, 3) #p!
				cv2.line(demo, p1, p2, randomColor(), 5) #p modified for paper
			print p2, #p
		print #p
	if debug:
		hull = cv2.convexHull(np.array(ends))
		showPolygon(hull)
	# hull = cv2.convexHull(np.array(ends)) #p!
	# showPolygon(hull) #p!
	# cv2.imwrite('step3b.jpg', demo) #p!

	# idea: lines between clusters

	import random
	edges, ignoreList = [], []
	crop = []
	for e1 in ends:
		along_x = [((e1, e2), round(abs(slope(e1, e2)), 2)) for e2 in ends if smallSlope(e1, e2, 'x', 5)]
		if len(along_x) > 1:
			along_x = [minima(along_x)[0]]
			# how about longer lines??
		along_y = [((e1, e2), round(abs(slope(e1, e2, 'y')), 2)) for e2 in ends if smallSlope(e1, e2, 'y', 4)]
		if len(along_y) > 1:
			along_y = [minima(along_y)[0]]
		pairs = [p[0] for p in along_x] + [p[0] for p in along_y] # todo: choose only least tilted ones
		if len(pairs) > 1 or along_y: # todo: review | don't ignore separators!
			edges.append(pairs)
		else:
			ignoreList.append(e1)
			if debug:
				print 'ignored point:', e1
			# drawPoint(e1, gray, 7)
	# remove edges to ignored points
	# and those that aren't the best
	for pairs in edges:
		# print pairs[0][0], '...',
		offset = 0
		for i in range(len(pairs)):
			if pairs[i-offset][1] in ignoreList:
				del pairs[i-offset]
				offset += 1
				continue
			# print pairs[i-offset][1],
		# print
		color, t, count = randomColor(), random.randrange(3), 0
		for pair in pairs:
			ignored = True
			for pairs in edges:
				if flip(pair) in pairs:
					# if debug:
					# cv2.line(demo, pair[0], pair[1], red, 3+t)# #p #3
					if count == 0:
						crop.append(pair[0])
						#print pair[0], '...'
					#print '\t', pair[1]
					count += 1
					ignored = False
			# if ignored:
				# print '\t', pair[1], 'ignored'
		if count == 0:
			if debug:
				print 'ignored point:', pairs[0][0]
			# drawPoint(pairs[0][0], gray, 7)
	# cv2.imwrite('step4.jpg', demo) #p!

	# include corner points if reqd.
	if len(crop) < 3:
		crop.extend(corners)
		# for p in corners:
		# 	drawPoint(p, white, 20)

	hull = cv2.convexHull(np.array(crop))
	#print '\npolygon ...', '\n\t',
	# showPolygon(hull) #p
	# cv2.imwrite('step5a.jpg', demo) #p!
	lx_ly = (hull[0][0][0], hull[0][0][1])
	lx_hy, hx_ly, hx_hy = lx_ly, lx_ly, lx_ly
	for p in hull:
		p = p[0] # issues??
		if p[0]+1 < lx_ly[0]:
			lx_ly = (p[0]+1, lx_ly[1])
			lx_hy = (p[0]+1, lx_hy[1])
		if p[1]+2 < lx_ly[1]:
			lx_ly = (lx_ly[0], p[1]+2)
			hx_ly = (hx_ly[0], p[1]+2)
		if p[0] > hx_hy[0]:
			hx_hy = (p[0], hx_hy[1])
			hx_ly = (p[0], hx_ly[1])
		if p[1] > hx_hy[1]:
			hx_hy = (hx_hy[0], p[1])
			lx_hy = (lx_hy[0], p[1])
	#print '\nrectangle ...', '\n\t',
	def show(poly, debug=False):
		c = randomColor()
		for i in range(len(poly)):
			p1 = (poly[i-1][0][0],poly[i-1][0][1])
			p2 = (poly[i][0][0],poly[i][0][1])
			if not debug:
				cv2.line(demo, p1, p2, red, 3) #p
			print p2,
		print
	# show([[lx_ly], [lx_hy], [hx_hy], [hx_ly]]) #p
	# cv2.imwrite('step5b.jpg', demo) #p!
	demo = demo[lx_ly[1]:hx_hy[1], lx_ly[0]:hx_hy[0]]

	# find separator points
	rectangle = [lx_ly, lx_hy, hx_ly, hx_hy]
	pts, sep_x, sep_y = [], [], []
	for point in crop:
		if minima([(point, d2(point, p)) for p in rectangle])[0][1] > 4 * radius**2:
			pts.append(point)
			#drawPoint(point, white, 20)
	# find separating lines
	count = 0
	for e1 in pts:
		along_x = [(e1, e2) for e2 in pts[count:] if smallSlope(e1, e2, 'x', 1)] #5
		along_y = [(e1, e2) for e2 in pts[count:] if smallSlope(e1, e2, 'y', 1)] #4
		for pair in along_x:
			if pair[0][1] not in sep_y:
				sep_y.append(pair[0][1])
			if pair[1][1] not in sep_y:
				sep_y.append(pair[1][1])
		for pair in along_y:
			if pair[0][0] not in sep_x:
				sep_x.append(pair[0][0])
			if pair[1][0] not in sep_x:
				sep_x.append(pair[1][0])
		count += 1
	# choose few separators
	def filter(l):
		def dist(a, b):
			return (a-b)**2
		clu = []
		for p in l:
			put(p, clu, dist)
		fl = []
		for c in clu:
			fl.append(int(np.mean(c)))
		return fl
	sep_x = [x-lx_ly[0] for x in filter(sep_x)]
	sep_y = [y-lx_ly[1] for y in filter(sep_y)]

	# for x in sep_x: #p!
	# 	cv2.line(demo, (x, 0), (x, sep_y[0]), red, 3) #p!
	# for y in sep_y: #p!
	# 	cv2.line(demo, (0, y), (1184, y), red, 3) #p!
	# cv2.imwrite('step6.jpg', demo) #p!

	def addBorder(image, frac=0.02, type=cv2.BORDER_CONSTANT):
		top = (int) (frac*demo.shape[0])
		bottom = top
		left = (int) (frac*demo.shape[1])
		right = left
		return cv2.copyMakeBorder(image, top, bottom, left, right, type);
	# demo = addBorder(demo) # try fixed size

	def scale(image, multiplier):
		# INTER_NEAREST
		return cv2.resize(image, None, fx=multiplier, fy=multiplier)
	# demo = scale(demo, 2)

	# http://answers.opencv.org/question/30082/detect-and-remove-borders-from-framed-photographs
	#import remove_border as rb#
	# print rb.crop_border(demo)

	# edgy = cv2.Canny(cv2.cvtColor(demo, cv2.COLOR_BGR2GRAY), 50, 20, apertureSize = 3)
	# minLineLength, maxLineGap = 100, 10
	# lines = cv2.HoughLinesP(edgy, 1, np.pi/180, 100, minLineLength, maxLineGap)
	# for x1,y1,x2,y2 in lines[0]:
	# 	p1, p2 = (x1,y1), (x2,y2)
	# 	if d2(p1, p2) > (0.4 * (img.shape[0] if smallSlope(p1, p2, 'y') else img.shape[1])) **2:
	# 		cv2.line(demo, p1, p2, randomColor(), 5)

	# floodfill corners ...
	def removeLines():
		return

	# crop into 3 or fewer segments
	if sep_y:
		# cv2.line(demo, (0,sep_y[0]), (hx_ly[0],sep_y[0]), randomColor(), 2)
		img1 = scale(addBorder(demo[sep_y[-1]:, 0:]), 2)
		cv2.imwrite(output+'1.jpg', img1)
	if sep_x:
		# cv2.line(demo, (sep_x[0],0), (sep_x[0],sep_y[0] if sep_y else lx_hy[1]), randomColor(), 2)
		img2 = scale(addBorder(demo[0:sep_y[-1] if sep_y else hx_hy[1], 0:sep_x[0]]), 2)
		cv2.imwrite(output + ('2.jpg' if sep_y else '1.jpg'), img2)
		img3 = scale(addBorder(demo[0:sep_y[-1] if sep_y else hx_hy[1], sep_x[0]:]), 2)
		cv2.imwrite(output + ('3.jpg' if sep_y else '2.jpg'), img3)
	elif sep_y:
		img2 = scale(addBorder(demo[0:sep_y[-1], 0:]), 2)
		cv2.imwrite(output+'2.jpg', img2)
	else:
		cv2.imwrite(output+'1.jpg', scale(addBorder(demo), 2))

	# cv2.imwrite(output+'.jpg', demo)
