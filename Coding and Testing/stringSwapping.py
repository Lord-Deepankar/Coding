def strong(x):
    integer_value = x
    tuple1 = tuple(int(digit) for digit in str(integer_value))
    sum1 = 1
    pic = 1
    job = 1
    for i in range(1,tuple1[0]+1) :
        sum1 = sum1*i
    for j in range(1,tuple1[1]+1):
        pic = pic*j
    for k in range(1,tuple1[2]+1):
        job = job*k
    return sum1+job+pic

num1  = int(input("enter number ..."))
if  num1 ==strong(num1) :
    print("strong number")
else:
    print("not a strong number")
    
