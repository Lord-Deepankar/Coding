fin = open("test.txt","r") #opening file
x = fin.read()
print(x)
list1 = x.split()  #spliting file and converting it into list
count = 0
list2 = []
for i in list1 :   #changing lowercase to uppercase 
    z  = i.upper()  #then appending to a new list
    list2.append(z)
str1 = ""            #declaring a new string
for i in list2 :
    str1 += (i+" ")  #converting list2 to string
print("new data is...", str1)    #printing output
fin.close()
