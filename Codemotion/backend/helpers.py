
# converts list of lists to a flat list without duplicates
def flatten(l):
	return list(set([item for sublist in l for item in sublist]))
