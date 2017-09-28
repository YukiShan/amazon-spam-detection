import random

fin = open('users.txt', 'r')
# print("The content is: ", fin)
agents=[]
for line in fin.readlines():
	# print("each line is: ", line)
	# print(line[:-1])
	agents.append(line[:-1])

print(agents)