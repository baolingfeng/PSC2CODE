# stackoverflow.com/questions/3537170
import itertools, operator
def minima(lol, f=operator.itemgetter(1)):
	return list(next(itertools.groupby(sorted(lol, key=f), key=f))[1])

white = (255,255,255)
gray = (50,50,50)

import random as r
def randomColor():
	return (r.randrange(255),r.randrange(255),r.randrange(255))

def d2(p1, p2):
	return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def flip(pair):
	return (pair[1], pair[0])

''' 
maybe: compare speed

# (Non-probabilistic) Hough Transform
lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
for rho,theta in lines[0]:
	a, b = np.cos(theta), np.sin(theta)
	x0, y0 = a*rho, b*rho
	x1, y1 = int(x0 + 1000*(-b)), int(y0 + 1000*(a))
	x2, y2 = int(x0 - 1000*(-b)), int(y0 - 1000*(a))
	# does the line need to be end-to-end?
	cv2.line(img, (x1,y1), (x2,y2), (0,0,255), 2)
'''