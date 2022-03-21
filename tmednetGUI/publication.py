import sys, getopt, os

from datetime import datetime
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import file_manipulation as fm
import file_writer as fw
import user_interaction as ui
import numpy as np
import matplotlib.dates as mdates
from matplotlib.figure import Figure


# Gets the parameters from the command line to execute the publication script
# TODO can create hovmoller, keep working

class Arguments:

    def __init__(self):
        self.path = ""
        self.files = []
        self.mdata = []
        self.index = []
        self.newfiles = 0
        self.counter = []
        self.recoverindex = None
        self.recoverindexpos = None
        self.reportlogger = []
        self.tempdataold = []
        self.controlevent = False


def main(argv):
    inputdir = ''
    historical = ''
    try:
        opts, args = getopt.getopt(argv, 'hi:x:', ['idir=', 'hfile='])
    except getopt.GetoptError:
        print('publication.py -i <inputdirectory> -x <historicalfilepath>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('publication.py -i <inputdirectory> -x <historicalfilepath>')
            sys.exit()
        elif opt in ('-i', '--idir'):
            inputdir = arg
        elif opt in ('-x', '--hfile'):
            historical = arg
        print(opts)
    print('Input directory is ', inputdir)
    print('Historical file is ', historical)
    filepath = []
    files = []
    with os.scandir(inputdir) as entries:
        for entry in entries:
            filepath.append(inputdir + '/' + entry.name)
            files.append(entry.name)
    files.sort()
    filepath.sort()
    print(files)

    args = Arguments()
    args.path = inputdir + '/'
    args.files = files
    args.newfiles = len(files)

    fm.load_data(args)
    cut_endings(args)
    plot_hovmoller(args)
    print('Stratification Plot Done')
    plot_annualTCycle(args, historical)
    print('TCycles Plot Done')
    plot_thresholds(args, historical)
    print('Thresholds Plot Done')


def cut_endings(args):
    if args.mdata:
        # self.tempdataold = []
        for data in args.mdata:
            # self.tempdataold.append(data['temp'].copy())
            _, temperatures, indexes, start_index = fm.zoom_data(data)
            for i in indexes:
                data['temp'][int(i) - len(np.array(temperatures[1]))] = 999
            for i in range(0, int(start_index)):
                data['temp'][int(i)] = 999
        print('Endings of all the files cut')
    else:
        print('Error could not cut')


def plot_hovmoller(args):
    try:

        plt.rc('legend', fontsize='medium')
        fig = Figure(figsize=(5, 4), dpi=100, constrained_layout=True)
        plot = fig.add_subplot(111)
        fm.to_utc(args.mdata)
        global cb
        df, depths, _ = fm.list_to_df(args.mdata)
        depths = np.array(depths)

        levels = np.arange(np.floor(np.nanmin(df.values)), np.ceil(np.nanmax(df.values)), 1)
        cf = plot.contourf(df.index.to_pydatetime(), -depths, df.values.T, 256, extend='both', cmap='RdYlBu_r')

        cb = plt.colorbar(cf, ax=plot, label='Temperature (ºC)', ticks=levels)

        plot.set(ylabel='Depth (m)',
                 title='Stratification Site: ' + args.mdata[0]['region_name'])

        # Sets the X axis as the initials of the months
        locator = mdates.MonthLocator()
        plot.xaxis.set_major_locator(locator)
        fmt = mdates.DateFormatter('%b')
        plot.xaxis.set_major_formatter(fmt)
        # Sets the x axis on the top
        plot.xaxis.tick_top()

        plot.figure.savefig('Stratification_' + args.files[0][:-7] + '.png')
        print('Plotting the HOVMOLLER DIAGRAM at region: ' + str(args.mdata[0]['region']))
    except IndexError:
        print('Load several files before creating a diagram')
    except TypeError:
        print('Load more than a file for the Hovmoller Diagram')


def plot_annualTCycle(args, historical):
    # Gets the historical data to calculate the multi-year mean and deletes the old plots


    excel_object = fw.Excel(historical, write_excel=False, seasonal=False)  # returns an excel object
    histdf = excel_object.monthlymeandf

    dfdelta = fm.running_average(args.mdata, running=360)

    # All this block serves only to transform the data from hourly to daily. It should be inside its own method
    daylist = []
    for time in dfdelta.index:
        old = datetime.strftime(time, '%Y-%m-%d')
        new = datetime.strptime(old, '%Y-%m-%d')
        daylist.append(new)
    dfdelta['day'] = daylist
    newdf = None
    for depth in dfdelta.columns:
        if depth != 'day':
            if newdf is not None:
                newdf = pd.merge(newdf, dfdelta.groupby('day')[depth].mean(), right_index=True, left_index=True)
            else:
                newdf = pd.DataFrame(dfdelta.groupby('day')['5'].mean())

    # BLOCK ENDS HERE!!!!!!!

    # Dict to change from string months to datetime
    monthDict = {}
    for i in range(1, 13):
        if i < 10:
            monthDict['0'+str(i)] = datetime.strptime(datetime.strftime(dfdelta.index[0], '%Y')+'-0' + str(i) + '-01',
                                                      '%Y-%m-%d')
        else:
            monthDict[str(i)] = datetime.strptime(
                datetime.strftime(dfdelta.index[0], '%Y') + '-' + str(i) + '-01',
            '%Y-%m-%d')


    # Creates the subplots and deletes the old plot

    plt.rc('legend', fontsize='medium')
    fig = Figure(figsize=(5, 4), dpi=100, constrained_layout=True)
    plot = fig.add_subplot(111)


    for month in histdf['month'].unique():
        histdf['month'].replace(month, monthDict[month], inplace=True)
    usedf = histdf.copy()
    usedf.set_index('month', inplace=True)
    usedf.sort_index(inplace=True)
    oldepth = 0
    for depth in usedf['depth'].unique():
        if oldepth != 0:
            plot.fill_between(np.unique(usedf.index), usedf.loc[usedf['depth'] == oldepth]['mean'],
                                   usedf.loc[usedf['depth'] == depth]['mean'], facecolor='lightgrey')
        oldepth = depth

    for depth in histdf['depth'].unique():
        histdf.loc[histdf['depth'] == depth].plot(kind='line', x='month', y='mean', ax=plot, color='white',
                                                  label='_nolegend-', legend=False)


    newdf.plot(ax=plot)
    plot.set(ylabel='Temperature (ºC) smoothed',
                  title='Annual T Cycles')
    plot.set_ylim([10, 28]) #Sets the limits for the Y axis
    plot.legend(title='Depth (m)')

    #Sets the X axis as the initials of the months
    locator = mdates.MonthLocator()
    plot.xaxis.set_major_locator(locator)
    fmt = mdates.DateFormatter('%b')
    plot.xaxis.set_major_formatter(fmt)

    plot.xaxis.set_label_text('foo').set_visible(False)
            # fig.set_size_inches(14.5, 10.5, forward=True)
    plot.figure.savefig('Cositas al canal.png')

def plot_thresholds(args, historical):
    excel_object = fw.Excel(historical, write_excel=False)  # returns an excel object
    df = excel_object.mydf3

    # Creates the subplots and deletes the old plot
    plt.rc('legend', fontsize='medium')
    fig = Figure(figsize=(5, 4), dpi=100, constrained_layout=True)
    plot = fig.add_subplot(111)

    # Setting the properties of the line as lists to be used on a for loop depending on the year
    markers = ['+', 'o', 'x', 's', 'd', '^', 'v', 'p', 'h', '*']
    colors = ['b', 'b', 'k', 'k']
    lines = ['solid', 'dotted', 'solid', 'dotted']

    # Loop to decide each year which style has
    years = df['year'].unique()
    # Iterates through all the years and temperatures to create a dictionary storing the needed data to plot
    maxdepth = 0  # Used to set the lowest depth as the lowest point in the Y axis
    maxdays = 0   # Used to set the maximum number of days to point in the X axis
    temperatures = {23: [], 24: [], 25: [], 26: [], 28: []}
    year_dict = {}
    for year in years:
        for i in range(23, 29):
            yearly_plot = np.column_stack(
                (df.loc[df['year'] == year, 'Ndays>=' + str(i)], df.loc[df['year'] == year, 'depth(m)']))
            yearly_plot = yearly_plot.astype(int)
            if yearly_plot[-1, -1] > maxdepth:
                maxdepth = yearly_plot[-1, -1]
            if np.max(yearly_plot[:, 0]) > maxdays:
                maxdays = np.max(yearly_plot[:, 0])
            temperatures[i] = np.copy(yearly_plot)
        year_dict[year] = temperatures.copy()
        plot.set(ylim=(0, maxdepth + 2))
        plot.set(xlim=(-2, maxdays + 2))
        if int(year) < 2000:
            color = colors[0]
            if year == years[-1]:
                color = 'tab:orange'
            plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1], marker=markers[int(year) - 1990]
                           , color=color, linestyle=lines[0])
        elif int(year) >= 2000 and int(year) < 2010:
            color = colors[1]
            if year == years[-1]:
                color = 'tab:orange'
            plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1], marker=markers[int(year) - 2000],
                           color=color, linestyle=lines[1])
        elif int(year) >= 2010 and int(year) < 2020:
            color = colors[2]
            if year == years[-1]:
                color = 'tab:orange'
            plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1], marker=markers[int(year) - 2010],
                           color=color, linestyle=lines[2])
        elif int(year) >= 2020 and int(year) < 2030:
            color = colors[3]
            if year == years[-1]:
                color = 'tab:orange'
            plot.plot(year_dict[year][23][:, 0], year_dict[year][23][:, 1], marker=markers[int(year) - 2020],
                           color=color, linestyle=lines[3])

        plot.invert_yaxis()
        plot.xaxis.tick_top()

    #Shrink the axis a bit to fit the legend outside of it
    box = plot.get_position()
    plot.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Draws the legend for the different years
    plot.legend(years, title='Year', loc='center left', bbox_to_anchor=(1, 0.5))
    plot.set(ylabel='Depth (m)',
                  title=args.mdata[0]['region_name'] + ' Summer days ≥ 23ºC')
    plot.figure.savefig('thisonesgood.png')
    

#TODO this works wonders, add it to the console onscreen on the GUI
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd=''):
    percent = ('{0:.' + str(decimals) + 'f}').format(100* (iteration/float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end= printEnd)
    if iteration == total:
        print()

if __name__ == '__main__':
    main(sys.argv[1:])