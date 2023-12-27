import pwinput
import time
pas = pwinput.pwinput(prompt='PASSWORD---> ')
check = ""
list1 = [ "0","1","2","3","4","5","6","7","8","9"]
for i in pas:
    if i in list1:
        print("SCANNING!!!")
        
        time.sleep(1)
        print("GOT IT!!!")
        
        time.sleep(0.4)
        print("PUTTING IN REGISTRY")
        check += i
    else:
        print("ALPHANUMERIC PASSWORD")
if check == pas:
    print("THIS IS YOUR PASSWORD------------->",check)