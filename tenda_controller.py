"""
In this script we will control Tenda SP9 smart plug over HTTP.
Hence start an HTTP server to give an interface to control the plug.

The plug is controlled by sending a POST request to the plug's IP address.

To get the state: http://IP_ADDRESS:5000/getSta
  Response: {"resp_code":0,"data": {"status": 1 or 0}}
To set the state: http://IP_ADDRESS:5000/setSta
  with json {"status": 1} or {"status": 0}
To get the name: http://IP_ADDRESS:5000/getDetail
  Response: {"resp_code":0,"data":{"rssi":-59,"mac":"50:0f:f5:6e:43:30","time_zone":60,"nick":"Four + Micro-onde","sn":"EB551010207000257","model":"SP9V1.0","sft_ver":"V1.1.0.17(139)_SP9_EU","hrd_ver":"V1.0","mod":1}}
"""

import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import os
import json
import subprocess

def get_plugs(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.loads(f.read())
    else:
        print(f"File '{path}' not found. Running 'tenda_scraper.py' to create it.")
        os.popen("python3 tenda_scraper.py")
        process = subprocess.Popen(["python3", "tenda_scraper.py"])
        process.wait()
        with open(path, "r") as f:
            return json.loads(f.read())

# Plugs path
PLUGS_PATH = "/config/plugs.json"
# Get PLUGS from PLUGS_PATH if it exists
# If it doesn't exist, run "tenda_scraper.py" to create it
PLUGS = get_plugs(path=PLUGS_PATH)
print(f"Found {len(PLUGS)} plugs.")

# LANGUAGE from environment variable
LANGUAGE = os.environ.get("LANGUAGE")
if LANGUAGE is None:
    LANGUAGE = "en"

# The port to listen on
PORT = 80

class TendaPlug:
    """
    Class to control Tenda SP9 smart plug over HTTP.
    """
    def __init__(self, ip, name=None):
        self.ip = ip
        self.name = self.get_name() if name is None else name
        self.state = self.get_state()

    def get_state(self):
        """
        Get the state of the plug.
        """
        # Get the state from HTTP request
        response = requests.get(f"http://{self.ip}:5000/getSta")
        response = response.json()
        state = response["data"]["status"] == 1

        # Return the state
        return state
    
    def set_state(self, state):
        """
        Set the state of the plug.
        """
        # Set the state
        state = int(state)
        response = requests.post(f"http://{self.ip}:5000/setSta", json={"status": state})
        response = response.json()
        if response["resp_code"] != 0:
            raise Exception("Error while setting the state of the plug")
        
        print(f"Plug {self.ip} set to {state} at {time.time()}")
    
    def toggle_state(self):
        """
        Toggle the state of the plug.
        """
        # Get the current state
        state = self.get_state()

        # Toggle the state
        state = not state

        # Set the new state
        self.set_state(state)

        return state

    def get_name(self):
        """
        Get the name of the plug.
        """
        # Get the name from HTTP request
        response = requests.get(f"http://{self.ip}:5000/getDetail")
        response = response.json()
        name = response["data"]["nick"]

        # Return the name
        return name
    

class RequestHandler(BaseHTTPRequestHandler):
    """
    Class to handle HTTP requests.

    We have one page main.html which is the main page.
    We have one API /toggle/IP_ADDRESS which toggles the state of the plug.
    """
    
    def do_GET(self):
        """
        Handle GET requests.
        """
        # Get the path
        path = self.path

        # Serve the main page
        if path == "/":
            self.serve_main_page()

        # Serve the toggle API
        elif path.startswith("/toggle/"):
            self.serve_toggle_api(path)

        # Serve the refresh API
        elif path.startswith("/refresh/"):
            self.serve_refresh_api()

        # Serve the 404 page
        else:
            self.serve_404_page()

    def serve_main_page(self):
        """
        Serve the main page.
        """
        html = ""
        # Get HTML from tenda_controller.html
        with open("tenda_controller.html", "r") as f:
            html = f.read()

        tmp = "<!-- PLUGS -->\n"
        # Create table of plugs
        tmp += "<table><tr><th id=\"plug-name\">Nom</th><th id=\"plug-ip\" class=\"plug-ip\">Adresse IP</th><th id=\"plug-state\">Etat</th></tr>"
        # Add the plugs
        for plug in PLUGS:
            state = "UNKNOWN"
            name = ""
            try:
                plug = TendaPlug(plug['ip'], plug['name'])
                state = plug.state
                if state:
                    state = "ON"
                else:
                    state = "OFF"
                name = plug.name
            except Exception as e:
                print(e)
            tmp += f"""
            <tr class="plug" data-ip="{plug.ip}" data-state="{state}" data-name="{name}">
                <td class="plug-name">{name}</td>
                <td class="plug-ip">{plug.ip}</td>
                <td class="plug-state">{state}</td>
            </tr>
            """
        tmp += "</table>"
        html = html.replace("{{PLUGS}}", tmp)

        js = ""
        # Add the language js file to the HTML
        with open(f"/lang/lang.{LANGUAGE}.js", "r") as f:
            js = f.read()
        # Add 'lang/lang.js' to the HTML
        # This file contains the script to change the language on the fly
        with open("/lang/lang.js", "r") as f:
            js += f.read()
        html = html.replace("{{SCRIPTS}}", js)

        # Send the response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def serve_toggle_api(self, path):
        """
        Serve the toggle API.
        """
        # Get the plug's IP address
        plug_ip = path.split("/toggle/")[1]

        # Il last character is a slash, remove it
        if plug_ip[-1] == "/":
            plug_ip = plug_ip[:-1]

        # Toggle the plug
        plug = TendaPlug(plug_ip)
        state = plug.toggle_state()
        if state:
            state = "ON"
        else:
            state = "OFF"

        # Send the JSON response
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(f'{{"state": "{state}"}}'.encode("utf-8"))

    def serve_refresh_api(self):
        """
        Serve the refresh API.
        """
        # Remove PLUGS_PATH and refresh the plugs
        global PLUGS
        os.remove(PLUGS_PATH)
        print("PLUGS_PATH removed")
        PLUGS = get_plugs(path=PLUGS_PATH)
        print(f"Found {len(PLUGS)} plugs")

        # Send the JSON response
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write('{"status": "ok"}'.encode("utf-8"))

    def serve_404_page(self):
        """
        Serve the 404 page.
        """
        # Create the HTML
        html = """
        <html>
            <head>
                <title>404 Not Found</title>
            </head>
            <body>
                <h1>404 Not Found</h1>
                <p>You will be redirected to the main page in 3 seconds.</p>
            </body>
        </html>
        """
    
        # Send the response
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

        # Wait 3 seconds before redirecting
        time.sleep(3)

        # Redirect to the main page
        self.send_response(301)
        self.send_header("Location", "/")
        self.end_headers()

def main():
    """
    The main function.
    """
    # Create the server
    server = HTTPServer(("", PORT), RequestHandler)

    # Start the server
    print(f"\nStarting server on port {PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
