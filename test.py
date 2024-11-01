str1 = "aaabbcccdd"
l = len(str1)
list1 = []
list2 = []
for i in range(l):
    list1.append(i)
    if str1[i]==str1[i+1] and i<l:
        pass
    elif i==l:
        break
print(list1)