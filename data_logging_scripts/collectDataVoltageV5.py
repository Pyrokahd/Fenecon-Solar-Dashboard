#Abfrage der Messwerte FENECON Wechselrichter via REST API
# Hier mit fester IP Adresse
# Stand 08.05.2023
import os
import time
import requests
import csv
from os.path import exists
from datetime import datetime
#import explorerhat
import numpy as np
import logging
logging.basicConfig(filename='dataCollectionLog.log', encoding='utf-8', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
print("done importing")
logging.info("done importing")

# SETTINGS
LOOP_TIME = 5  # time for one iteration in mins (when values are requestet and saved)
NUMBER_MODULES = 10

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

cell_voltage_urls = []
# battery module 10 (0-9)
# pro modul 14 zellen (0-13)
# Creating API URLs based on Module and Cellnumber
for i in range(NUMBER_MODULES):  #Anzahl der Batteriemodule hier eintragen
    for n in range(14):  # Cells per Module = 14
        if n < 10:
            cellnumber = "0"+str(n)
            #print("Cell=", cellnumber)
        else:
            cellnumber = n
        temp_url = f"http://x:user@192.168.1.229:8084/rest/channel/battery0/Tower0Module{i}Cell0{cellnumber}Voltage"
        temp_header = f"Voltage Module{i} Cell0{cellnumber}"  # in mV
        
        urls.append(temp_url)
        cell_voltage_urls.append(temp_url)
        fields.append(temp_header)


def get_all_cell_mV_values(_cell_voltage_urls):
    """

    :param _cell_voltage_urls: A list with the URLs to all cell mV values
    :return: numpy array containing all cell mV values ordered from cell 0-13 in module 0-9
    """
    all_cell_vals = []
    for url in _cell_voltage_urls:
        response = requests.get(url)
        responseData = response.json()
        entry = responseData["value"]   # the actual value
        # current_module = url[-15:-14]
        all_cell_vals.append(entry)
    return np.asarray(all_cell_vals)


def add_global_min_max_delta_mV(fields, row, all_cell_mV_values):
    """
    Appends new values containing min max and delta mV over all cells to the lists "fields" and "row".
    Because they are appended, the values are added to the original list.
    :param fields:  list containing the column names for the csv
    :param row: list containing the row values for the csv
    :param all_cell_mV_values:  list with the mV value for every cell
    :return:  no return, directly modifies the given lists
    """
    # calculate and append voltage values over all modules (global)
    all_cell_mV_values = np.asarray(all_cell_mV_values)
    global_min = np.min(all_cell_mV_values)
    global_max = np.max(all_cell_mV_values)
    global_delta = global_max - global_min
    fields.append("Global Min")
    fields.append("Global Max")
    fields.append("Global Delta")
    row.append(global_min)
    row.append(global_max)
    row.append(global_delta)


def add_avg_mV_per_module(fields, row, all_cell_mV_values):
    """
    Appends new values, containing the average mV per module measured over all cells within the module,
    to the lists "fields" and "row".
    :param fields: list containing the column names for the csv
    :param row: list containing the row values for the csv
    :param all_cell_mV_values:
    :return:
    """
    # Calculate avg mV value per module
    module_cellmV_lists = []
    # loop über alle werte in 14er schritten
    for i in range(0, len(all_cell_mV_values) - 13, 14):
        cells_per_module = []
        # take values
        for n in range(14):
            cells_per_module.append(all_cell_mV_values[i + n])
        # a list of lists
        # has a list for every module containing cell values
        module_cellmV_lists.append(np.asarray(cells_per_module))

    # Create labels and Avg values
    avg_values_per_module = []
    for l in module_cellmV_lists:
        avg_values_per_module.append(np.average(l, axis=0))
    avg_labels = []
    for i in range(10):
        avg_labels.append(f"Module_{i}")  # from top to bottom in the tower? Seems like it not sure yet

    # add column name and value to fields and rows
    for i in range(len(avg_labels)):
        fields.append(avg_labels[i])
        row.append(avg_values_per_module[i])


file = "fenecon_voltage_data.csv"

# current dir and then into data
data_path = os.path.abspath( os.path.join( os.path.dirname(os.path.realpath(__file__)), "data"))
logging.debug(f"data_path: {data_path}")

filename = os.path.join(data_path, file)  # actually a file path
addHeader = True
run_loop = True

# File is created when the first row is read out (including column names)
# this way its easier to check if data exists (when the file exists) in the dashboard app.py
"""
# add the other field names that would be created from "add_global_min_max_delta_mV" and "add_avg_mV_per_module"
fields.append("Global Min")
fields.append("Global Max")
fields.append("Global Delta")
# range(NUM_MODULES)
for i in range(NUMBER_MODULES):
    fields.append(f"Module_{i}")
# CREATE EMPTY CSV FILE!
with open(filename, "a", newline='') as csvfile:
    writer = csv.writer(csvfile)
    # adding header
    writer.writerow(fields)
"""


reset_fields = fields
addHeader = True


def collection_loop():
    # collect data loop
    while run_loop:
        # Fields need to be resetted because new fields are added in this loop to track module mV min max and delta as well as global
        fields = reset_fields

        start = time.time()
        # explorerhat.light[3].on()  # green lamp on = explorer is reading data
        print("Running start of loop ...")
        logging.info("Running start of loop ...")

        if exists(filename):
            addHeader = False

        row = []

        # Get timestamp
        dt = datetime.now()
        row.append(dt)

        dict_of_all_modul_voltages = {}
        current_module = None
        # Get data from API and write it into a row
        # print("API REST call ...")

        try:
            for url in urls:
                #print("Request with url: ", url)
                response = requests.get(url)
                responseData = response.json()
                entry = responseData["value"]
                row.append(entry)

            all_cell_mV_values = get_all_cell_mV_values(cell_voltage_urls)
            add_global_min_max_delta_mV(fields, row, all_cell_mV_values)
            add_avg_mV_per_module(fields, row, all_cell_mV_values)

            # Add the row to a csv file
            print("adding row ...")
            logging.info("adding row ...")
            with open(filename, "a", newline='') as csvfile:
                writer = csv.writer(csvfile)
                if addHeader:
                    writer.writerow(fields)
                writer.writerow(row)

            # Replace all ',' with ';'
            file = open(filename)
            replacement = file.read().replace(",", ";")
            file.close()
            file = open(filename, "w")
            file.write(replacement)
            file.close()
            # explorerhat.light[3].off()

            print(f"Iteration took: {time.time() - start} s")
            logging.info(f"Iteration took: {time.time() - start} s")

            # Wait for 60 seconds
            # print("waiting ...")
            for minute in range(LOOP_TIME - 1):  # (min-1)
                blink_freq = 2  # in sec  (for accurate results use even numbers that add up to 60)
                blink_count = 60 // blink_freq  # how often do we need to blink with that freq for 1 min
                for _ in range(blink_count):
                    # explorerhat.light.red.on()
                    time.sleep(blink_freq // 2)
                    # explorerhat.light.red.off()
                    time.sleep(blink_freq // 2)

            # explorerhat.light[0].off()
            # explorerhat.light[1].off()
            # explorerhat.light[2].off()
            # explorerhat.light[3].off()
        except Exception as e:
            print(f"Exception occured: {e} \n waiting 5 minutes before trying again...")
            logging.error(f"Exception occured: {e} \n waiting 5 minutes before trying again...")
            print(f"Time: {datetime.now()}")
            logging.debug(f"Time: {datetime.now()}")
            time.sleep(5 * 60)
            print(f"done sleeping, retrying...")
            logging.debug(f"done sleeping, retrying...")
            print()

collection_loop()