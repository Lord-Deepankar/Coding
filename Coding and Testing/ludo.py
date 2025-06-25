#ludo game
import random 
print(" red\n","blue\n","yellow\n","green\n")
a = input("enter your color..")
print("let's have a lucky draw for who throws dice first")
print(" red = 1\n", "blue = 2\n" , "yellow = 3\n" ,"green = 4\n")
def draw():
    global b
    b=random.randint(1,4)
    return b
red = 1
blue = 2
yellow = 3
green = 4
while True:
    a = input("wanna throw y/n...")
    if a == "y":
        draw()
        if b==1:
            print("it's RED turn")
            print("the number dice shows is...",random.randint(1,6))
        elif b==2:
            print("it's BLUE turn")
            print("the number dice shows is...",random.randint(1,6))
        elif b==3:
            print("it's YELLOW turn")
            print("the number dice shows is...",random.randint(1,6))
        elif b==4:
            print("it's GREEN turn")
            print("the number dice shows is...",random.randint(1,6))
    else:
        print("game ends as there is no cooperation")
        break
