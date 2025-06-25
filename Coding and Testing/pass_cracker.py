def pass_cracker():
    import pwinput
    import time
    pas = pwinput.pwinput(prompt='PASSWORD---> ')
    check = ""
    sym = [ "!","@","#","$","%","&","*","~"]
    alph = [ "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
    list1 = [ "0","1","2","3","4","5","6","7","8","9"]
    for i in pas:
        if i in list1 or i.lower() in alph or i in sym :
            print("SCANNING!!!")
            time.sleep(0.5)
            print("GOT IT!!!")
            time.sleep(0.3)
            print("PUTTING IN REGISTRY")
            check += i
    if check == pas:
        print("THIS IS YOUR PASSWORD--------->",check)
    else:
        print("Invalid password!!!")
pass_cracker()