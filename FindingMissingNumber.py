#to check which elements in the list are missing
def missingNumber(list1):
    list2 = []
    for i in list1:
        if i == list1[-1] and len(list1) != 1:
            break
        elif i+1 not in list1:
            list2.append(i+1)
    print(list2)

list1 = [1,2,3,4,5,7,8,10]
if len(list1) != 0:
    missingNumber(list1)