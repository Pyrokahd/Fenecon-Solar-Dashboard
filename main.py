# This is a sample Python script.
import dash
import numpy as np
import time
import os
import csv
# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Strg+F8 to toggle the breakpoint.

def modlist(mylist):
    mylist.append("new val")

def change(inp):
    global globalstuff
    globalstuff = inp

globalstuff = "hi"
# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    print(globalstuff)
    print("change")
    change("test")
    print(globalstuff)

    file = "fenecon_voltage_data.txt"
    #data_path = os.path.abspath(os.path.join(os.getcwd(), "..", "data"))  # current dir one back and then into data
    data_path = os.path.join(os.getcwd(), "data")
    print(data_path)
    filename = os.path.join(data_path, file)

    #print("test creating file")
    #f = open(filename, "a")
    #f.write("This textfile is created from within a docker container")
    #f.close()
    #time.sleep(25)
    #print_hi('PyCharm')


