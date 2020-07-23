#!/usr/bin/env python3
import argparse
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("action", help="enter action desired [build | start | stop | restart]")
args = parser.parse_args()

if args.action == "build":
    command = "docker build -t devnet-create-2020 .".split()
    subprocess.run(command)
if args.action == "rebuild":
    command = "docker build --no-cache -t devnet-create-2020 .".split()
    subprocess.run(command)
elif args.action == "start":
    command = "docker run --name devnet-create-demo -p 5000:5000 -d devnet-create-2020".split()
    subprocess.run(command)
elif args.action == "stop":
    command = "docker stop devnet-create-demo".split()
    subprocess.run(command)
elif args.action == "restart":
    pass
elif args.action == "delete":
    command = "docker rm devnet_create_2020".split()
    subprocess.run(command)
else:
    print("invalid option")
