import time
stack = []
def stack_program():
    print("STACK OPTIONS")
    time.sleep(1)
    print("1-push")
    time.sleep(1)
    print("2-pop")
    time.sleep(1)
    print("3-peek")
    time.sleep(1)
    print("4-display")
    time.sleep(1)
    print("5-exit")
    time.sleep(1)
    print("Loading")
    for i in range(75):
        print("#", end="")
        time.sleep(0.05)
    while True:
        your_choice = int(input("enter your desired choice..."))
        
        
        if your_choice==1:
            val = int(input("enter value you want to push.."))
            time.sleep(2)
            print("SUCCESFULL operation!!!")
            stack.append(val)
            
            
        elif your_choice==2:
            L = len(stack)
            if L==0:
                print("stack underflow error")
            else:
                time.sleep(2)
                stack.pop()
         
        elif your_choice==3:
            a = input("enter diplay type...indexing or full stack display...")
            if a =="indexing":
                val3 = input("enter value you want to see..")
                time.sleep(1)
                for i in range (len(stack)):
                    if stack[i]==val3:
                        time.sleep(2)
                        print(i,"is the index value of",stack[i])
            elif a=="full stack display":
                time.sleep(2)
                print("this is your stack...",stack)
        
        elif your_choice == 4:
            print("GETTING YOUR STACKS READY...")
            time.sleep(0.5)
            print(stack)
                
                
        elif your_choice==5:
            print("Thank you for uing this pogram of stack")
            break
        else:
            print("invalid input!!#%$!@&")
            break
stack_program()     #calling the function
