import time


def print_phase(name: str):
    print("-" * 50)
    print(f"\033[94m[{name}]\033[0m")
    time.sleep(0.5)
