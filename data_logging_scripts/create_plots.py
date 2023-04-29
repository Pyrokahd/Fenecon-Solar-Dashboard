import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.dates as mdates

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Plot Voltage for fenecon data.')

# Optional argument
parser.add_argument('--file', type=str, default="March23_fenecon_voltage_data.csv",
                    help='The csv file to be loaded. Only one can be loaded.'
                         ' Default file is March23_fenecon_voltage_data.csv')
args = parser.parse_args()

current_path = os.getcwd()
save_path = current_path
file_path = os.path.join(current_path, args.file)

# load file as data frame
df = pd.read_csv(file_path, sep=";")
df['Zeitstempel'] = pd.to_datetime(df['Zeitstempel'],
                                   format='%Y-%m-%d %H:%M:%S.%f')  # Year month day hour minute second microseconds

# Get all cell names to retrieve relevant columns from data frame
all_cells = []
for m in range(10):
    for c in range(14):
        if c < 10:
            all_cells.append(f"Voltage Module{m} Cell00{c}")
        else:
            all_cells.append(f"Voltage Module{m} Cell0{c}")

# Save all columns from the cells as lists and the dates
all_cell_values = []
all_cell_dates = []
for name in all_cells:
    all_cell_values.append(df[name].tolist())
    all_cell_dates.append(df["Zeitstempel"].tolist())

# create a list of different colors (not optimal to produce more differentiable colors)
basetones = ["#550000", "#000055", "#550055", "#8A0000", "#00008A", "#8A008A", "#CC0000", "#0000CC", "#CC00CC",
             "#FF0000"]
colors = []
for i in range(10):
    base = basetones[i]
    for n in range(14):
        midval1 = base[3]
        midval2 = base[4]
        midval1 = int(midval1) + (n)
        if midval1 == 10:
            midval1 = "A"
        if midval1 == 11:
            midval1 = "B"
        if midval1 == 12:
            midval1 = "C"
        if midval1 == 13:
            midval1 = "D"
        if midval1 == 14:
            midval1 = "E"
        if midval1 == 15:
            midval1 = "F"
        midval2 = midval1
        col = "#" + base[1] + base[2] + str(midval1) + str(midval2) + base[5] + base[6]
        colors.append(col)

# get a list of labels for the legend in the plots
# contains empty values for the cells except for the first to reduce the amount of labels
labels = []
for i in range(len(all_cells)):
    if (i-6) % 14 == 0:
        labels.append("V_mod"+all_cells[i].split(" ")[1][6])
    else:
        labels.append("")

# CREATE MULTIPLE STACKED PLOTS FOR EVERY MODULE 1 PLOT CONTAINING ALL CELLS STACKED
anzahl_module = 10
fig = plt.figure(figsize=(25, 50))
# 10 rows, 1 col, index
ax = [fig.add_subplot(anzahl_module, 1, i + 1) for i in range(anzahl_module)]
n = 0
for a in ax:
    # Only take the 14 cells per module, n indicates the mpdule => [(n*14):((n+1)*14-1)]
    a.stackplot(range(len(all_cell_values[0])), all_cell_values[(n * 14):((n + 1) * 14 - 1)],
                labels=labels[(n * 14):((n + 1) * 14 - 1)], colors=colors[(n * 14):((n + 1) * 14 - 1)],
                lw=0.3, edgecolor="black");
    # remove y axis
    a.get_yaxis().set_visible(False)
    # legend
    a.legend(loc='upper left')
    # title
    a.title.set_text(f"Modul_{n}")
    n += 1
# plt.suptitle(f"Cars of type {target_check} that got predicted as {is_check}")  # title for whole graph
plt.savefig(os.path.join(save_path, "stackplot_per_module.png"), dpi=800, facecolor=fig.get_facecolor(), bbox_inches='tight')

# mV per Cell
fig, ax = plt.subplots(figsize=(20, 8), facecolor='white')
for i in range(len(all_cells)):
    # X achse = anzahl der werte von 0 bis max  (first arg)
    # y achse die voltage der cells  (second arg)
    if (i - 6) % 14 == 0:
        plt.plot(df["Zeitstempel"], all_cell_values[i], marker='', color=colors[i],
                 linewidth=0.4, alpha=0.9, label=labels[i])
    else:
        plt.plot(df["Zeitstempel"], all_cell_values[i], marker='', color=colors[i],
                 linewidth=0.4, alpha=0.9, label=labels[i])
plt.title("Voltage per Cell over time")
leg = ax.legend(loc='upper right')
ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
# set the linewidth of each legend object
for legobj in leg.legendHandles:
    legobj.set_linewidth(5.0)
plt.xlabel('time (15min/step)')
plt.ylabel('voltage (mV)')
plt.savefig(os.path.join(save_path, "lineplot_cells.png"), dpi=600, facecolor=fig.get_facecolor(), bbox_inches='tight')

# Create AVG mV per plot
module_lists = []
# loop über alle werte in 14er schritten
for i in range(0, len(all_cell_values)-13, 14):
    cells_per_module = []
    # take values
    for n in range(14):
        cells_per_module.append(all_cell_values[i+n])
    module_lists.append(np.asarray(cells_per_module))
# Create labels and Avg values
avg_values_per_module = []
for l in module_lists:
    avg_values_per_module.append(np.average(l, axis=0))
avg_labels = []
for i in range(10):
    avg_labels.append(f"Avg_V_Module_{i}")

# PLOT mV per Module
# figsize defines width and height of plot
fig, ax = plt.subplots(figsize=(25, 12), facecolor='white')
for i in range(len(avg_values_per_module)):
    plt.plot(df["Zeitstempel"], avg_values_per_module[i], marker='',  # color=colors[i*14+6],
             linewidth=0.6, alpha=0.9, label=avg_labels[i], zorder=15 - i)
plt.title("Voltage per Module over time")
leg = ax.legend(loc='upper right')
ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
# set the linewidth of each legend object
for legobj in leg.legendHandles:
    legobj.set_linewidth(5.0)
plt.xlabel('date')
plt.ylabel('voltage (mV)')
# dpi defines resolution
plt.savefig(os.path.join(save_path, "lineplot_AVG_per_modules.png"), dpi=600, facecolor=fig.get_facecolor(), bbox_inches='tight')

# Avg values over the whole time
avg_vals = []
i = 0
fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
for vals in avg_values_per_module:
    print(f"Module_{i} has avg V: {np.average(vals)}")
    avg_vals.append(np.average(vals))
    i+=1
plt.bar([0,1,2,3,4,5,6,7,8,9], avg_vals)
plt.ylim(3260, 3310)
plt.ylabel("avg mV")
plt.xlabel("module")
plt.savefig(os.path.join(save_path,"avg_mv_perModule.png"), dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')


