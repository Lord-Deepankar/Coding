def hcf(x,y):
    factors = []
    i = 1
    while (i<=x and i<=y):
        if (x%i==0 and y%i==0):
            factors.append(i)
        i = i+1
    print(factors)
    factors.sort(reverse=True)
    return factors[0]

#main function
z = int(input("enter num..."))
p = int(input("enter num..."))
print(z , p , sep="&")
print("hcf of number is...",hcf(z,p))
