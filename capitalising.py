str1  = 'my  namayewaa      is deepankar'
str2 = ""
for i in range (len(str1)):
    if str1[i]==' ':
        str2 += str1[i-1].upper()
        str2 += str1[i]
        str2 += str1[i+1].upper()
    elif i==0 or i==(len(str1)-1):
        str2 += str1[i].upper()
    elif str1[i+1]==' ' or str1[i-1]==' ' :
        continue
    elif 2<5:
        str2 += str1[i]
print(str2)
    
