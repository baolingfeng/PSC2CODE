import os,pandas as pd
from collections import OrderedDict

def listDirs(folder):
    return [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

def listFiles(folder):
    return [d for d in os.listdir(folder) if not os.path.isdir(os.path.join(folder, d))]


basedir=r"E:\karim\Code\Clusters"
lsDirs = listDirs(basedir)
lsDirs.sort(key=int)

lstRows=[]
for f in lsDirs:
    dRow = OrderedDict()
    dRow['Original'] = len(listFiles(basedir + '/' + f))
    # try:
    #     dRow['Deleted_Dup'] = len(listFiles(basedir + '/' + f + '/Deleted_Dup'))
    # except FileNotFoundError:
    #     print("Deleted_Dup for %s is not found" % f)
    #     break
    lstRows.append(dRow)

df = pd.DataFrame(lstRows)
df['delta'] = df['Original']

print("Table:")
print(df)

print("Original:")
print("\tTotal: %d" % df['Original'].sum())
print("\tMax: %d" % df['Original'].max())
print("\tMin: %d" % df['Original'].min())
print("\tAvg: %d" % df['Original'].mean())


