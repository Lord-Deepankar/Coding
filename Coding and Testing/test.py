import sys

def binary(number):
    binary_num = bin(number)[2:]
    return binary_num

num = int(input("enter num-: "))
n = 0
while n < num:

    if 2**n == num and num%2==0:
        print(f"num == {n}")    
        break
    else:
        pass
    n += 1






while True :
    try:
        number = int(input("enter your number for checking-: "))
        if number%2==0 or number==1:
            bin_list = [ int(i) for i in binary(number) ]
            print(bin_list)
            if sum(bin_list) == 1:
                binary_num = binary(number)
                cnt = binary_num.count('0')
                print(f"{number} can be expressed as 2^{cnt}")
            else:
                print(f"{number} can't have this in 2^X format")
        else:
            print(f"{number} can't have this in 2^X format")

    except Exception as KeyboardInterrupt:
        print("KeyboardInterrupt......Exiting.....")
        break
