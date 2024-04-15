'''
logvis visualize the log data
'''

import time
import argparse

import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

params = {
    # 'font.family': 'Inter',
    'font.family': 'sans-serif',
    'legend.fontsize': 'x-small',
    'axes.labelsize': 'x-small',
    'axes.titlesize': 'x-small',
    'xtick.labelsize': 'x-small',
    'ytick.labelsize': 'x-small',
    # 'figure.figsize': (3.0, 1.7),
}
plt.rcParams.update(params)
plt.clf()
log_headers = ["timesteps", "start_time", "action", "latency", "file_path", "num_query"]


def parse_timestamp(timestamp_str):
    # 2024-04-12 14:45:40.00857
    # to datetime object
    return pd.to_datetime(timestamp_str, format='%Y-%m-%d %H:%M:%S.%f')

def parse_func_name(func_name_str):
    # Func:'load_index' => "load_index"
    str_l = func_name_str.split(":")
    if "completed" in func_name_str:
        return func_name_str
    return str_l[-1][:]

def parse_latency(time_str):
    return float(time_str[:-1])

def create_gantt_chart(load_index_hbars, search_index_hbars, figsize=(6, 1), ax=None, vline=True):
    return_ax = False
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        return_ax = True

    bar_width = 0.5
    bar_gap = 0.0
    # [(x, length), ()], (y, bar_width)
    ax.broken_barh(load_index_hbars[:], (1, bar_width), facecolors =('darkorange'))
    ax.broken_barh(search_index_hbars[:], (1+bar_width+bar_gap, bar_width), facecolors =('green'))

    ax.set_yticks([1+bar_width/2, 1+bar_width+bar_gap+bar_width/2], ['load', 'search'])
    # ax.grid(True, alpha=0.5)

    if vline:
        last_x = search_index_hbars[-1][0]+search_index_hbars[-1][1]
        ax.axvline(x=last_x, color='black', linestyle='--', alpha=1)

    if return_ax:
        return fig, ax
    return ax

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize log data")
    parser.add_argument("--log", required=True, help="log file", type=str,)
    # parser.add_argument("-mr", "--mixtures_ratios", nargs="+", default=[0.], help="mixtures ratio for random queries (-mr 0.1 0.2 0.3)", type=float,)
    args = parser.parse_args()

    log_file = args.log

    df = pd.read_csv(log_file, header=None)
    df.columns = log_headers
    df["action"] = df["action"].map(parse_func_name)
    df["latency"] = df["latency"].map(parse_latency)
    df['start_time'] = df['start_time'] - df['start_time'][0]

    load_index_hbars = []
    search_index_hbars = []
    for i, row in df[df["action"] == "load_index"].iterrows():
        load_index_hbars.append((row["start_time"], row["latency"]))
    for i, row in df[df["action"] == "query_index"].iterrows():
        search_index_hbars.append((row["start_time"], row["latency"]))

    fig, ax = create_gantt_chart(load_index_hbars, search_index_hbars, ax=None)
    ax.set_title(log_file)
    fig.tight_layout()
    fig.savefig("vislogs/tmp.pdf")
