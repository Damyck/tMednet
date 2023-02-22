import os
import time
import math
import imageio
import numpy as np
import xarray as xr
import pandas as pd
import seaborn as sns
import shapefile as shp
import cartopy.crs as ccrs
from netCDF4 import num2date
import cartopy.feature as cf
from datetime import datetime, date
import marineHeatWaves as mhw
from pandas import ExcelWriter
import matplotlib.pyplot as plt
from scipy import io, interpolate
from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset as NetCDFFile

os.environ['PROJ_LIB'] = '/home/marcjou/anaconda3/envs/tMednet/share/proj/'

class MHWMapper:
    _mat = ''
    duration = None
    intensity = None

    def __init__(self, dataset_path, start_period=str(date.today().year)+'-06-01', end_period=str(date.today().year)+'-06-30'):
        # Set up the Netcdf satellite data using the xarray library
        with xr.open_dataset(dataset_path) as self.ds:
            self.variables = self.ds.variables
            self.MHW = self.ds.MHW
            self.MHW_days = self.ds.MHW_days
            self.ds_dtime = self.ds.time
            self.lat = self.ds.lat
            self.lon = self.ds.lon

        # Get the period you want to plot
        self.__set_sliced_ds(start_period, end_period)

    def __str__(self):
        return "<MHWMapper object>"

    def __set_sliced_ds(self, start_period, end_period):
        start_time = pd.to_datetime(start_period)
        try:
            end_time = pd.to_datetime(end_period)
            self.ds_dtime.loc[end_time]  # TODO change this to check if end_time exists in the ds
        except:
            end_time = self.ds_dtime[-1]
        self.ds_time = self.ds_dtime.loc[start_time:end_time].dt.strftime('%Y-%m-%d')
        self.ds_MHW_sliced = self.MHW.sel(time=slice(start_time, end_time))
        self.ds_MHW_days_sliced = self.MHW_days.sel(time=slice(start_time, end_time))

    @staticmethod
    def ax_setter():
        ax = plt.axes(projection=ccrs.Mercator())
        ax.set_extent([-9.5, 37., 28., 50.], crs=ccrs.PlateCarree())
        ax.add_feature(cf.OCEAN)
        ax.add_feature(cf.LAND)
        ax.coastlines(resolution='10m')
        ax.add_feature(cf.BORDERS, linestyle=':', alpha=1)
        return ax

    def __create_image_by_type(self, lons, lats, mode, filenames):
        start = time.time()
        if mode == 'temperature':
            ds = self.ds_asst_interpolated
            levels = np.arange(math.trunc(float(np.nanquantile(np.ma.filled(ds, np.nan), 0.01))),
                               math.trunc(float(np.nanquantile(np.ma.filled(ds, np.nan), 0.99))) + 1, 1)
            cmap = 'RdYlBu_r'
            ylabel = 'Temperature (ºC)'
        elif mode == 'duration':
            ds = self.ds_MHW_days_sliced
            levels = np.arange(0, 31, 5)
            cmap = 'Purples'
            ylabel = 'Duration (Nº days)'
        elif mode == 'intensity':
            ds = self.ds_MHW_sliced
            levels = np.arange(0, 10, 1)
            cmap = 'gist_heat_r'
            ylabel = 'Max Intensity (ºC)'
        end = time.time()
        timu = end - start
        print('Time for creating levels: ' + str(timu))
        print('after levels')

        for i in range(0, ds.shape[0]):
            ax = self.ax_setter()
            print('Loop i: ' + str(i))
            start = time.time()
            temp = ax.contourf(lons, lats, ds[i, :, :], levels=levels, transform=ccrs.PlateCarree(),
                               cmap=cmap)
            end = time.time()
            timu = end - start
            print('Time to create temp: ' + str(timu))
            #if i == 0:
            cb = plt.colorbar(temp, location="bottom", ticks=levels, label=ylabel)
            plt.title(str(self.ds_time[i].values))
            # plt.show()
            print('hey')
            plt.savefig('../src/output_images/image_' + str(i) + '.png')
            print('hoy')
            filenames.append('../src/output_images/image_' + str(i) + '.png')
            ax.remove()
        return filenames

    def map_temperature(self, mode):
        lons, lats = self.lon, self.lat
        filenames = []
        filenames = self.__create_image_by_type(lons, lats, mode, filenames)
        # build gif
        with imageio.get_writer('../src/output_images/' + str(mode) + '_June_VJan23gif.gif', mode='I', duration=0.7) as writer:
            for filename in filenames:
                image = imageio.v3.imread(filename)
                writer.append_data(image)
        import os
        # Remove files
        for filename in set(filenames):
            os.remove(filename)

