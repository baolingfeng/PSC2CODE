# run from (main) directory containing
# code, images and text folders

import re, HTMLParser, operator
parser = HTMLParser.HTMLParser()

filename = 'image0_optimistic'
sample_tab = "   "

# hocr output conversion
res = [] # distance, code
with open('text/misc/'+filename+'.hocr') as hocr_output:
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

base = min(res, key=operator.itemgetter(0))[0]

# yet to address case when 30,33,62 happens
temp = [r for r in res if r[0] >= base*1.1]
tab = min(temp, key=operator.itemgetter(0))[0]-base

res = [[int(round((r[0]-float(base))/tab)), r[1]] for r in res]
indented_lines = []
for r in res:
	indented = ""
	for i in range(r[0]):
		indented += sample_tab
	indented += r[1]
	indented_lines.append(indented)

for line in indented_lines:
	print line
