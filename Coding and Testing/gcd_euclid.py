# finding gcd or highest common divisor through euclidean algorithm
def gcd(a,b):
    while True:
        c = a%b         
        if b%c==0 and c != 0:
            print('the GCD of both',a,'and ',b,'is ',c)
            break
        else:
            t =a
            a = b
            b = c       
a = int(input('enter first number--->'))
b = int(input('enter second number--->'))
gcd(a,b)

