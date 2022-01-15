import time
import argparse
import datetime

possible_cases = ["info", "address", "pay", "search", "store", "cart", "list"]

if __name__ == "__main__":
    TIME = datetime.datetime.today().replace(microsecond = 0)
    print(TIME)
    print(type(TIME))
    print()