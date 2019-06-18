from scipy.stats import ranksums

x = [548,123,476,216,251]
y = [353,86,404,583,409]

print(ranksums(x, y))