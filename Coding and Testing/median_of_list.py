def fibonacci(n):
    seq = []
    if n <= 0:
        seq.append(0)
        return seq
    elif n == 1:
        seq.extend([0,1])
        return seq
    elif n == 2 :
        seq.extend([0,1])
        return seq
    else:
        seq.extend([0,1])
        a , b = 0 ,1
        for i in range (n-2):
            c = a+b
            seq.append(c)
            a,b = b , c
        return seq
#main program
n = int ( input("enter the number of fibonacci number you want..."))
print(fibonacci(n))


