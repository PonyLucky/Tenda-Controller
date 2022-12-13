# Find all SP9 plugs and print their status
# We will loop over all IP addresses in the range
# And try to "IP:5000/getSta" to see if we get a response
# If we do, we will print the status of the plug
# If we don't, we will move on to the next IP address
# 
# Save the IP addreses of the plugs in a file called "plugs.json"


import requests
import json
import os
import multiprocessing

# Get IP address of gateway from environment variable "ROUTER_IP"
# This is the IP address of the router e.g. 192.168.0.1
gateway_ip = os.environ['ROUTER_IP']

if not gateway_ip:
    # If the environment variable is not set, use the following IP address
    gateway_ip = "192.168.1.1"
    print("Using default gateway IP: " + gateway_ip)
    print("If this is not correct, set the environment variable ROUTER_IP to the IP address of your router")

# Loop over all IP addresses in the range
def scan_ip(ip):
    url = 'http://' + ip + ':5000/getSta'
    try:
        print('Trying IP: ' + ip)
        # Try to get the status of the plug
        # Timeout after 0.5 seconds
        r = requests.get(url, timeout=0.5)
        if r.status_code == 200:
            # Fetch "/getDetail" to get the name of the plug
            r = requests.get('http://' + ip + ':5000/getDetail')
            r = r.json()
            name = r['data']['nick']
            # If name starts with "/!\", raise an exception
            if name.startswith('/!\\'):
                print(f"Skipping: {ip} - {name}")
                raise Exception('Plug name starts with "/!\\"')
            print(f"Found: {ip} - {name}")
            # Return the IP address and name of the plug
            return {'ip': ip, 'name': name}
    except:
        return None

# Create a list of all IP addresses in the range
ip_list = []
for i in range(1, 250):
    ip_list.append(gateway_ip[:-1] + str(i))

# Create 20 processes
pool = multiprocessing.Pool(processes=20)
tenda_plugs = pool.map(scan_ip, ip_list)
tenda_plugs = [x for x in tenda_plugs if x is not None]

# Print the IP addresses and names of the plugs
print("\nFound the following plugs:")
for plug in tenda_plugs:
    print(f"IP: {plug['ip']}, Name: {plug['name']}")

# Plugs path
PLUGS_PATH = "/config/plugs.json"

# Save the plugs in a file
with open(PLUGS_PATH, 'w') as f:
    f.write(json.dumps(tenda_plugs, indent=2))
    f.close()
