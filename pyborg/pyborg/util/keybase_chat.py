import sys
import json
import subprocess


def main(args):
    "keybase chat util for pyborg testing entrypoint"
    command = ["keybase", "chat", "api", "-m", json.dumps({"method": "list"})]
    x = subprocess.run(command)
    print(x)


if __name__ == "__main__":
    main(sys.argv)
