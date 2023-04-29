# Abfrage der Messwerte FENECON Wechselrichter via REST API
# Hier mit fester IP Adresse
# Stand 19.3.2023

# Dieses program dient dazu die durchschnittlichen mV pro Batterie Modul zu printen


import time
import requests
import csv
from os.path import exists
from datetime import datetime
# import explorerhat
import numpy as np
print("done importing")

urls = []
fields = []
NUM_MODULES = 10

# battery module 10 (0-9)
# pro modul 14 zellen (0-13)
# Creating API URLs based on Module and Cellnumber
for i in range(NUM_MODULES):  #Anzahl der Batteriemodule hier eintragen
    for n in range(14):  # Cells per Module = 14
        if n < 10:
            cellnumber = "0"+str(n)
            #print("Cell=",cellnumber)
        else:
            cellnumber = n
        temp_url = f"http://x:user@192.168.1.229:8084/rest/channel/battery0/Tower0Module{i}Cell0{cellnumber}Voltage"
        temp_header = f"Voltage Module{i} Cell0{cellnumber}"  # in mV
        
        urls.append(temp_url)
        fields.append(temp_header)

run_loop = True
#i = 0

# collect data loop
while run_loop:

    start = time.time()
    #explorerhat.light[3].on()
    #print("Running start of loop ...")

    row = []
    # Get timestamp
    dt = datetime.now()
    row.append(dt)

    dict_of_all_modul_voltages = {}
    current_module = None
    # Get data from API and write it into a row
    #print("API REST call ...")

    try:
        for url in urls:
            #print("Request with url: ", url)
            response = requests.get(url)
            responseData = response.json()
            entry = responseData["value"]
            row.append(entry)

            # get voltage per module and cell
            # if url ends with Voltage
            if url[-7:] == "Voltage":
                current_module = url[-15:-14]  # modul is char at index 15 from behind. Only if max modul number is 9!
                # create entry for module if not existent
                if not current_module in dict_of_all_modul_voltages:
                    dict_of_all_modul_voltages[str(current_module)] = []
                # append voltage value to list within dict
                dict_of_all_modul_voltages[str(current_module)].append(entry)

        # Dict that contains a list of the 14 cell values in mV for every module (key = modulenumber, value = list)
        #print(dict_of_all_modul_voltages)

        avg_mV_per_module = {}
        # Calculate avg mV per mdoule
        all_values = []
        for key, values in dict_of_all_modul_voltages.items():

            # save all values in single list for global min/max/delta
            # to calculate Voltage over all module and cells
            for v in values:
                all_values.append(v)

            # AVERAGE PER MODULE FOR CURRENT MESSUNG
            avg_mV_per_module[f"Mod-{key}"] = round(np.mean(np.asarray(values)), 2)


        print(dt)
        returnstring = ""
        returnstring2 = ""
        highest_mV = 0
        for k,v in avg_mV_per_module.items():
            returnstring += f"{k}: {v}[mV]  |  "
            if v > highest_mV:
                highest_mV = v

        stringparts = returnstring.split("|")
        n = -1
        for v in avg_mV_per_module.values():
            n += 1
            #print(len(stringparts))
            #print(stringparts)
            value_difference = round(highest_mV - v, 2)

            sign = "-"
            if value_difference <= 0:
                sign = "+"
            mV_difference_string = f"{sign}{value_difference}[mV]"

            # set space buffer to align outputstring
            buffer_length = len(stringparts[n]) - len(mV_difference_string) - 2
            buffer = ""
            for i in range(buffer_length):
                buffer += " "

            returnstring2 += f"{buffer}{mV_difference_string}  |"

        print(returnstring)
        print(returnstring2)

        with open("mv_log.txt", mode="a") as f:
            f.write(str(dt))
            f.write("\n")
            f.write(returnstring)
            f.write("\n")
            f.write(returnstring2)
            f.write("\n")

        """
        explorerhat.light[3].off()
        
        print(f"Iteration took: {time.time() - start} s")

        # Wait for 60 seconds
        #print("waiting ...")
        for minute in range(LOOP_TIME-1):  #(min-1)
            blink_freq = 2 # in sec  (for accurate results use even numbers that add up to 60)
            blink_count =  60 // blink_freq  # how often do we need to blink with that freq for 1 min
            for _ in range(blink_count):
                explorerhat.light.red.on()
                time.sleep(blink_freq//2)
                explorerhat.light.red.off()
                time.sleep(blink_freq//2)
        
        explorerhat.light[0].off()
        explorerhat.light[1].off()
        explorerhat.light[2].off()
        explorerhat.light[3].off()
        """
    except Exception as e:
        print(f"Exception occured: {e} \n waiting 2 minutes before trying again...")
        print(f"Time: {datetime.now()}")
        time.sleep(2*60)
        print(f"done sleeping, retrying...")
        print()
