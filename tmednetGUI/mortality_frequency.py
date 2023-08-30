import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import patches as ptch
from matplotlib.colors import ListedColormap, BoundaryNorm
import time
import seaborn as sns
import math
import imageio
import logging
import calendar
import numpy as np
import xarray as xr
import pandas as pd
from sys import _getframe
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from typing import Literal, get_args, get_origin
from shapely.validation import make_valid
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

class MME_Plot:

    def __init__(self, PATH):
        self.df_events = pd.read_excel('../src/MME.xlsx', sheet_name='Quim Years with MME')
        self.df_numbers = pd.read_excel('../src/MME.xlsx', sheet_name='Massimo original dataset')
        self.df_fishes = pd.read_excel('../src/Example_Visual_census_ALL.xlsx', 'DATA-All')
        self.df_corals = pd.read_excel('../src/Mortality Atención Corales.xlsx', 'Mortality Data')
        df_coords = pd.read_excel('../src/Coords.xlsx')
        self.df_map = pd.merge(self.df_events, df_coords[['id.hexagon', 'Lat', 'Lon']], on='id.hexagon', how='left')
        self.df_events.columns = self.df_events.columns.astype(str)
        self.columns = self.df_events.columns[4:]
        self.coords = pd.read_csv('../src/Ecoregion coords.csv')

    def plot_return_time_regional(self, reg):
        plt.clf()
        df_scatter = self.create_scatter_dataframe()
        df_reg = df_scatter.loc[df_scatter['sub-ecoregion'] == reg]
        df = self.create_dict_df(df_reg)
        df_sorted_yearly = self.create_dataframe_sorted(df)
        min_size = np.min(df_sorted_yearly['Count']) * 10
        max_size = np.max(df_sorted_yearly['Count']) * 10
        ax_scatter_years2 = sns.scatterplot(df_sorted_yearly, x='Year', y='Return tax', size='Count', sizes=(min_size, max_size),
                                            alpha=.5, legend='brief')
        ax_scatter_years2 = sns.lineplot(df_sorted_yearly, x='Year', y='Max Return', color='k')
        ax_scatter_years2 = sns.regplot(df_sorted_yearly, x='Year', y='Mean', ci=None, color='tab:orange')
        leg = plt.legend(loc='upper right', labels=['Max return years', 'Regression', 'Nº of Events'])
        ax_scatter_years2.add_artist(leg)
        plt.legend(loc=[0.8, 0.3])
        plt.title(reg)
        ax_scatter_years2.set(ylabel='Return Years')
        plt.savefig('../src/output_images/Returning Time_' + reg + '.png',
                    bbox_inches='tight')
        print('ha')

    def create_scatter_dataframe(self):
        df_return = self.df_events.copy()
        ret_counter = 0
        old_year = ''
        for idx, row in self.df_events.iterrows():
            for year in self.columns:
                if row[year] == 1 or year == self.columns[-1]:
                    if year == '2020':
                        print('ye')
                    ret_counter = ret_counter + 1
                    if old_year == '':
                        old_year = year
                        if year == self.columns[-1]:
                            old_year = ''
                            ret_counter = 0
                            df_return[year][idx] = np.nan
                    else:
                        if year == self.columns[-1]:
                            df_return[old_year][idx] = np.nan
                            df_return[year][idx] = np.nan
                            old_year = ''
                            ret_counter = 0
                        else:
                            if ret_counter - 1 <= 0:
                                df_return[old_year][idx] = np.nan
                            else:
                                df_return[old_year][idx] = ret_counter - 1
                            ret_counter = 1
                            old_year = year
                else:
                    df_return[year][idx] = np.nan
                    if ret_counter != 0:
                        ret_counter = ret_counter + 1

        df_scatter = df_return.melt(id_vars=['sub-ecoregion', 'id.hexagon', '#Years with MME',
                                             '#Records MMEs_All_years_'], var_name='Year', value_name='Return time')

        df_scatter['Year'] = df_scatter['Year'].astype(int)

        return df_scatter

    def create_dict_df(self, df_scatter):
        dict_for_yearly = {'Year': '', 'Return years': 0, 'Count': 0}

        dict_list_yearly = []
        for i in range(1, 41):
            for year in df_scatter['Year'].unique():
                dict_for_yearly['Year'] = year
                dict_for_yearly['Return years'] = i
                dict_for_yearly['Count'] = df_scatter['Return time'].loc[
                    (df_scatter['Year'] == year) & (df_scatter['Return time'] == i)].count()
                dict_list_yearly.append(dict_for_yearly.copy())

        df = pd.DataFrame.from_records(dict_list_yearly)

        return df

    def create_dataframe_sorted(self, df):
        df_sorted_yearly = df.sort_values(['Year', 'Return years']).reset_index()
        df_sorted_yearly.loc[df_sorted_yearly['Count'] > 0, 'Return tax'] = df_sorted_yearly.loc[
            df_sorted_yearly['Count'] > 0, 'Return years']
        df_sorted_yearly.loc[df_sorted_yearly['Count'] == 0, 'Count'] = np.nan
        df_sorted_yearly['Max Return'] = df_sorted_yearly['Year'].max() - df_sorted_yearly['Year']
        df_sorted_yearly['Cum years'] = df_sorted_yearly['Return years'] * df_sorted_yearly['Count']
        df_sorted_yearly['Mean'] = np.nan
        df_sorted_yearly['Mean'] = round(
            df_sorted_yearly.loc[df_sorted_yearly['Return tax'] > 0].groupby(df_sorted_yearly['Year'])[
                'Cum years'].transform('sum') /
            df_sorted_yearly.loc[df_sorted_yearly['Return tax'] > 0].groupby(df_sorted_yearly['Year'])[
                'Count'].transform('sum'), 2)
        return df_sorted_yearly

    def plot_return_time(self):
        plt.clf()
        df_scatter = self.create_scatter_dataframe()
        df = self.create_dict_df(df_scatter)
        df_sorted_yearly = self.create_dataframe_sorted(df)
        min_size = np.min(df_sorted_yearly['Count']) * 10
        max_size = np.max(df_sorted_yearly['Count']) * 10
        ax_scatter_years = sns.scatterplot(df_sorted_yearly, x='Year', y='Return tax', size='Count', sizes=(min_size, max_size),
                                           alpha=.5, legend='brief')
        ax_scatter_years = sns.lineplot(df_sorted_yearly, x='Year', y='Max Return', color='k')
        ax_scatter_years = sns.regplot(df_sorted_yearly, x='Year', y='Mean', color='tab:orange')
        leg = plt.legend(loc='upper right', labels=['Max return years', 'Regression', 'Nº of Events'])
        ax_scatter_years.add_artist(leg)
        plt.legend(loc=[0.8, 0.5])
        ax_scatter_years.set(ylabel='Return Years')
        self.save_image('Returning Time_Mediterranean')
        
    def plot_map_regional(self, reg):
        # Use only the pixels with more than a year of mortality
        self.df_map = self.df_map.loc[self.df_map['#Years with MME'] > 1]
        df = self.df_map.loc[self.df_map['sub-ecoregion'] == reg]
        if (reg == 'Southwestern Mediterranean') or (reg == 'Northwestern Mediterranean'):
            reg_df = self.coords.loc[self.coords['ECOREGION'] == 'Western Mediterranean']
        else:
            reg_df = self.coords.loc[self.coords['ECOREGION'] == reg]
        print('Before setting axes for ' + reg)
        ax, gl = self.ax_setter(float(reg_df['Lat1']), float(reg_df['Lat2']), float(reg_df['Lon1']), float(reg_df['Lon2']))
        print('Axes set')
        cmap = 'autumn_r'
        nyears = ax.scatter(x=df['Lon'], y=df['Lat'], c=df['#Years with MME'],
                            transform=ccrs.PlateCarree(), cmap=cmap, alpha=0.7, s=15, edgecolor='blue', linewidths=0.5)
        cb = plt.colorbar(nyears, ticks=range(0, 41), label='No of Years with MME')
        print('Plotted, time to save')
        plt.title(reg)
        self.save_image('Years per pixel_' + reg)

    def regional_returntime_composer(self):
        self.loop_ecoregion(self.plot_return_time_regional)
    def regional_map_composer(self):
        self.loop_ecoregion(self.plot_map_regional)
    def plot_data_map(self):
        '''plt.clf()
        # Use only the pixels with more than a year of mortality
        self.df_map = self.df_map.loc[self.df_map['#Years with MME'] > 1]
        ax, gl = self.ax_setter()
        cmap = 'autumn_r'
        nyears = ax.scatter(x=self.df_map['Lon'], y=self.df_map['Lat'], c=self.df_map['#Years with MME'],
                            transform=ccrs.PlateCarree(), cmap=cmap, alpha=0.7, s=15, edgecolor='blue', linewidths=0.5)
        cb = plt.colorbar(nyears, ticks=range(0, 41), label='No of Years with MME')'''
        plt.clf()
        cmap = 'autumn_r'
        #self.df_map['Record range'] = (self.df_map['#Records MMEs_All_years_']/10).apply(np.floor)*10
        #Set the categories
        self.df_map['Record range'] = self.df_map['#Records MMEs_All_years_'].apply(
            lambda y: 0.2 if y < 10 else (0.4 if y < 50 else (0.6 if y < 100 else (0.8 if y < 200 else 1))))
        self.df_map['Log10 Records'] = np.log10(self.df_map['#Records MMEs_All_years_'])
        ax, gl = self.ax_setter()
        nyears = ax.scatter(x=self.df_map['Lon'], y=self.df_map['Lat'], c=self.df_map['Log10 Records'],
                            transform=ccrs.PlateCarree(), alpha=1, s=15, edgecolor='blue', linewidths=0.5, cmap=cmap)
        cb = plt.colorbar(nyears, label='No of Records across all years')
        cb.set_ticks([np.log10(1), np.log10(10), np.log10(50), np.log10(100), np.log10(200)])
        cb.set_ticklabels(['1-10', '10-50', '50-100', '100-200', '>200'])
        self.save_image('Records across years Map')
    def plot_affected_percentage(self):
        y_axis = self.df_events['#Years with MME'].unique()
        y_axis.sort()
        total_hex = self.df_events['#Years with MME'].count()
        df_inc = pd.DataFrame([self.df_events['#Years with MME'].loc[self.df_events['#Years with MME'] == i].count() for i in y_axis],
                              columns=['count'])
        df_inc['% affected'] = (df_inc['count'] / total_hex) * 100
        df_inc['N affected'] = df_inc['count']
        df_inc['y_axis'] = y_axis
        ax = df_inc.plot.bar(x='y_axis', y='% affected')
        ax.set_xlabel('Years with MME')
        ax.set_ylabel('Percentage of affected hexagons')
        ax.set_ylim([0, 70])
        plt.xticks(rotation=0)
        ax.get_legend().remove()
        plt.title('Mediterranean MME')
        self.save_image('MME_Global')

    def plot_affected_number(self):
        df_third = self.get_numbered_df()
        df_third['Year'] = df_third['Year'].astype(int)
        ax = df_third.plot.bar(x='Year', y='Count', figsize=(10, 5))
        ax.set_xlabel('Year')
        ax.set_ylabel('Number of affected hexagons')
        ax.set_ylim([0, df_third['Count'].max() + 25])
        plt.xticks(rotation=90)
        ax.get_legend().remove()
        plt.title('Mediterranean MME')
        self.save_image('MME_N_Global')

    def get_numbered_df(self):
        df_third = pd.DataFrame(self.columns, columns=['Year'])
        df_third['Count'] = 0
        for year in self.columns:
            df_third['Count'].loc[df_third['Year'] == year] = self.df_events[year].sum()
        return df_third

    def save_image(self, title):
        plt.savefig('../src/output_images/' + title + '.png',
                    bbox_inches='tight')

    def affected_percentage_regional_composer(self):
        self.loop_ecoregion(self.plot_affected_percentage_regional)

    def affected_numbers_regional_composer(self):
        self.loop_ecoregion(self.plot_affected_numbers_regional)

    def loop_ecoregion(self, func):
        for n in self.df_events['sub-ecoregion'].unique():
            func(n)

    def plot_affected_percentage_regional(self, reg):
        y_axis = self.df_events['#Years with MME'].loc[self.df_events['sub-ecoregion'] == reg].unique()
        y_axis.sort()
        total_hex = self.df_events['#Years with MME'].loc[self.df_events['sub-ecoregion'] == reg].count()
        df_inc = pd.DataFrame(
            [self.df_events['#Years with MME'].loc[(self.df_events['#Years with MME'] == i) & (self.df_events['sub-ecoregion'] == reg)].count() for i in
             y_axis],
            columns=['count'])
        df_inc['% affected'] = (df_inc['count'] / total_hex) * 100
        df_inc['N affected'] = df_inc['count']
        df_inc['y_axis'] = y_axis
        ax = df_inc.plot.bar(x='y_axis', y='% affected')
        ax.set_xlabel('Years with MME')
        ax.set_ylabel('Percentage of affected hexagons')
        ax.set_ylim([0, 100])
        plt.xticks(rotation=0)
        ax.get_legend().remove()
        plt.title(reg + ' MME')
        self.save_image('MME_' + reg)

    def plot_affected_numbers_regional(self, reg):
        df_third = self.get_numbered_df()
        total_max = df_third['Count'].max()
        for year in self.columns:
            df_third['Count'].loc[df_third['Year'] == year] = self.df_events[year].loc[self.df_events['sub-ecoregion'] == reg].sum()
        ax = df_third.plot.bar(x='Year', y='Count', figsize=(10, 5))
        ax.set_xlabel('Year')
        ax.set_ylabel('Number of affected hexagons')
        ax.set_ylim([0, total_max + 25])
        plt.xticks(rotation=90)
        ax.get_legend().remove()
        plt.title(reg + ' MME')
        self.save_image('MME_N_' + reg)

    def setup_heatmap_base(self):
        events_copy = self.df_events.copy()
        events_copy.replace(0, np.nan, inplace=True)
        events_copy.index = events_copy['sub-ecoregion']
        for i in self.df_events.columns[:4]:
            del events_copy[i]
        myColors = ((1.0, 1.0, 1.0, 1.0), (0.8, 0.0, 0.0, 1.0))
        cmap = LinearSegmentedColormap.from_list('Custom', myColors, len(myColors))
        return events_copy, cmap

    def plot_heatmap_base(self):
        plt.clf()
        events_copy, cmap = self.setup_heatmap_base()
        reg = events_copy.index.unique()
        yticks = []
        for i in reg:
            yticks.append(events_copy.index.get_indexer_for((events_copy[events_copy.index == i].index))[0])
        num_ticks = len(reg)
        reg_list = events_copy.index
        # the content of labels of these yticks
        yticklabels = [reg_list[idx] for idx in yticks]

        ax = sns.heatmap(events_copy, cmap=cmap, yticklabels=yticklabels, vmax=1, vmin=0, cbar_kws={'ticks': [0, 1]})
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels)
        self.save_image('Heatmap Global')

    def plot_heatmap_base_regional(self, reg):
        events_copy, cmap = self.setup_heatmap_base()
        plt.clf()
        ax = sns.heatmap(events_copy.loc[events_copy.index == reg], cmap=cmap, yticklabels=False, vmax=1, vmin=0,
                         cbar_kws={'ticks': [0, 1]})
        ax.set_ylabel(reg)
        self.save_image('Heatmap ' + reg)

    def heatmap_base_composer(self):
        self.loop_ecoregion(self.plot_heatmap_base_regional)

    def plot_fish_assesment(self):
        plt.clf()
        ax, gl = self.ax_setter()
        cmap = self.fish_assesment()
        asses = ax.scatter(x=self.df_fishes['LONG'], y=self.df_fishes['LAT'], c=self.df_fishes['Assesment'],
                           transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                           vmax=3, zorder=10)
        cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
        cb.set_ticklabels(['Tempered', 'Warm', 'Tropicalized', 'Highly Tropicalized'])
        self.save_image('Fish Assesment')

    def plot_fish_assesment_zoom(self):
        plt.clf()
        ax, gl = self.ax_setter(lat1=-5.49, lat2=21.60, lon1=35.82, lon2=45.86)
        cmap = self.fish_assesment()
        asses = ax.scatter(x=self.df_fishes['LONG'], y=self.df_fishes['LAT'], c=self.df_fishes['Assesment'],
                           transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                           vmax=3, zorder=10)
        cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
        cb.set_ticklabels(['Tempered', 'Warm', 'Tropicalized', 'Highly Tropicalized'])
        self.save_image('Fish Assesment_Zoom')

    def fish_assesment(self):
        self.df_fishes['Assesment'] = self.df_fishes['Tropical. Index'].apply(
            lambda y: 0 if y <= 1 else (1 if y <= 3 else (2 if y <= 5 else 3)))
        colors = ['green', 'yellow', 'orange', 'red']
        cmap = LinearSegmentedColormap.from_list('Custom', colors, len(colors))
        return cmap

    def plot_yearly_fish_assesment(self):
        for year in self.df_fishes['YEAR'].unique():
            plt.clf()
            ax, gl = self.ax_setter()
            cmap = self.fish_assesment()
            df = self.df_fishes.loc[self.df_fishes['YEAR'] == year]
            asses = ax.scatter(x=df['LONG'], y=df['LAT'], c=df['Assesment'],
                               transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                               vmax=3, zorder=10)
            cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
            cb.set_ticklabels(['Tempered', 'Warm', 'Tropicalized', 'Highly Tropicalized'])
            plt.title('Fish census ' + str(year))
            self.save_image('Fish Assesment ' + str(year))

    def plot_yearly_fish_assesment_zoom(self):
        for year in self.df_fishes['YEAR'].unique():
            plt.clf()
            ax, gl = self.ax_setter(lat1=-5.49, lat2=21.60, lon1=35.82, lon2=45.86)
            cmap = self.fish_assesment()
            df = self.df_fishes.loc[self.df_fishes['YEAR'] == year]
            asses = ax.scatter(x=df['LONG'], y=df['LAT'], c=df['Assesment'],
                               transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                               vmax=3, zorder=10)
            cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
            cb.set_ticklabels(['Tempered', 'Warm', 'Tropicalized', 'Highly Tropicalized'])
            plt.title('Fish census ' + str(year))
            self.save_image('Fish Assesment Zoom ' + str(year))

    def plot_mortality_assesment(self):
        ax, gl = self.ax_setter()
        cmap = self.mortality_assesment()
        asses = ax.scatter(x=self.df_corals['LONG'], y=self.df_corals['LAT'], c=self.df_corals['Assesment'],
                           transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                           vmax=3, zorder=10)
        cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
        cb.set_ticklabels(['No Impact', 'Low Impact', 'Moderate Impact', 'High Impact'])
        self.save_image('Mortality Assesment')

    def plot_mortality_assesment_zoom(self):
        ax, gl = self.ax_setter(lat1=-5.49, lat2=21.60, lon1=35.82, lon2=45.86)
        cmap = self.mortality_assesment()
        asses = ax.scatter(x=self.df_corals['LONG'], y=self.df_corals['LAT'], c=self.df_corals['Assesment'],
                           transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                           vmax=3, zorder=10)
        cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
        cb.set_ticklabels(['No Impact', 'Low Impact', 'Moderate Impact', 'High Impact'])
        self.save_image('Mortality Assesment Zoom')

    def mortality_assesment(self):
        indx = self.df_corals.loc[self.df_corals['Total colonies'] == 0].index
        self.df_corals.drop(index=indx, inplace=True)
        self.df_corals['Assesment'] = self.df_corals['% Affected all'].apply(
            lambda y: 0 if y <= 10 else (1 if y <= 30 else (2 if y < 60 else 3)))
        colors = ['green', 'yellow', 'orange', 'red']
        cmap = LinearSegmentedColormap.from_list('Custom', colors, len(colors))
        return cmap

    def plot_yearly_mortality_assesment(self):
        for year in self.df_corals['YEAR'].unique():
            plt.clf()
            ax, gl = self.ax_setter()
            cmap = self.mortality_assesment()
            df = self.df_corals.loc[self.df_corals['Year'] == year]
            asses = ax.scatter(x=df['LONG'], y=df['LAT'], c=df['Assesment'],
                               transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                               vmax=3, zorder=10)
            cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
            cb.set_ticklabels(['No Impact', 'Low Impact', 'Moderate Impact', 'High Impact'])
            plt.title('Mortality Assesment ' + str(year))
            self.save_image('Mortality Assesment ' + str(year))

    def plot_yearly_mortality_assesment_zoom(self):
        for year in self.df_corals['Year'].unique():
            plt.clf()
            ax, gl, fig = self.ax_setter(lat1=-5.49, lat2=21.60, lon1=35.82, lon2=45.86, subplot=True)
            cmap = self.mortality_assesment()
            df = self.df_corals.loc[self.df_corals['Year'] == year]
            df_histo = df['% Affected all'].sort_values(ascending=False).reset_index()
            asses = ax.scatter(x=df['LONG'], y=df['LAT'], c=df['Assesment'],
                               transform=ccrs.PlateCarree(), s=20, cmap=cmap, edgecolor='blue', linewidth=0.2, vmin=0,
                               vmax=3, zorder=10)
            cb = plt.colorbar(asses, ticks=range(0, 5), label='Assesment')
            cb.set_ticklabels(['No Impact', 'Low Impact', 'Moderate Impact', 'High Impact'])
            plt.title('Mortality Assesment ' + str(year))
            ax2 = fig.add_subplot(2,1,2)
            ax2.bar(df_histo.index, df_histo['% Affected all'])
            ax2.set_xticks([])
            ax2.set_ylim([0, 100])
            ax2.set_ylabel('% Affected all')
            ax2.axhline(y = 10, color = 'g', linestyle = '-', alpha=0.3)
            ax2.axhline(y=30, color='yellow', linestyle='-', alpha=0.3)
            ax2.axhline(y=60, color='orange', linestyle='-', alpha=0.3)


            ax2.add_patch(plt.Rectangle((-1,0), len(df_histo.index) + 1, 10, facecolor='green', alpha=0.3))
            ax2.add_patch(plt.Rectangle((-1, 10), len(df_histo.index) + 1, 20, facecolor='yellow', alpha=0.3))
            ax2.add_patch(plt.Rectangle((-1, 30), len(df_histo.index) + 1, 30, facecolor='orange', alpha=0.3))
            ax2.add_patch(plt.Rectangle((-1, 60), len(df_histo.index) + 1, 40, facecolor='red', alpha=0.3))
            print('Year ' + str(year) + ' Plotter')
            self.save_image('Mortality Assesment Zoom + Histogram ' + str(year))

    @staticmethod
    def ax_setter(lat1=-9.5, lat2=37., lon1=28., lon2=50., subplot=False):
        """
        Creates the axes where the map will be plotted selecting the coordinates to properly represent
        the Mediterranean sea and plots and colors the land and sea.

        Returns
        -------
        ax : Axes matplotlib
            the axes in which the data will be plotted
        gl : Gridlines
            the gridlines of the plot featured to divide the latitude and longitude
        """
        if not subplot:
            rows = 1
        else:
            rows = 2

        fig = plt.figure(figsize=(20 / 2.54, 15 / 2.54))

        ax = fig.add_subplot(rows, 1, 1, projection=ccrs.Mercator())
        ax.set_extent([lat1, lat2, lon1, lon2], crs=ccrs.PlateCarree())
        ax.add_feature(cf.OCEAN)
        ax.add_feature(cf.LAND)
        ax.coastlines(resolution='10m')
        ax.add_feature(cf.BORDERS, linestyle=':', alpha=1)

        gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=1, color='grey', alpha=0.3, linestyle='--',
                          draw_labels=True)
        gl.top_labels = False
        gl.left_labels = True
        gl.right_labels = False
        gl.xlines = True
        # gl.xlocator = mticker.FixedLocator([120, 140, 160, 180, -160, -140, -120])
        # gl.ylocator = mticker.FixedLocator([0, 20, 40, 60])
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        # gl.xlabel_style = {'color': 'red', 'weight': 'bold'}
        p = ax.get_window_extent()
        '''plt.annotate('Source: T-MEDNet MHW Tracker / Generated using E.U. Copernicus Marine Service information',
                     xy=(-0.2, -0.3), xycoords=p, xytext=(0.1, 0),
                     textcoords="offset points",
                     va="center", ha="left")'''
        plt.annotate('t-mednet.org', xy=(0.01, 0.03), xycoords=p, xytext=(0.1, 0),
                     textcoords="offset points",
                     va="center", ha="left", alpha=0.5)

        if not subplot:
            return ax, gl
        else:
            return ax, gl, fig



'''
ex = pd.read_excel('../src/MME.xlsx', sheet_name='Quim Years with MME')
ex.columns = ex.columns.astype(str)
columns = ex.columns[4:]

df_third = pd.DataFrame(columns, columns=['Year'])
df_third['Count'] = 0
for year in columns:
    df_third['Count'].loc[df_third['Year'] == year] = ex[year].sum()
y_axis = ex['#Years with MME'].unique()
y_axis.sort()
total_hex = ex['#Years with MME'].count()

#Dataframe for counting N of MME per

df_third['Year'] = df_third['Year'].astype(int)
ax = df_third.plot.bar(x='Year', y='Count', figsize = (10, 5))
ax.set_xlabel('Year')
ax.set_ylabel('Number of affected hexagons')
ax.set_ylim([0, df_third['Count'].max() + 25])
plt.xticks(rotation=90)
ax.get_legend().remove()
plt.title('Mediterranean MME')
plt.savefig('../src/output_images/MME_N_Global.png',
                                bbox_inches='tight')
for n in ex['sub-ecoregion'].unique():


    for year in columns:
        df_third['Count'].loc[df_third['Year'] == year] = ex[year].loc[ex['sub-ecoregion'] == n].sum()
    ax = df_third.plot.bar(x='Year', y='Count', figsize = (10, 5))
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of affected hexagons')
    ax.set_ylim([0, df_third['Count'].max() + 25])
    plt.xticks(rotation=90)
    ax.get_legend().remove()
    plt.title(n + ' MME')
    plt.savefig('../src/output_images/MME_N_' + n + '.png',
                bbox_inches='tight')

df_return = ex.copy()
ret_counter = 0
old_year = ''
for idx, row in ex.iterrows():
    for year in columns:
        if row[year] == 1 or year == columns[-1]:
            if year == '2020':
                print('ye')
            ret_counter = ret_counter + 1
            if old_year == '':
                old_year = year
                if year == columns[-1]:
                    old_year = ''
                    ret_counter = 0
                    df_return[year][idx] = np.nan
            else:
                if year == columns[-1]:
                    df_return[old_year][idx] = np.nan
                    df_return[year][idx] = np.nan
                    old_year = ''
                    ret_counter = 0
                else:
                    if ret_counter - 1 <= 0:
                        df_return[old_year][idx] = np.nan
                    else:
                        df_return[old_year][idx] = ret_counter - 1
                    ret_counter = 1
                    old_year = year
        else:
            df_return[year][idx] = np.nan
            if ret_counter != 0:
                ret_counter = ret_counter + 1

df_scatter = df_return.melt(id_vars=['sub-ecoregion', 'id.hexagon', '#Years with MME',
       '#Records MMEs_All_years_'], var_name='Year', value_name='Return time')

df_scatter['Year'] = df_scatter['Year'].astype(int)
ax2 = df_scatter.plot.scatter(x='Year', y='Return time')
ax2.set_xlabel('Year')
ax2.set_ylabel('Number of years to return')
ax2.set_ylim([0, 40])
ax2.set_xlim([1978, 2020])
plt.title('Mediterranean Return Time')
plt.savefig('../src/output_images/RT_Global.png', bbox_inches='tight')

#Create a list of decades
decade_list = []
i = df_scatter['Year'].unique()[0]
while i < df_scatter['Year'].unique()[-1]:
    new_i = round((i + 10) / 10) * 10
    decade_list.append(str(i) + '-' + str(new_i))
    i = new_i + 1

dict_for_df = {'Decade' : '', 'Return years' : 0, 'Count' : 0}
dec_sum = 0
oldi_year = 0
for i in range(1, 11):
    for year in df_scatter['Year'].unique():
        if oldi_year == 0:
            oldi_year = year
        dec_sum = df_scatter['Return time'].loc[(df_scatter['Year'] == year) & (df_scatter['Return time'] == i)].count() + dec_sum
        if year-10 == round(oldi_year/10)*10:
            dict_for_df['Decade'] = str(oldi_year) + '-' + str(year)
            dict_for_df['Return years'] = i
            dict_for_df['Count'] = dec_sum

dec_sum = dict.fromkeys(df_scatter['Year'].unique(), 0)
for year in df_scatter['Year'].unique():
    for i in range(1, 11):
        dec_sum[year] = df_scatter.loc[(df_scatter['Year'] == year) & (df_scatter['Return time'] == i)].count() + dec_sum


for n in ex['sub-ecoregion'].unique():
    ux = ex.loc[ex['sub-ecoregion'] == n]
    df_return = ux.copy()
    ret_counter = 0
    old_year = ''
    for idx, row in ux.iterrows():
        for year in columns:
            if row[year] == 1 or year == columns[-1]:
                ret_counter = ret_counter + 1
                if old_year == '':
                    old_year = year
                    if year == columns[-1]:
                        old_year = ''
                        ret_counter = 0
                        df_return[year][idx] = np.nan
                else:
                    if year == columns[-1]:
                        df_return[old_year][idx] = np.nan
                        df_return[year][idx] = np.nan
                        old_year = ''
                        ret_counter = 0
                    else:
                        if ret_counter - 1 <= 0:
                            df_return[old_year][idx] = np.nan
                        else:
                            df_return[old_year][idx] = ret_counter - 1
                        ret_counter = 1
                        old_year = year
            else:
                df_return[year][idx] = np.nan
                if ret_counter != 0:
                    ret_counter = ret_counter + 1
    df_scatter = df_return.melt(id_vars=['sub-ecoregion', 'id.hexagon', '#Years with MME',
                                         '#Records MMEs_All_years_'], var_name='Year', value_name='Return time')

    df_scatter['Year'] = df_scatter['Year'].astype(int)
    ax2 = df_scatter.plot.scatter(x='Year', y='Return time')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Number of years to return')
    ax2.set_ylim([0, 40])
    ax2.set_xlim([1978, 2020])
    plt.title(n + 'Return Time')
    plt.savefig('../src/output_images/RT_' + n + '.png',
                bbox_inches='tight')

print('stop')

'''