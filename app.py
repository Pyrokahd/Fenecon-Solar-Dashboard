
import dash
from dash import dcc  # https://dash.plotly.com/dash-core-components
from dash import html  # https://dash.plotly.com/dash-html-components
from dash.dependencies import Input, Output, State

import plotly.express as px  # express plot
from plotly.tools import mpl_to_plotly  # matplot
import plotly.graph_objects as go  # graph objects  # https://plotly.com/python/graph-objects/

from plotly.subplots import make_subplots  # Make Subplots with go https://plotly.com/python/creating-and-updating-figures/

import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np
import matplotlib.dates as mdates
import datetime
import logging
logging.basicConfig(filename='DashboardLog.log', encoding='utf-8', level=logging.DEBUG,
                    format='app.py %(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

import time
import threading
# Typehint: https://docs.python.org/3/library/typing.html

# initial callback duplicates need to be prevented
app = dash.Dash(__name__, prevent_initial_callbacks="initial_duplicate")  # default: http://127.0.0.1:8050
# Dash automatically loads CSS files that are in the assets folder

VERSION = "0.2"
filename: str = "fenecon_voltage_data.csv"   # "REP_fenecon_voltage_data_v5_test.csv"
timecolumn = 'Zeitstempel'  # x-axis in most plots
colors = {"background_plot": "#DEDEDE", "text": "#cce7e8", "text_disabled": "#779293", "background_area": "#1d2c45"}
GLOBAL_GRAPH_MARGINS = {"l":80, "r":30, "t":5, "b":10}

global_df = None  # global var for dataframe to be used in callbacks
global_module_names = None  # global var for the module names to be used in callbacks to update plots
global_cell_names = None  # global var for the column names for all cells
global_secondary_column_names = None  # global var for column names that are not modules or cells

debug_run = True  # flask runs the main code twice when in debugging


def read_data_as_df(filename):
    df = pd.read_csv(
        # read the filename in directory "data" within current directory
        os.path.join(os.path.join(os.getcwd(), "data"), filename), sep=";"
    )
    # convert time form string to timedate object
    df[timecolumn] = pd.to_datetime(df[timecolumn],
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


def add_avg_module_to_df(avg_module_values, module_names, df):
    """
    Depricated! avg per module is now calculated in the data collection script and directly saved within the csv
    :param avg_module_values:
    :param module_names:
    :param df:
    :return:
    """
    # combine the values for every column into tuples
    # because pandas creates row per row so 1 tuple are all values in the first row from all columns
    # for this unpack the lists as args into zip https://stackoverflow.com/questions/4112265/how-to-zip-lists-in-a-list
    avg_df = pd.DataFrame(list(zip(*avg_module_values)), columns=module_names)
    # concat both frames
    new_df = pd.concat([df, avg_df], axis=1, join="inner")
    return new_df


def create_fig_matplot(avg_module_values, avg_labels) -> plt:
    # PLOT mV per Module
    # figsize defines width and height of plot
    px = 1 / plt.rcParams['figure.dpi']

    fig, ax = plt.subplots(figsize=(960*px, 540*px), facecolor='white')
    for i in range(len(avg_module_values)):
        plt.plot(df[timecolumn], avg_module_values[i], marker='',  # color=colors[i*14+6],
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
    fig = px.line(df, x=timecolumn, y=module_names)
    # https://plotly.com/python/creating-and-updating-figures/#updating-traces
    fig.update_traces(line=dict(width=0.8))  # selector?
    fig.update_layout(legend_title_text="Modules")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Avg mV")

    return fig


def create_fig_graphobject(df, module_names, add_secondary_y: bool = False, secondary_col: str = "Ladezustand [%]",
                           use_delta=False, show_marker=False):
    # https://plotly.com/python/graph-objects/
    # https://plotly.com/python-api-reference/

    # Create figure with secondary y-axis
    if add_secondary_y:
        fig = make_subplots(specs=[[{"secondary_y": True}]]) #, "r":-0.01}]])  # 1% weniger abstand zur legende
    else:
        fig = go.Figure()

    if show_marker:
        linemode = "lines+markers"
    else:
        linemode = "lines"

    # mV plot lines
    for name in module_names:
        fig.add_trace(go.Scatter(x=df[timecolumn], y=df[name], mode=linemode,
                                 showlegend=True, line=dict(width=0.9), name=name,
                                 hovertemplate="%s<br>Date=%%{x}<br>mV=%%{y}<extra></extra>"%name
                                 ))
    if add_secondary_y:
        # handle too long names for legend
        legend_name = secondary_col
        if len(legend_name) > 15:
            legend_name = legend_name.split(" ")[0]
        if len(legend_name) > 15:
            legend_name = "Secondary"

        if use_delta:
            y_axis = df[secondary_col].diff().fillna(0)
        else:
            y_axis = df[secondary_col]

        fig.add_trace(
            go.Scatter(x=df[timecolumn], y=y_axis, name=legend_name, mode=linemode,
                       line=dict(width=1.4, color="red", dash='dot'),
                       hovertemplate="%s<br>Date=%%{x}<br>value=%%{y}<extra></extra>"%secondary_col),
            secondary_y=True
        )
        fig.update_yaxes(title_text=secondary_col, secondary_y=True, color="red")#, tickfont_family="Arial Black")
        fig.update_yaxes(title_text="mV", secondary_y=False)
        #fig.update_traces(marker=dict(size=3, line=dict(width=0, color='black')))
    else:
        # secondary_y only exists in subplots
        fig.update_yaxes(title_text="mV")

    fig.update_layout(legend_title_text="Modules")
    fig.update_xaxes(title_text="Date")
    fig.update_layout(legend_x=1)

    # change colors
    fig.update_layout(
        plot_bgcolor=colors["background_plot"],
        paper_bgcolor=colors["background_area"],
        font_color=colors["text"],
        margin=dict(l=GLOBAL_GRAPH_MARGINS["l"], r=GLOBAL_GRAPH_MARGINS["r"]+100, t=GLOBAL_GRAPH_MARGINS["t"],
                    b=GLOBAL_GRAPH_MARGINS["b"]),
        #title_text="Double Y Axis Example"
    )

    return fig


def create_bar_fig(df, module_names):
    avg_per_mod = []

    for mod in module_names:
        avg_per_mod.append(np.average( np.asarray(df[mod].tolist()) ))

    fig = px.bar(x=module_names, y=avg_per_mod, range_y=[min(avg_per_mod)-100, max(avg_per_mod)+100])

    fig.update_xaxes(title_text="Module")
    fig.update_yaxes(title_text="Avg mV")
    # change colors
    fig.update_layout(
        plot_bgcolor=colors["background_plot"],
        paper_bgcolor=colors["background_area"],
        font_color=colors["text"],
        margin=dict(l=GLOBAL_GRAPH_MARGINS["l"], r=GLOBAL_GRAPH_MARGINS["r"], t=GLOBAL_GRAPH_MARGINS["t"],
                    b=GLOBAL_GRAPH_MARGINS["b"]),
        height=int(300)  # setting based on callback through default height? https://stackoverflow.com/questions/70315657/get-width-and-height-of-plotly-figure
    )


    return fig


def create_delta_overtime_fig(df, module_names, add_secondary_y: bool = False, secondary_col: str = "Ladezustand [%]",
                              use_delta=False, show_marker=False):
    if add_secondary_y:
        fig = make_subplots(specs=[[{"secondary_y": True}]]) #, "r":-0.01}]])  # 1% weniger abstand zur legende
    else:
        fig = go.Figure()

    if show_marker:
        linemode = "lines+markers"
    else:
        linemode = "lines"

    # get the lowest and highest value betwwen all modules at every timestep
    # Add delta mV values (value between min mV and max mV over all modules) to df
    tmp_df = df.copy()
    tmp_df["absolute_delta"] = tmp_df[module_names].max(axis=1) - tmp_df[module_names].min(axis=1)

    fig.add_trace(go.Scatter(x=tmp_df[timecolumn], y=tmp_df["absolute_delta"], mode=linemode,
                             showlegend=True, line=dict(width=1.2), name="mV delta",  # line=dict(width=1.2, color="#26874a")
                             hovertemplate="%s<br>Date=%%{x}<br>delta mV=%%{y}<extra></extra>"%"mV delta"
                             ))
    if add_secondary_y:
        # handle too long names for legend
        legend_name = secondary_col
        if len(legend_name) > 15:
            legend_name = legend_name.split(" ")[0]
        if len(legend_name) > 15:
            legend_name = "Secondary"

        if use_delta:
            y_axis = df[secondary_col].diff().fillna(0)
        else:
            y_axis = df[secondary_col]

        fig.add_trace(
            go.Scatter(x=df[timecolumn], y=y_axis, name=legend_name, mode=linemode,
                       line=dict(width=1.4, color="red", dash='dot'),
                       hovertemplate="%s<br>Date=%%{x}<br>value=%%{y}<extra></extra>"%secondary_col),
            secondary_y=True
        )
        fig.update_yaxes(title_text=secondary_col, secondary_y=True, color="red")#, tickfont_family="Arial Black")
        fig.update_yaxes(title_text="mV delta", secondary_y=False)
        #fig.update_traces(marker=dict(size=3, line=dict(width=0, color='black')))
    else:
        # secondary_y only exists in subplots
        fig.update_yaxes(title_text="mV delta")

    fig.update_layout(legend_title_text="Modules")
    fig.update_xaxes(title_text="Date")
    fig.update_layout(legend_x=1)

    # change colors
    fig.update_layout(
        plot_bgcolor=colors["background_plot"],
        paper_bgcolor=colors["background_area"],
        font_color=colors["text"],
        margin=dict(l=GLOBAL_GRAPH_MARGINS["l"], r=GLOBAL_GRAPH_MARGINS["r"]+100, t=GLOBAL_GRAPH_MARGINS["t"],
                    b=GLOBAL_GRAPH_MARGINS["b"]),
        #title_text="The delta between the lowest module mV and the highest over time",
        height=int(180),
    )

    return fig


def create_headerdiv():
    header_text: str = '''
        # Fenecon Solar Panel Dashboard

        This Dashboard primarly shows the voltage values for every battery module to see if they behave the same.
        Every module has 14 cells. Additional information can be included in the main graph as secondary y axis,
        for example the battery loading level. This is done in the "Settings" section.
        '''

    return html.Div([
        html.Label("v"+VERSION),
        #html.Img(src=os.path.join("assets", "driller.PNG"), style={"width":"100px","height":"100px"}),
        dcc.Markdown(children=header_text)
    ], id="header_div", className="container")


def create_module_selection_div(module_names):
    return html.Div([

        html.Label("Module Selection"),
        html.Br(),
        dcc.Dropdown(
            id="module-dropdown",
            options=[{"label": y, "value": v} for y,v in zip(module_names, range(len(module_names)))],
            value=0,
            className="dropdown",
            style={"margin": "0px 0px 0px 0px"}
        )

    ], id="module_selection_div", className="div_class",
        style={"margin-left": f"{GLOBAL_GRAPH_MARGINS['l']}px", "flex": "1 1 0px"})


def create_settingsdiv(secondary_column_names):
    return html.Div([

        html.H3("Settings:", id="settings_label"),

        html.Div([
            dcc.Checklist(options=["Show secondary y-axis", "Use delta value"], id="secondary_y_checkbox",
                          value=[], style={}),
            # todo is there a way to directly adress the marker in the figs via callback and only change those (without new fig generation)?
            dcc.Checklist(options=["Show line-marker"], id="showmarker_checkbox",
                          value=[], style={}),

        ],id="settings_checklist_div"),


        html.Label("Select secondary value", style={"padding-top":"10px"}),
        dcc.Dropdown(
            id="secondary_y_dropdown",
            options=[{"label": y, "value": y} for y in secondary_column_names],
            value="Ladezustand [%]",
            className="dropdown",
            style={"padding-right":f"{GLOBAL_GRAPH_MARGINS['r']}px"}
        )

        #html.Br()

    ], id="settings_div", className="div_class")


def create_mV_plots_per_cell_for_one_module(_df, _module_names, all_cell_names, module_id: int = 0):
    """

    :param _df:
    :type _df:
    :param _module_names:  Only to be used as label for the legend of the cell plot.
    :type _module_names:
    :param all_cell_names:
    :type all_cell_names:
    :param module_id:
    :type module_id:
    :return:
    :rtype:
    """
    # Every module has 14 cells
    module_cell_values_names = all_cell_names[0 + (module_id * 14):14 + (module_id * 14)]
    shortened_cell_names = [i.split()[-1][:-3]+"_"+i.split()[-1][-3:] for i in module_cell_values_names]

    # Create line figure for cell mV
    fig = go.Figure()
    i = -1
    for name in module_cell_values_names:
        i+=1
        short_name = shortened_cell_names[i]
        fig.add_trace(go.Scatter(x=_df[timecolumn], y=_df[name], mode='lines',
                                 showlegend=True, line=dict(width=0.8), name=short_name,
                                 hovertemplate="%s<br>Date=%%{x}<br>mV=%%{y}<extra></extra>" % short_name
                                 ))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="mV")
    # change colors
    fig.update_layout(
        plot_bgcolor=colors["background_plot"],
        paper_bgcolor=colors["background_area"],
        font_color=colors["text"],
        margin=dict(l=GLOBAL_GRAPH_MARGINS["l"], r=GLOBAL_GRAPH_MARGINS["r"], t=GLOBAL_GRAPH_MARGINS["t"],
                    b=GLOBAL_GRAPH_MARGINS["b"]),
        height=int(360),
        # TODO This seems to be a bug in dash that the legend_title doesnt update on the callback
        #legend_title_text=str(_module_names[module_id]),
        #title_text="mV per cell in "+str(_module_names[module_id])
    )
    #fig.update_layout(showlegend=True)

    # Create bar plot for avg cell mV
    avg_per_cell = []
    for cell in module_cell_values_names:
        avg_per_cell.append(np.average(np.asarray(_df[cell].tolist())))

    # create bar figure with shortened cell names
    fig_bar = px.bar(x=shortened_cell_names,
                     y=avg_per_cell, range_y=[min(avg_per_cell) - 50, max(avg_per_cell) + 50])

    fig_bar.update_xaxes(title_text="Cell")
    fig_bar.update_yaxes(title_text="Avg mV")
    # change colors
    fig_bar.update_layout(
        plot_bgcolor=colors["background_plot"],
        paper_bgcolor=colors["background_area"],
        font_color=colors["text"],
        margin=dict(l=GLOBAL_GRAPH_MARGINS["l"], r=GLOBAL_GRAPH_MARGINS["r"], t=GLOBAL_GRAPH_MARGINS["t"],
                    b=GLOBAL_GRAPH_MARGINS["b"]),
        height=int(360)
    )

    return fig, fig_bar


def create_module_cell_plots_div(_df, _module_names, all_cell_names):
    fig1, fig2 = create_mV_plots_per_cell_for_one_module(_df, _module_names, all_cell_names)

    return html.Div([
        # top right bottom left (margin)
        html.H2("Voltage Values for the cells within the selected module:", style={"margin":f"50px 5px 20px {GLOBAL_GRAPH_MARGINS['l']}px"}),

        #Settings div
        html.Div([
            create_module_selection_div(_module_names),

            html.Div([
                # empty div next to module selection for spacing
            ], className="div_class", style={"flex": "1 1 0px"})
        ], id="mod_selection", className="div_class", style={'display': 'flex', 'flex-direction': 'row'}),

        # Row containing both graphs
        html.Div([
            html.Div([
                dcc.Graph(id="cell_line_fig", figure=fig1)
            ], id="cellline_div", className="div_class"),

            html.Div([
                dcc.Graph(id="cell_bar_fig", figure=fig2)
            ], id="cellbar_div", className="div_class")

        ], id="cell_plots_div", className="div_class")

    ], id="lower_area_div", className="div_class", style={'display': 'flex', 'flex-direction': 'column'})


def create_correlation_div(_df):
    """
    Example for scatter plot to check for correlation based on delta values from i.e. energy given
    :param _df:
    :type _df:
    :return:
    :rtype:
    """
    df = _df.copy()
    df["Netzeinspeisung delta [Wh]"] = df["Netzeinspeisung Energie [Wh]"].diff().fillna(0)
    df["Netzbezug delta [Wh]"] = df["Netzbezug Energie [Wh]"].diff().fillna(0)

    fig = px.scatter(df, x="Netzbezug delta [Wh]", y="Netzeinspeisung delta [Wh]")
    return html.Div([
        dcc.Graph(id="correlation_div", figure=fig)
    ], id="correlation_row_div", className="div_class", style={'display': 'flex', 'flex-direction': 'row'})


def get_df_with_transformed_date_and_rangeslider_marker(_df):
    """
    Returns a flag, the edited dataframe and a marker for the rangeslider.
    The returns flag 'hour' or 'day' or 'minute' tells us if it is rounded to hours or to days.
    df.
    The marker dict is a dict used to set the markers for a rangeslider to the datetime.
    :param _df:
    :type _df:
    :return: flag, dataframe, marker
    :rtype: str, pandas.df, dict
    """
    # EDIT DATAFRAME
    flag = "hour"
    df_new_time = _df.copy()
    difference = max(df_new_time[timecolumn]) - min(df_new_time[timecolumn])
    if difference > pd.Timedelta(1, "d"):
        # reduce time timestamp resolution to per day basis
        df_new_time[timecolumn] = df_new_time[timecolumn].dt.date   # floors to closest day without time
        flag = "day"
    elif difference > pd.Timedelta(1, "H"):
        # timedelta.round(freq='H')
        df_new_time[timecolumn] = df_new_time[timecolumn].dt.round(freq="H")
        flag = "hour"
    else:
        df_new_time[timecolumn] = df_new_time[timecolumn].dt.round(freq="min")
        flag = "minute"

    # MARKER
    numdate = [x for x in range(len(df_new_time[timecolumn].unique()))]
    if flag == "day":
        marker = {numd: {"label": date.strftime('%d/%m/%y'), "style": {"color": colors["text"]}} for numd, date in
                     zip(numdate, df_new_time[timecolumn].unique())}
    elif flag == "hour":
        marker = {numd: {"label": date.strftime('%d/%m/%y %H:%M'), "style": {"color": colors["text"]}} for numd, date in
                  zip(numdate, df_new_time[timecolumn].unique())}
    elif flag == "minute":
        marker = {numd: {"label": date.strftime('%d/%m/%y %H:%M'), "style": {"color": colors["text"]}} for numd, date in
                  zip(numdate, df_new_time[timecolumn].unique())}
    return flag, df_new_time, marker


def get_df_mask_from_rangeslider(flag, _rounded_df, _df_to_mask, minval, maxval):
    """
    Takes a flag 'hour' or 'day' (based on if the datas timestemps are rounded to the full hour or converted to date).
    Takes a dataframe on which the min and maxvals are based (same as df to mask but with rounded or converted timedates).
    Takes a dataframe to be masked, and a minval and maxval refering to datetimes (_df_to_mask).
    Returns the mask to filter the dataframe to be between the selected datetimes.
    :param flag:
    :type flag:
    :param _rounded_df:
    :type _rounded_df:
    :param _df_to_mask:
    :type _df_to_mask:
    :param minval:
    :type minval:
    :param maxval:
    :type maxval:
    :return:
    :rtype:
    """
    # translate the numbers from the slider to the dates then timedates
    from_val = _rounded_df[timecolumn].unique()[minval]
    to_val = _rounded_df[timecolumn].unique()[maxval]
    from_val = pd.to_datetime(from_val, format='%Y-%m-%d %H:%M:%S.%f')
    to_val = pd.to_datetime(to_val, format='%Y-%m-%d %H:%M:%S.%f')
    # no time added for hour since hour is rounded and not floored
    if flag == "hour":
        # add 1 hour -1 sec
        to_val = to_val + pd.Timedelta("00:30:59")
    if flag == "day":
        # add 24h -1 sec
        to_val = to_val + pd.Timedelta("23:59:59")
    if flag == "minute":
        # add 24h -1 sec
        from_val = from_val - pd.Timedelta("00:00:59")
        to_val = to_val + pd.Timedelta("00:00:59")
    # filter the original df (with datetime not date) to contain only data within the selected dates
    mask = (_df_to_mask[timecolumn] >= from_val) & (_df_to_mask[timecolumn] <= to_val)
    return mask


def create_app_layout(df, module_names, all_cell_names, secondary_column_names):
    """
    add html elements and figues to the dash app
    :param fig:
    :type fig:
    :return:
    :rtype:
    """
    # reduce time timestamp resolution to per day basis (or to hours if its less than 24h)
    flag, tmp_df, marker = get_df_with_transformed_date_and_rangeslider_marker(global_df)
    numdate = [x for x in range(len(tmp_df[timecolumn].unique()))]

    fig = create_fig_graphobject(df, module_names)
    bar_fig = create_bar_fig(df, module_names)
    delta_fig = create_delta_overtime_fig(df, module_names)

    app.layout = html.Div([
        create_headerdiv(),
        dcc.Interval(
            id='interval-component',
            interval= 60 * 1000,  # in milliseconds
            n_intervals=0
        ),

        html.Div([
            html.H2("The mV value per module as average over its cells:",
                    style={"margin": f"50px 5px 20px {GLOBAL_GRAPH_MARGINS['l']}px"}),
            dcc.Graph(id="linefig", figure=fig)
        ], id="figure_div", className="div_class"),

        html.Div([
            dcc.RangeSlider(min=numdate[0], max=numdate[-1], value=[numdate[-0], numdate[-1]],
                        #marks={numd: date.strftime('%d/%m/%y') for numd, date in zip(numdate, df_time_as_days[timecolumn].unique())},
                        marks=marker,
                        #tooltip = {"placement": "bottom", "always_visible": False}
                        #updatemode='drag',  # to update instantly while dragging, else while releasing
                        step=1,  # only whole steps (whole day are relevant)
                        id="date_rangeslider")
        ], id="rangeslider_div", className="div_class"),

        html.Div([
            html.H3("The delta, between the lowest module mV and the highest mV, over time:",
                    style={"margin": f"10px 5px 2px {GLOBAL_GRAPH_MARGINS['l']}px"}),
            dcc.Graph(id="delta_fig", figure=delta_fig)
        ], id="delta_over_time_div", className="div_class"),

        html.Div([

            html.Div([
                dcc.Graph(id="barfig", figure=bar_fig)
            ], id="barplot_div", className="div_class"),
            create_settingsdiv(secondary_column_names),

        ], id="setting_barplot_div", className="div_class"),

        create_module_cell_plots_div(df, module_names, all_cell_names),

        #create_correlation_div(df),


    ], id="layout", className="div_class")


# If possible, expensive initialization (like downloading or querying data) should be done
# in the global scope of the app instead of within the callback functions.
@app.callback(
    Output('date_rangeslider', 'marks'),
    [Input('date_rangeslider', 'value')],
    [State('date_rangeslider', 'marks')]
)
def update_rangeslider_marks(vals, marks):
    """
    Update the dateslider marks when selected, to have the correct color and text style
    :param vals:
    :type vals:
    :param marks:
    :type marks:
    :return:
    :rtype:
    """
    for k in marks:
        if int(k) >= vals[0] and int(k) <= vals[1]:
            marks[str(k)]['style']['color'] = colors["text"]  # selected
        else:
            marks[str(k)]['style']['color'] = colors["text_disabled"]  # not selected
    return marks


# Another possibility instead of duplicate Outputs: Updating the Same Output From Different Inputs
# https://dash.plotly.com/duplicate-callback-outputs
@app.callback(
    Output("linefig", "figure"),
    Output('barfig', 'figure'),
    Output("cell_line_fig", "figure"),
    Output("cell_bar_fig", "figure"),
    Output("delta_fig", "figure"),
    Input("date_rangeslider", "value"),
    State("module-dropdown", "value"),
    State("secondary_y_checkbox", "value"),
    State("secondary_y_dropdown", "value"),
    State("showmarker_checkbox", "value"),
    prevent_initial_call=True
)
def update_figures_timespan(selected_year_range, sel_module_id, checkbox, dropdown_value, marker_checkbox):
    # first get the transformed timestamps (as date or rounded to full hour)

    flag, tmp_df, _ = get_df_with_transformed_date_and_rangeslider_marker(global_df)
    mask = get_df_mask_from_rangeslider(flag, tmp_df, global_df, selected_year_range[0], selected_year_range[1])
    filtered_df = global_df.loc[mask]

    show_secondary_axis = False
    use_delta = False
    show_marker = False
    if "Show line-marker" in marker_checkbox:
        show_marker = True
    if 'Show secondary y-axis' in checkbox:
        show_secondary_axis = True
    if 'Use delta value' in checkbox:
        use_delta = True

    # Create new figure return that figure
    fig = create_fig_graphobject(filtered_df, global_module_names, show_secondary_axis, dropdown_value,
                                 use_delta, show_marker)
    #fig.update_layout(legend_title_text="blabla")
    fig.update_layout(transition_duration=200)

    # Update Avg Bar plot
    barfig = create_bar_fig(filtered_df, global_module_names)
    barfig.update_layout(transition_duration=200)

    # Update Cell line and bar figures
    cell_line, cell_bar = create_mV_plots_per_cell_for_one_module(filtered_df, global_module_names, global_cell_names, sel_module_id)
    cell_line.update_layout(transition_duration=200)
    cell_bar.update_layout(transition_duration=200)

    # Update delta fig
    deltafig = create_delta_overtime_fig(filtered_df, global_module_names, show_secondary_axis, dropdown_value,
                                         use_delta, show_marker)
    deltafig.update_layout(transition_duration=200)

    return fig, barfig, cell_line, cell_bar, deltafig


@app.callback(
    Output("cell_line_fig", "figure", allow_duplicate=True),
    Output("cell_bar_fig", "figure", allow_duplicate=True),
    Input("module-dropdown", "value"),
    State("date_rangeslider", "value"),
    prevent_initial_call=True
)
def update_cell_figures(sel_module_id, selected_year_range):
    # year_range is a list with two numbers left and right value
    # first get the timestamps as date (without time) as tempdf
    # first get the transformed timestamps (as date or rounded to full hour)
    flag, tmp_df, _ = get_df_with_transformed_date_and_rangeslider_marker(global_df)
    mask = get_df_mask_from_rangeslider(flag, tmp_df, global_df, selected_year_range[0], selected_year_range[1])
    filtered_df = global_df.loc[mask]

    # Update Cell line and bar figures
    cell_line, cell_bar = create_mV_plots_per_cell_for_one_module(filtered_df, global_module_names, global_cell_names,
                                                                  sel_module_id)
    cell_line.update_layout(transition_duration=200)
    cell_bar.update_layout(transition_duration=200)

    return cell_line, cell_bar


@app.callback(
    Output("linefig", "figure", allow_duplicate=True),
    Output("delta_fig", "figure", allow_duplicate=True),
    Input("secondary_y_checkbox", "value"),
    Input("secondary_y_dropdown", "value"),
    Input("showmarker_checkbox", "value"),
    State("date_rangeslider", "value"),
    prevent_initial_call=True
)
def update_secondary_axis_in_lineplot(checkbox, dropdown_value, marker_checkbox, selected_year_range):
    # year_range is a list with two numbers left and right value
    # first get the timestamps as date (without time) as tempdf
    # first get the transformed timestamps (as date or rounded to full hour)
    flag, tmp_df, _ = get_df_with_transformed_date_and_rangeslider_marker(global_df)
    mask = get_df_mask_from_rangeslider(flag, tmp_df, global_df, selected_year_range[0], selected_year_range[1])
    filtered_df = global_df.loc[mask]

    show_secondary_axis = False
    use_delta = False
    show_marker = False
    print(marker_checkbox)
    if "Show line-marker" in marker_checkbox:
        show_marker = True
    if 'Show secondary y-axis' in checkbox:
        show_secondary_axis = True
    if 'Use delta value' in checkbox:
        use_delta = True

    fig = create_fig_graphobject(filtered_df, global_module_names, show_secondary_axis, dropdown_value, use_delta,
                                 show_marker)

    # Update delta fig
    deltafig = create_delta_overtime_fig(filtered_df, global_module_names, show_secondary_axis, dropdown_value,
                                         use_delta, show_marker)

    return fig, deltafig


@app.callback(
    Output("linefig", "figure", allow_duplicate=True),
    Output('barfig', 'figure', allow_duplicate=True),
    Output("cell_line_fig", "figure", allow_duplicate=True),
    Output("cell_bar_fig", "figure", allow_duplicate=True),
    Output('date_rangeslider', 'marks', allow_duplicate=True),
    Output("delta_fig", "figure", allow_duplicate=True),
    Input("interval-component", "n_intervals"),
    State("date_rangeslider", "value"),
    State("secondary_y_checkbox", "value"),
    State("secondary_y_dropdown", "value"),
    State("showmarker_checkbox", "value"),
    State("module-dropdown", "value"),
    prevent_initial_call=True
)
def refresh_all_graphs_on_interval(n, selected_year_range, checkbox, dropdown_value, marker_checkbox, sel_module_id):
    # Here the global df needs to be reloaded in order to update for current data
    # even though callbacks shouldnt be used to update global vars, this probably is fince since its an interval
    # todo maybe use a filesystem cache and a dc.store element as input for df in every callback, as alternative
    # https://dash.plotly.com/sharing-data-between-callbacks
    global global_df
    global_df = read_data_as_df(filename)

    # first get the transformed timestamps (as date or rounded to full hour)
    flag, tmp_df, marker = get_df_with_transformed_date_and_rangeslider_marker(global_df)
    mask = get_df_mask_from_rangeslider(flag, tmp_df, global_df, selected_year_range[0], selected_year_range[1])
    filtered_df = global_df.loc[mask]

    # Update the graphs
    show_secondary_axis = False
    use_delta = False
    show_marker = False
    if "Show line-marker" in marker_checkbox:
        show_marker = True
    if 'Show secondary y-axis' in checkbox:
        show_secondary_axis = True
    if 'Use delta value' in checkbox:
        use_delta = True

    # Create new figure return that figure
    fig = create_fig_graphobject(filtered_df, global_module_names, show_secondary_axis, dropdown_value,
                                 use_delta, show_marker)
    #fig.update_layout(legend_title_text="blabla")
    fig.update_layout(transition_duration=200)

    # Update Avg Bar plot
    barfig = create_bar_fig(filtered_df, global_module_names)
    barfig.update_layout(transition_duration=200)

    # Update Cell line and bar figures
    cell_line, cell_bar = create_mV_plots_per_cell_for_one_module(filtered_df, global_module_names, global_cell_names, sel_module_id)
    cell_line.update_layout(transition_duration=200)
    cell_bar.update_layout(transition_duration=200)

    # Update delta fig
    deltafig = create_delta_overtime_fig(filtered_df, global_module_names, show_secondary_axis, dropdown_value,
                                         use_delta, show_marker)
    deltafig.update_layout(transition_duration=200)

    return fig, barfig, cell_line, cell_bar, marker, deltafig


# MAIN CODE THAT SHOULD ALSO RUN WHEN IMPORTING THE SCRIPT (into wsgi.py)
print("Checking for file...")
logging.info("Checking for file...")
# waiting for the file to generate if its not there already
if not os.path.exists(os.path.join(os.path.join(os.getcwd(), "data"), filename)):
    print("CSV TO READ DOESNT EXIST! Waiting...")
    logging.warning("CSV TO READ DOESNT EXIST! sleeping 3 min...")
    time.sleep(180)  # wait 2 minutes
print("done checking")
logging.info("done checking")

df = read_data_as_df(filename)
cell_values, cell_names = get_list_of_cell_voltage_values(df)
avg_module_values, module_names = get_list_of_avg_module_voltage_values(cell_values)

global_secondary_column_names = [x for x in df.columns if
                                 x not in cell_names + module_names + [timecolumn] and x[:6] != "Module"]
global_df = df  # to have a global reference to use in callbacks
global_module_names = module_names
global_cell_names = cell_names

create_app_layout(global_df, module_names, cell_names, global_secondary_column_names)


#  __main__ means the script is executed directly and not imported
if __name__ == "__main__":
    # Correlation test
    #print(np.corrcoef(global_df["Ladezustand [%]"].tolist(), global_df["Netzbezug Energie [Wh]"].diff().fillna(0).tolist()))
    #print(np.corrcoef(global_df["Ladezustand [%]"].tolist(), global_df["Netzeinspeisung Energie [Wh]"].diff().fillna(0).tolist()))

    print("main running")
    logging.info("main running")

    app.run_server(debug=True, port=8050, dev_tools_hot_reload=True)

    # Todo config file to change urls?



# Other ideas
# cool 3D graph example: https://plotly.com/python/custom-buttons/
# Change legend pos on callback: https://plotly.com/python/legend/?_ga=2.214419600.642079767.1682617466-1272301599.1682617466#legend-position