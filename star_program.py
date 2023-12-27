import time
n = int(input("enter number of rows of stars you want..."))
for i in range(1,(n+1)):
    print(n*" " + i*"* ")
    time.sleep(1)
    n=n-1
    
