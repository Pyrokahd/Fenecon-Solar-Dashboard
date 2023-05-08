# This is a sample Python script.
import dash
import numpy as np

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Strg+F8 to toggle the breakpoint.

def modlist(mylist):
    mylist.append("new val")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    bla = ["asa fff", "aaa ddd", "aaa eee", "aaa ggg", "aaa zzz"]
    bla2 = [i.split()[-1] for i in bla]

    print(bla)
    modlist(bla)
    print(bla)

    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
