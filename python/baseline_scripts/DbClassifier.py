import sqlite3
import os
from shutil import copyfile


conn = sqlite3.connect('Classifier.db')
c = conn.cursor()
q="SELECT video,frame from classifier WHERE class=2 and class2=2"


c.execute(q)
names = list(map(lambda x: x[0], c.description))
print(names)
rows = c.fetchall()
print(len(rows))
# print("(1,1)=",len(rows))
# total=len(rows)
# q="select video, frame from classifier WHERE class=1 and class2=2"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
# print("(1,2)=",len(rows))
# total+=len(rows)
# q="select video, frame from classifier WHERE class=1 and class2=3"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
#
# print("(1,3)=",len(rows))
# total+=len(rows)
# q="select video, frame from classifier WHERE class=2 and class2=1"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
#
# print("(2,1)=",len(rows))
# total+=len(rows)
# q="select video, frame from classifier WHERE class=3 and class2=1"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
#
# print("(3,1)=",len(rows))
# total+=len(rows)
# q="select video, frame from classifier WHERE class=2 and class2=2"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
#
# print("(2,2)=",len(rows))
# total+=len(rows)
# q="select video, frame from classifier WHERE class=2 and class2=3"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
#
# print("(2,3)=",len(rows))
# total+=len(rows)
# q="select video, frame from classifier WHERE class=3 and class2=2"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
#
# print("(3,2)=",len(rows))
# total+=len(rows)
# q="select video, frame from classifier WHERE class=3 and class2=3"
#
#
# c.execute(q)
# names = list(map(lambda x: x[0], c.description))
# print(names)
# rows = c.fetchall()
# print("(3,3)=",len(rows))
# total+=len(rows)
# print("Total=",total)
# print("missing,",23658-total)

L = []
D = {}
for row in rows:
    frame = row[1]
    frame = ("0" * (3 - len(str(frame)))) + str(frame)
#    print(row[0],frame)
    if not os.path.isfile("E:/karim/static/" + str(row[0]) + '/Deleted_Dup/img' + frame + ".png"):
        print(frame)

    L.append(str(row[0]) + "_img" + frame)
    if str(row[0]) + "_img" + frame in D.keys():
        D[str(row[0]) + "_img" + frame] += 1
    else:
        D[str(row[0]) + "_img" + frame] = 1
    src = "E:/karim/static/" + str(row[0]) + '/Deleted_Dup/img' + frame + ".png"
    dest = "E:/karim/PartiallyVisible/" + str(row[0]) + "_img" + frame + ".png"
    copyfile(src, dest)

c.close()

print("files: \t\t\t" + str(len(rows)))
if len(L) != len(set(L)):
    print("unique files: \t" + str(len(set(L))))
    print("duplicates: \t" + str(len(L) - len(set(L))) + " duplicates")


print(D)

for key in D:
    if D[key] > 1:
        print(key, D[key])