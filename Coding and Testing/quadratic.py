# finding soln if quadratic equations
a = int(input('enter coeff of x**2 --->'))
b = int(input('enter coeff of x --->'))
c = int(input('enter constant --->'))
def quad_soln(a,b,c):
    dis = (b**2 - 4*a*c)
    print(dis)
    if dis<0:
        print('No possible roots in real numbers')
    else:
        num = (-b) - dis**0.5
        num2 = (-b) + dis**0.5
        den = 2*a
        sol1 = num/den
        sol2 = num2 / den
        
        print('solns of your quadratic equation are --->',sol1, ' ',sol2)
quad_soln(a,b,c)

