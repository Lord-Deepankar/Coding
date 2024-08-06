list1 = [ "0", "1" , "0", "1" , "0", "1" , "0", "1" , "0", "1","0","0", "1" , "0", "1" , "0", "1" , "0", "1" , "0", "1","0", "0", "1" , "0", "1" , "0", "1" , "0", "1" , "0", "1","0" ]
str1 = "0100101010101101010"
count = 0
for i in range(len(str1)):
    if str1[i] == list1[i]:
        pass
    else:
        count += 1
print("number of changes req to make the string binary is...", count)
