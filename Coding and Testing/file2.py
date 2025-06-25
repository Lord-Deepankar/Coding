font= open("test.txt" , "r")
y = font.read()
print(y+'\n')   #printting content of file
font.close()
fin = open("test.txt","r")
list1 = []
list1 = fin.readlines()
print(list1) #assigining content of file to a list
print('\n')
count = 0
for ele in list1 :  #accessing first line
    l = len(ele)
    for j in range(l): #accessing first letter of first line
        if ele[j] == "a":
            count = count + 1
            break
        elif ele[j] == "A": #if a or A then increasing count
            count = count + 1  # breaking the loop 
            break              #after we got first word as a or A
        else:
            break
print("so number of lines starting from a or A are...", count)
fin.close()