str1 = "aaabbcccdd"
def splitting(str1):
    list= []
    for i in str1:
        list.append(i)
splitting(str1)


list1=[]
l = len(list1)
def getting_chars(str1, list1):
    for i in range(len(str1)-1):
        if str1[i] != str1[i+1]:
            list1.append(str1[i])
        
# Handle the last character
    if str1[-1] == str1[-2]:
        list1.append(str1[-1])
getting_chars(str1, list1)

list = ['a', 'a', 'a', 'b', 'b', 'c', 'c', 'c', 'd', 'd']
list1 = ['a', 'b', 'c', 'd']
list2 = []

count = 0
j = 0
while True:
    # First count all occurrences
    for i in list:
        if i == list1[j]:
            count += 1
    
    list2.append(count)
    list2.append(list1[j])
    
    # Then remove all occurrences of current character
    i = 0
    while i < len(list):
        if list[i] == list1[j]:
            list.remove(list[i])
        else:
            i += 1
            
    count = 0
    j += 1  
    if j == len(list1):
        break
print(list2)

















