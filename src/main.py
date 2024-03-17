import argparse
import importlib
import os
import time

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yml")
modules = []

parser = argparse.ArgumentParser(description="Yami Home Server")
parser.add_argument("-m", "--module", help="The module you would like to use")
args = parser.parse_args()


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def loadModules():
    modPath = os.path.join(os.path.dirname(__file__), "modules")
    for module in os.listdir(modPath):
        if module.endswith(".py"):
            modules.append(module[:-3])


def getVersion():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config["version"]


def getConfig(item):
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config[item]


def getOperatingSystem():
    if os.name == "nt":
        return "Windows"
    elif os.name == "posix":
        return "Linux"
    else:
        return "Unknown"


def checkDependencies(deps):
    pipFreeze = os.popen("pip freeze").read()
    for dep in deps:
        if dep not in pipFreeze:
            print(f"Missing dependency: {dep}, installing...")
            os.system(f"pip install {dep}")


def main():
    clear()
    loadModules()
    if args.module:
        if args.module not in modules:
            print("Invalid module name.")
            time.sleep(1)
            main()
        else:
            module = importlib.import_module(f"modules.{args.module}")
            module.main()
    else:
        operating_system = getOperatingSystem()
        print(
            f"Yami Home Server [Version {getVersion()}] is running on [{operating_system}]"
        )
        if len(modules) == 0:
            print("No modules found.")
            time.sleep(1)
            exit()
        print("Available modules: ")
        for module in modules:
            print(f" - {module}")
        module_name = input("Which module would you like to use? ")
        if module_name in modules:
            module = importlib.import_module(f"modules.{module_name}")
            clear()
            name = module.info["name"]
            description = module.info["description"]
            author = module.info["author"]
            version = module.info["version"]
            dependencies = module.info["dependencies"]

            areyouSure = input(
                f"Are you sure you want to use the {name} module? (y/n) "
            )

            if areyouSure.lower() != "y":
                main()

            print(f"Module: {name}")
            print(f"Description: {description}")
            print(f"Author: {author}")
            print(f"Version: {version}")
            checkDependencies(dependencies)

            module.main()
        else:
            print("Invalid module name.")
            time.sleep(1)
            main()


if __name__ == "__main__":
    main()
