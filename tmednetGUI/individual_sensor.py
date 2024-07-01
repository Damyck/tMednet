import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.dates as mdates
from matplotlib.figure import Figure


class SensorData():

    def __init__(self, filename):
        # For test "/home/marc/Projects/Mednet/tMednet/src/input_files/prueba_seascale.csv"
        # Load csv as DataFrame directly with its header
        self.data = pd.read_csv(filename, sep=',', header=9)
        # Reads the file and stores the metadata
        with open(filename) as f:
            content = f.readlines()
            self.utc = content[7][-8:-2]
            self.sensor = content[4][7:-1]
            self.dive = content[6][5:-1]
            self.duration = datetime.strptime(content[10][10:-4], '%H:%M:%S').time()
        self.__convert_to_utc()

    def __convert_to_utc(self):
        # Converts date column to datetime object and transforms it to UTC 00:00
        if self.utc[0] == '+':
            self.data['date'] = pd.to_datetime(self.data['date'],
                                               format="%Y-%m-%d %H:%M:%S") - timedelta(hours=float(self.utc[1:3]),
                                                                                       minutes=float(self.utc[4:6]))
        else:
            self.data['date'] = pd.to_datetime(self.data['date'],
                                               format="%Y-%m-%d %H:%M:%S") + timedelta(hours=float(self.utc[1:3]),
                                                                                       minutes=float(self.utc[4:6]))
    def plot_temperature_depth(self):

        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        self.data.plot(x='date', y='temperature(ºC)', ax=ax1)
        self.data.plot(x='date', y='depth(m.)', color='red', secondary_y=True, ax=ax2)
        plt.show()