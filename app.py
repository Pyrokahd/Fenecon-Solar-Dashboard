# Fenecon Dashboard
# Fenecon data logger

import dash
from dash import dcc
from dash import html

import plotly.express as px  # express plot
from plotly.tools import mpl_to_plotly  # matplot
import plotly.graph_objects as go  # graph objects  # https://plotly.com/python/graph-objects/

from plotly.subplots import make_subplots # Make Subplots with go https://plotly.com/python/creating-and-updating-figures/

import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np
import matplotlib.dates as mdates

# Typehint: https://docs.python.org/3/library/typing.html

APP = dash.Dash()  # default: http://127.0.0.1:8050
filename: str = "REP_fenecon_voltage_data_v5.csv"


def read_data_as_df(filename):
    df = pd.read_csv(
        # read the filename in directory "data" within current directory
        os.path.join(os.path.join(os.getcwd(), "data"), filename), sep=";"
    )
    # convert time form string to timedate object
    df['Zeitstempel'] = pd.to_datetime(df['Zeitstempel'],
                                       format='%Y-%m-%d %H:%M:%S.%f')  # Year month day hour minute second microseconds
    return df


def get_list_of_cell_voltage_values(df) -> list:
    """
    return a list of lists containing the voltage value per cell.
    Every 14 cells are one module. Also returns cell names
    :param df:
    :type df:
    :return:
    :rtype:
    """
    all_cells = []
    for m in range(10):
        for c in range(14):
            if c < 10:
                all_cells.append(f"Voltage Module{m} Cell00{c}")
            else:
                all_cells.append(f"Voltage Module{m} Cell0{c}")

    # Save all columns from the cells as lists and the dates
    all_cell_values = []
    for name in all_cells:
        all_cell_values.append(df[name].tolist())
    return all_cell_values, all_cells


def get_list_of_avg_module_voltage_values(all_cell_values) -> list:
    """
    return a list of lists containing the avg voltage value per module.
    Also returns the list of module names
    :param df:
    :type df:
    :return:
    :rtype:
    """
    # Create AVG mV per plot
    module_lists = []
    # loop über alle werte in 14er schritten
    for i in range(0, len(all_cell_values) - 13, 14):
        cells_per_module = []
        # take values
        for n in range(14):
            cells_per_module.append(all_cell_values[i + n])
        module_lists.append(np.asarray(cells_per_module))
    # Create labels and Avg values
    avg_values_per_module = []
    for l in module_lists:
        avg_values_per_module.append(np.average(l, axis=0))
    avg_labels = []
    for i in range(10):
        avg_labels.append(f"Module_{i}")  # from top to bottom in the tower? Seems like it not sure yet
    return avg_values_per_module, avg_labels


def add_avg_module_to_df(avg_module_values, avg_labels, df):
    # combine the values for every column into tuples
    # because pandas creates row per row so 1 tuple are all values in the first row from all columns
    # for this unpack the lists as args into zip https://stackoverflow.com/questions/4112265/how-to-zip-lists-in-a-list
    avg_df = pd.DataFrame(list(zip(*avg_module_values)), columns=avg_labels)
    # concat both frames
    new_df = pd.concat([df, avg_df], axis=1, join="inner")
    return new_df


def create_fig_matplot(avg_module_values, avg_labels) -> plt:

    # PLOT mV per Module
    # figsize defines width and height of plot
    px = 1 / plt.rcParams['figure.dpi']

    fig, ax = plt.subplots(figsize=(960*px, 540*px), facecolor='white')
    for i in range(len(avg_module_values)):
        plt.plot(df["Zeitstempel"], avg_module_values[i], marker='',  # color=colors[i*14+6],
                 linewidth=0.8, alpha=0.9, label=avg_labels[i], zorder=15 - i)
    #plt.title("Voltage per Module over time")
    leg = ax.legend(loc='upper right')
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    # set the linewidth of each legend object
    for legobj in leg.legend_handles:
        legobj.set_linewidth(5.0)
    plt.xlabel('date')
    plt.ylabel('voltage (mV)')
    # dpi defines resolution
    #plt.savefig(os.path.join(save_path, "lineplot_AVG_per_modules.png"), dpi=600, facecolor=fig.get_facecolor(),bbox_inches='tight')
    #plt.
    plotly_fig = mpl_to_plotly(fig)
    return plotly_fig


def create_fig_express(df, module_names):
    # Melt pandas dataframe to make long format: https://pandas.pydata.org/docs/reference/api/pandas.melt.html
    # the long format seems to be intended for express plots like example data from:
    # "https://raw.githubusercontent.com/ThuwarakeshM/geting-started-with-plottly-dash/main/life_expectancy.csv"
    # See more about wide vs long format here:
    # https://community.plotly.com/t/announcing-plotly-py-4-8-plotly-express-support-for-wide-and-mixed-form-data-plus-a-pandas-backend/40048

    # Graph objects instead of plotly express? https://plotly.com/python/graph-objects/
    # https://community.plotly.com/t/how-to-plot-multiple-lines-on-the-same-y-axis-using-plotly-express/29219/15


    # Create Line plot
    fig = px.line(df, x='Zeitstempel', y=module_names)
    # https://plotly.com/python/creating-and-updating-figures/#updating-traces
    fig.update_traces(line=dict(width=0.8))  # selector?
    fig.update_layout(legend_title_text="Modules")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Avg mV")

    return fig


def create_fig_graphobject(df, module_names):
    # https://plotly.com/python/graph-objects/
    # https://plotly.com/python-api-reference/

    fig = go.Figure()
    for name in module_names:
        fig.add_trace(go.Scatter(x=df['Zeitstempel'], y=df[name], mode='lines',
                                 showlegend=True, line=dict(width=0.8)
                                 ))

    fig.update_layout(legend_title_text="Modules")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Avg mV")
    return fig


def create_app_layout(fig):
    """
    add html elements with figues to the dash app
    :param fig:
    :type fig:
    :return:
    :rtype:
    """
    #root_div = html.Div(id="maindiv")
    #root_div.children.append(html.Div([ dcc.Dropdown(id="dropdown",options=[{"label": y, "value": y}for y in range(0, 100)]) ]))
    APP.layout = html.Div([dcc.Graph(id="fig1", figure=fig)])
    #APP.layout = html.Div([dcc.Graph(id="fig1", figure=figs[0])], [dcc.Graph(id="fig2", figure=figs[0])])


if __name__ == "__main__":
    df = read_data_as_df(filename)
    cell_values, cell_names = get_list_of_cell_voltage_values(df)
    avg_module_values, module_names =  get_list_of_avg_module_voltage_values(cell_values)
    df = add_avg_module_to_df(avg_module_values, module_names, df)

    fig1 = create_fig_express(df, module_names)
    #fig2 = create_fig_matplot(avg_module_values, module_names)
    fig3 = create_fig_graphobject(df, module_names)

    create_app_layout(fig3)


    print("main running")
    APP.run_server(debug=True)


