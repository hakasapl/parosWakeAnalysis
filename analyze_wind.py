import argparse
from cProfile import label
import os
import datetime
from time import strftime
from xmlrpc.client import Boolean
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter,FormatStrFormatter
from scipy.signal import butter, lfilter, detrend, welch, spectrogram
from scipy.signal.windows import hamming
import numpy as np
from obspy.signal.util import next_pow_2
import csv

def main():
    now = datetime.datetime.now()

    parser = argparse.ArgumentParser()
    parser.add_argument("data", help="Location of data output", nargs=1, type=str, default="data")
    parser.add_argument("-n", "--name", help="Name of event being analyzed", nargs=1, type=str)
    parser.add_argument("-f", "--event-log", help="Path to event log", type=str, default="")
    parser.add_argument("-s", "--start-time", help="Location of output data", type=str, default="1970-01-01-00-00-00")
    parser.add_argument("-e", "--end-time", help="Period, in ms, between each data push", type=str, default=now.strftime("%Y-%m-%d-%H-%M-%S"))
    parser.add_argument("-l", "--line", help="Point to mark vertical line on charts", action='append')
    parser.add_argument("-p", "--show-plots", help="Show interactive plots", action="store_true")
    args = parser.parse_args()
    print(args)

    if args.event_log == "":
        genGraphs(args.name[0], args.data[0], args.start_time, args.end_time, args.line, args.show_plots)
    else:
        # event log available
        with open(args.event_log, 'r') as csvfile:
            datareader = csv.reader(csvfile)
            for row in datareader:
                print(row)

                lines = row[1].split("|")

                genGraphs(row[0], args.data[0], row[2], row[3], lines, args.show_plots)

def genGraphs(str_eventname, str_datapath, str_starttime, str_endtime, str_events, show_plots = False):
    start_time = datetime.datetime.strptime(str_starttime, '%Y-%m-%d-%H-%M-%S')
    end_time = datetime.datetime.strptime(str_endtime, '%Y-%m-%d-%H-%M-%S')
    event_name = str_eventname
    output_loc = "output/" + event_name
    if not os.path.exists(output_loc):
        os.mkdir(output_loc)

    if start_time > end_time:
        print("End time must be after start time!")
        exit(1)

    df = pd.read_csv(str_datapath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])  # change this if timestamp format every changes in the data
    
    # filter out data outside of time range
    df = df.loc[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
    df.reset_index(drop=True, inplace=True)

    # get list of devices
    devices = df['module_id'].unique()

    # pivot table and interpolate missing timestamps
    df = df.pivot(index='timestamp', columns='module_id', values='value')

    # ensure fs=20
    new_range = pd.date_range(start_time, end_time, freq='50L')
    df = df.reindex(df.index.union(new_range)).interpolate(method='time').reindex(new_range)
    df = df.iloc[1: , :]
    #df.set_index("index")

    #print(df.head())
    #exit(0)

    #
    # (1) Plot raw barometric data
    #

    plt.figure()

    y_formatter = ScalarFormatter(useOffset=False)

    axes = df.plot(label=df.columns, subplots=True, lw=1)
    for ax in axes:
        ax.legend(loc='lower left', prop={'size': 6})
        ax.yaxis.set_major_formatter(y_formatter)
        ax.margins(x=0)
    
    # set plot title
    axes[0].set_title(event_name + " - Raw Wind Data", fontsize=22)
    plt.xlabel("Timestamp (UTC)", fontsize=18)
    plt.ylabel("Speed (m/s)", fontsize=18, loc='center')

    # plot event lines
    for event in str_events:
        event_dt = datetime.datetime.strptime(event, '%Y-%m-%d-%H-%M-%S')
        for ax in axes:
            ax.axvline(event_dt, color='k', linestyle='--')

    plt.savefig(output_loc + "/wind.png")

    if show_plots:
        plt.show()

if __name__ == "__main__":
    main()