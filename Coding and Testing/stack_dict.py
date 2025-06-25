import time
stack = {}
print(stack)
print("STACK OPERATIONS")
time.sleep(1)
print("1-push")
time.sleep(1)
print("2-pop")
time.sleep(1)
print("3-display")
time.sleep(1)
print("4-exit")
print("LOADING")
for i in range(79):       
        print("=", end="")
        time.sleep(0.1)
while True:
    ch  = int(input("enter choice..."))
    if ch == 1:
        key = input("enter name for key...")
        value = input("enter name to be stored in key...")
        time.sleep(2)
        print("SUCCESFULL INSERTION")
        stack[key]=value
    elif ch == 2 :
        a = max(stack.keys())
        del stack[a]
        time.sleep(0.6)
        print("DELETION COMPLETE")
    elif ch == 3:
        print("GETTING YOUR STACKS")
        time.sleep(2)
        print(stack)
    elif ch == 4:
        print("thank you using  our program ")
        break
    else:
        print("invalid input")