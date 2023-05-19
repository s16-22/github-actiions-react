from fastapi import FastAPI, Body
from fastapi import status, HTTPException
import requests
import uvicorn
import random
import string
import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

PATH_TO_PORTS = os.getenv("PATH_TO_FILES")
PATH_TO_CONFIGS = os.getenv("PATH_TO_CONFIGS")
DNS_SERVER = os.getenv("DNS_SERVER")
HOST_NAME = os.getenv("HOST_NAME")

app = FastAPI()


@app.on_event("startup")
def on_start():
    print("Working")


@app.get("/", response_description="Test the server")
def ping():
    return {
        "message": "Server is working!",
    }


@app.get("/get_kay/")
def create_config():
    key = ""

    unused_file = open(f"{PATH_TO_PORTS}unused_port.txt", "r+")
    used_file = open(f"{PATH_TO_PORTS}used_port.txt", "a+")
    exclude_file = open(f"{PATH_TO_PORTS}exclude.txt", "a+")

    port = unused_file.readline()[:-1]
    all_file = unused_file.read()

    used_file.writelines(port + "\n")
    password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(25))

    unused_file.close()
    used_file.close()

    unused_file = open(f"{PATH_TO_PORTS}unused_port.txt", "w")
    unused_file.writelines(all_file)
    unused_file.close()

    if not (port in used_file.read().split("\n") and port in exclude_file.read().split("\n")):
        new_config = open(f"{PATH_TO_CONFIGS}{port}.txt", "w+")
        config_text = f'{{\n"server_port": {port},\n"password": "{password}",\n"method": "chacha20-ietf-poly1305",\n"mode": "tcp_and_udp"\n}}'
        new_config.write(config_text)
        new_config.close()

        start_command = f"/usr/bin/ss-server -f /tmp/4003.pid -c {PATH_TO_CONFIGS}{port}.txt -t 60 -d {DNS_SERVER} -s {HOST_NAME}"
        result = subprocess.check_output(start_command, shell=True)

        command = f"echo chacha20-ietf-poly1305:{password}@{HOST_NAME}:{port} | base64 --wrap=0 | sed 's/^/ss:\x2F\x2F/' | sed 's/.$//' > {port}.txt"
        result = subprocess.check_output(command, stdin=subprocess.PIPE, shell=True)

        result_file = open(f"{port}.txt", "a+")
        data = result_file.read()
        result_file.close()
        return {
            "key": data
        }

    return {
        "key": "Error"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
