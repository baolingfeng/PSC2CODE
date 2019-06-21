from __future__ import division
import cv2
import numpy as np

def crop_border(src, edge_fraction=0.1, min_edge_pix_frac=0.7, max_gap_frac=0.025, max_grad = 1/40):
	'''Detect if picture is in a frame, by iterative flood filling from each edge, 
	then using HoughLinesP to identify long horizontal or vertical lines in the resulting mask.
	We only choose lines that lie within a certain fraction (e.g. 10%) of the edge of the picture,
	Lines need to be composed of a certain (usually large, e.g. 70%) fraction of edge pixels, and
	can only have small gaps (e.g. 2.5% of the height or width of the image).
	Horizontal lines are defined as -max_grad < GRAD < max_grad, vertical lines as -max_grad < 1/GRAD < max_grad
	We only crop the frame if we have detected left, right, top AND bottom lines.'''

	kern = cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
	sides = {'left':0, 'top':1, 'right':2, 'bottom':3}     # rectangles are described by corners [x1, y1, x2, y2]
	src_rect = np.array([0, 0, src.shape[1], src.shape[0]])
	crop_rect= np.array([0, 0, -1, -1])  #coords for image crop: assume right & bottom always negative
	axis2coords = {'vertical': np.array([True, False, True, False]), 'horizontal': np.array([False, True, False, True])}
	axis_type = {'left': 'vertical',   'right':  'vertical',
				 'top':  'horizontal', 'bottom': 'horizontal'}
	flood_points = {'left': [0,0.5], 'right':[1,0.5],'top': [0.5, 0],'bottom': [0.5, 1]} #Starting points for the floodfill for each side
	#given a crop rectangle, provide slice coords for the full image, cut down to the right size depending on the fill edge
	width_lims =  {'left':   lambda crop, x_max: (crop[0], crop[0]+x_max),
				   'right':  lambda crop, x_max: (crop[2]-x_max, crop[2]),
				   'top':    lambda crop, x_max: (crop[0], crop[2]),
				   'bottom': lambda crop, x_max: (crop[0], crop[2])}
	height_lims = {'left':   lambda crop, y_max: (crop[1], crop[3]),
				   'right':  lambda crop, y_max: (crop[1], crop[3]),
				   'top':    lambda crop, y_max: (crop[1], crop[1]+y_max),
				   'bottom': lambda crop, y_max: (crop[3]-y_max,crop[3])}

	cropped = True
	while(cropped):
		cropped = False
		for crop in [{'top':0,'bottom':0},{'left':0,'right':0}]:
			for side in crop: #check both edges before cropping
				x_border_max = int(edge_fraction * (src_rect[2]-src_rect[0] + crop_rect[2]-crop_rect[0]))
				y_border_max = int(edge_fraction * (src_rect[3]-src_rect[1] + crop_rect[3]-crop_rect[1]))
				x_lim = width_lims[side](crop_rect,x_border_max)
				y_lim = height_lims[side](crop_rect,y_border_max)
				flood_region = src[slice(*y_lim), slice(*x_lim), ...]
				h, w = flood_region.shape[:2]
				region_rect = np.array([0,0,w,h])
				flood_point = np.rint((region_rect[2:4] - 1) * flood_points[side]).astype(np.uint32)
				target_axes = axis2coords[axis_type[side]]
				long_dim = np.diff(region_rect[~target_axes])
				minLineLen = int((1.0 - edge_fraction * 2) * long_dim)
				maxLineGap = int(max_gap_frac * long_dim)
				thresh = int(minLineLen * min_edge_pix_frac)

				for flood_param in range(20):
					mask = np.zeros((h+2,w+2,1), np.uint8)
					cv2.floodFill(flood_region, mask, tuple(flood_point),1,(flood_param, flood_param, flood_param),(flood_param, flood_param, flood_param), cv2.FLOODFILL_MASK_ONLY)
					edges = cv2.morphologyEx(mask[1:-1,1:-1,...], cv2.MORPH_GRADIENT, kern, borderType=cv2.BORDER_REFLECT) # find edges in binary image
					lines = cv2.HoughLinesP(edges, rho = 1, theta = np.pi/180, threshold = thresh, minLineLength = minLineLen, maxLineGap = maxLineGap)
					if lines is not None:
						for l in range(lines.shape[1]):
							p = lines[0,l,:] #coords are in the same order as rect: x1, y1, x2, y2
							target_coords = p[target_axes]
							other_coords = p[~target_axes]
							target_diff = np.diff(target_coords)
							other_diff = np.diff(other_coords)
							if (other_diff != 0) and target_diff/other_diff < max_grad:
								line_at = np.rint(np.mean(target_coords)).astype(np.int32)  - region_rect[sides[side]]
								if abs(line_at) > abs(crop[side]):
									crop[side] = line_at

			for side in crop:
				if crop[side] is not 0:
					crop_rect[sides[side]] += crop[side]
					cropped = True
	return crop_rect[0], crop_rect[1], -crop_rect[2]-1, -crop_rect[3]-1