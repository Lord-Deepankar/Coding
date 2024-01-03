str1 = 'heguiw nsdhufwe'
str2 = ''
for i in range (len(str1)):
    if str1[i]==' ':
        print(str1[i-1])
        print(str1[i+1])
        str2 += str1[i-1].upper()
        str2 += str1[i]
        str2 += str1[i+1].upper()
    elif i==0 or i==(len(str1)-1):
        str2 += str1[i].upper()
    else:
        str2 += str1[i]





print(str2)        