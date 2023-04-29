#Abfrage der Messwerte FENECON Wechselrichter via REST API
# Hier mit fester IP Adresse
# Stand 19.3.2023

import time
import requests
import csv
from os.path import exists
from datetime import datetime
import explorerhat
import numpy as np
print("done importing")

# SETTINGS
LOOP_TIME = 5  # time for one iteration in mins (when values are requestet and saved)

# https://docs.fenecon.de/de/_/latest/fems/glossar.html
urls = ["http://x:user@192.168.1.229:8084/rest/channel/_sum/GridActivePower",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/GridBuyActiveEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/GridSellActiveEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/EssSoc",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/EssActivePower",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/EssActiveChargeEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/EssActiveDischargeEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/EssDcChargeEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/EssDcDischargeEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/EssCapacity",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ProductionActivePower",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ProductionAcActivePower",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ProductionDcActualPower",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ProductionActiveEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ProductionAcActiveEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ProductionDcActiveEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ConsumptionActivePower",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/ConsumptionActiveEnergy",
        "http://x:user@192.168.1.229:8084/rest/channel/_sum/State"]

fields = ['Zeitstempel',
          'Netzbezug(positiv)/Einspeisung(negativ) [W]',
          'Netzbezug Energie [Wh]',
          'Netzeinspeisung Energie [Wh]',
          'Ladezustand [%]',
          'Beladeleistung(negativ)/Entladeleistung(positiv) [W]',
          'Beladeenergie [Wh]',
          'Entladeenergie [Wh].',
          'Beladeenergie der Batterie [Wh]',
          'Entladeenergie der Batterie [Wh]',
          'Nenn-Batteriekapazität [Wh]',
          'Erzeugungsleistung [W]',
          'Leistung der AC-Erzeuger [W]',
          'Leistung der DC-Erzeuger [W]',
          'Erzeugte Energie [Wh]',
          'Energie der AC-Erzeuger [Wh]',
          'Energie der DC-Erzeuger [Wh]',
          'Summenleistung aller Verbraucher [W]',
          'Summenenergie aller Verbraucher [Wh]',
          'Status des Systems'
          
          
          ]

# battery module 10 (0-9)
# pro modul 14 zellen (0-13)
# Creating API URLs based on Module and Cellnumber
for i in range(10):  #Anzahl der Batteriemodule hier eintragen
    for n in range(14):  # Cells per Module = 14
        if n < 10:
            cellnumber = "0"+str(n)
            print("Cell=",cellnumber)
        else:
            cellnumber = n
        temp_url = f"http://x:user@192.168.1.229:8084/rest/channel/battery0/Tower0Module{i}Cell0{cellnumber}Voltage"
        temp_header = f"Voltage Module{i} Cell0{cellnumber}"  # in mV
        
        urls.append(temp_url)
        fields.append(temp_header)

filename = "March23_fenecon_voltage_data.csv"
addHeader = True
run_loop = True
#i = 0

reset_fields = fields


# collect data loop
while run_loop:
    # Fields need to be resetted because new fields are added in this loop to track module mV min max and delta as well as global
    fields = reset_fields
    
    start = time.time()
    explorerhat.light[3].on()  # green lamp on = explorer is reading data
    print("Running start of loop ...")
    #i=i+1
    if exists(filename):
        addHeader = False

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
            print("Request with url: ", url)
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
        
        # Calculate min, max and delta (difference) within each modul and across all modules
        all_values = []
        for key,values in dict_of_all_modul_voltages.items():
            
            # save all values in single list for global min/max/delta
            for v in values:
                all_values.append(v)
            # min for current module
            fields.append(f"Module{key} Min")  
            min_val = np.min(np.asarray(values))
            row.append(min_val)
            # max for current module
            fields.append(f"Module{key} Max")  # add column name
            max_val = np.max(np.asarray(values))
            row.append(max_val)  # add value
            # delta for current module
            fields.append(f"Module{key} Delta")  
            delta_val = max_val-min_val
            row.append(delta_val)
        
        # calculate and append voltage values over all modules (global)
        all_values = np.asarray(all_values)
        global_min = np.min(all_values)
        global_max = np.max(all_values)
        global_delta = global_max-global_min
        fields.append("Global Min")
        fields.append("Global Max")
        fields.append("Global Delta")
        row.append(global_min)
        row.append(global_max)
        row.append(global_delta)
        
        # Add the row to a csv file
        print("adding row ...")
        with open(filename, "a", newline='') as csvfile:
            writer = csv.writer(csvfile)
            if addHeader:
                writer.writerow(fields)
            writer.writerow(row)

        # Replace all ',' with ';'
        #print("replacing ...")
        file = open(filename)
        replacement = file.read().replace(",", ";")
        file.close()
        file = open(filename, "w")
        file.write(replacement)
        file.close()
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
    except Exception as e:
        print(f"Exception occured: {e} \n waiting 5 minutes before trying again...")
        print(f"Time: {datetime.now()}")
        time.sleep(5*60)
        print(f"done sleeping, retrying...")
        print()

