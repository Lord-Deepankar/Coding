import sys
import os
import subprocess


def main():
    
    # Wait for user input
    for i in range(0,20):
        sys.stdout.write("$ ")
        command = input() 
        list1 = command.split(" ")       
        if command == "exit 0":
            break
        elif list1[0] == "echo":            
            str1 = ""
            for i in range(1,len(list1)):
                str1 = str1 + list1[i] + " "
            print(str1)
        elif list1[0] == "type":
            if list1[1] in ["echo","type","exit"]:
                print(list1[1],"is a shell builtin")
            elif list1[1] == "cat" and os.path.isfile("/bin/cat"):
                print(list1[1],"is /bin/cat")
            else:
                new_path = os.environ.get("PATH")
                paths = new_path.split(":")
                found = False
                for directories in paths:
                    full_path = directories + "/" + list1[1]
                    if os.path.isfile(full_path) == True and os.access(full_path , os.X_OK):
                        print(list1[1],"is" ,full_path)
                        found = True
                        break
                if found == False:
                    print(f"{list1[1]}: not found")
        elif list1[0] == "pwd":
            print(os.getcwd())
        else:# list1[0] == "custom_exe_1234":


            new_path = os.environ.get("PATH")
            paths = new_path.split(":")
            found = False      
            for dir in paths:
                f_path = os.path.join(dir,list1[0])
                if os.path.isfile(f_path)==True and os.access(f_path , os.X_OK):
                    found = True
                    try:
                        result = subprocess.run(list1, capture_output=True, text=True)
                        print(result.stdout, end="")  # print the program's output
                        print(result.stderr, end="")



                    except Exception as e:
                        print(f"Not found {e}")   
            if found == False:
                print(f"{command}: command not found")


                    
                        


if __name__ == "__main__":
    main()

