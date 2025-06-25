def total_primes(num1):
    def prime(num):
        count =0 
        for i in range (2,num):
            if num%i == 0:
                count +=1
        if count <1:
            return True



    list1 = []
    for i in range (1,num1):
        count = 0
        if prime(i) == True:
            count +=1
            list1.append(i)
        else:
            pass

    print(list1," These are numbers of prime number till ",num1," total ",len(list1)," prime numbers.")

num1 = int(input("ENTER THE NUMBER TILL WHICH YOU WANT NUMBER OF PRIME NUMBERS...."))
total_primes(num1)
