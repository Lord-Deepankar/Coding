# Path to the hosts file
hosts_path = r"C:/Windows/System32/drivers/etc/hosts"  # For Windows
# hosts_path = "/etc/hosts"  # For Unix-based systems

# Websites to block
website_list = []
a = int(input("entr no of websites you want to block..."))
print(a)
for i in range(0,a):
    b = input('enter websites with only www.xyz.com format not https...')
    website_list.append(b)

# Redirect IP address
redirect_ip = "127.0.0.1"

# Open the hosts file and add the blocked websites
fin = open(hosts_path,"a")
for website in website_list:
    fin.write(redirect_ip + " " + website + "\n")

print("Websites blocked successfully.")
fin.close()
