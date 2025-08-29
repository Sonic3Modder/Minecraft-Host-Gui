import json
import os
from time import sleep

# Initialize all variables
version = input("Just to make sure we get this right, what version of Minecraft do you use? ").strip()
type = input("Hello! To get started, please enter the type of server you want to host (vanilla, modded, plugins, proxy, hybrid) or do you use PumpkinMC?: ").strip().lower()

# Initialize config dictionary with minecraft version
config = {
    "minecraft_version": version,
    "server_type": type
}

if type == "vanilla":
    print("Ok, you're good to go. Closing setup in 3 seconds...")
elif type == "modded":
    modded_type = input("What modded server do you host with? (forge, fabric, neoforge, quilt): ").strip().lower()
    if modded_type in ['forge', 'fabric', 'neoforge', 'quilt']:
        config["modded_type"] = modded_type
        print("You're good to go. Closing setup in 3 seconds...")
    else:
        print("Invalid modded server type. Please enter one of the following: forge, fabric, neoforge, quilt.")
        exit(1)
elif type == "plugins":
    plugins_type = input("What plugins server do you host with? (folia, paper, purpur): ").strip().lower()
    if plugins_type in ['folia', 'paper', 'purpur']:
        config["plugins_type"] = plugins_type
        print("You're good to go. Closing setup in 3 seconds...")
    else:
        print("Invalid plugins server type. Please enter one of the following: folia, paper, purpur.")
        exit(1)
elif type == "proxy":
    proxy_type = input("What proxy server do you host with? (bungeecord, waterfall, velocity): ").strip().lower()
    if proxy_type in ['bungeecord', 'waterfall', 'velocity']:
        config["proxy_type"] = proxy_type
        print("You're good to go. Closing setup in 3 seconds...")
    else:
        print("Invalid proxy server type. Please enter one of the following: bungeecord, waterfall, velocity.")
        exit(1)
elif type == "hybrid":
    hybrid_type = input("What hybrid server do you host with? (youer, mohist, magma, arclight): ").strip().lower()
    if hybrid_type in ['youer', 'mohist', 'magma', 'arclight']:
        config["hybrid_type"] = hybrid_type
        print("You're good to go. Closing setup in 3 seconds...")
    else:
        print("Invalid hybrid server type. Please enter one of the following: youer, mohist, magma, arclight.")
        exit(1)
elif type == "pumpkinmc":
    print("Ok, you're good to go. Closing setup in 3 seconds...")
else:
    print("Invalid server type. Please enter one of the following: vanilla, modded, plugins, proxy, hybrid, pumpkinmc.")
    exit(1)

# Write configuration to JSON file
with open('config.json', 'w') as f:
    json.dump(config, f, indent=4)

print("Configuration saved to config.json")
sleep(3)


