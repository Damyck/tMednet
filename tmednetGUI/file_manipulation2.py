import os
import re
import time
import json
import xarray
import numpy as np
import pdf_creator
import pandas as pd
from numpy import diff
from netCDF4 import Dataset
import user_interaction as ui
from geojson import Point, Feature, dump
from datetime import datetime, timedelta
from scipy.ndimage.filters import uniform_filter1d
import progressbar as pb


class DataManager:

    def __init__(self, console):
        self.path = ""
        self.files = []
        self.mdata = []
        self.index = []
        self.newfiles = 0
        self.recoverindex = None
        self.recoverindexpos = None
        self.reportlogger = []
        self.tempdataold = []
        self.controlevent = False
        self.console_writer = console
        print('hello')

    def openfile(self, files, textBox, lister):
        """
        Method: openfile(self, files, consolescreen)
        Purpose: Opens the files to be used with the GUI
        Require:
            self: The mdata
            files: The filenames to be opened
            consolescreen: In order to write to the console
        Version: 01/2021, EGL: Documentation
        """

        filesname = []
        self.newfiles = 0
        nf = len(files)
        try:
            if nf > 0:
                self.path = "/".join(files[0].split("/")[:-1]) + "/"
                for ifile in files:
                    _, file_extension = os.path.splitext(ifile)
                    if file_extension != '.txt' and file_extension != '.csv':
                        raise ValueError('Error, file not loadable')
                    filesname.append(ifile.split("/")[-1])

                print(self.path, "files: ", filesname)

                # Escric els fitxers a la pantalla principal
                textBox.insert("end", 'Hem carregat: ' + str(nf) + ' files \n')
                textBox.insert("end", '\n'.join(filesname))
                if lister.size() != 0:  # Checks if the list is empty. If it isn't puts the item at the end of the list
                    n = lister.size()
                    for i in range(len(filesname)):
                        lister.insert(i + n, filesname[i])
                        self.newfiles = self.newfiles + 1
                else:
                    for i in range(len(filesname)):
                        lister.insert(i, filesname[i])
                        self.newfiles = self.newfiles + 1

            return filesname
        except (ValueError, TypeError) as err:
            self.console_writer(repr(err), 'warning')

    def load_data(self):
        """
        Method: load_data(self, consolescreen)
        Purpose: read tmednet *.txt data files
        Require:
            self: For the mdata dictionary
            consolescreen: In order to write to the consolescreen
        Version: 05/2021, MJB: Documentation
        """
        try:
            # Iterates based on the last entry on self.files to not overwrite
            for ifile in self.files[len(self.files) - self.newfiles:]:
                filein = self.path + ifile

                lat, lon, site_name = self.load_coordinates(int(ifile.split('_')[0]))
                # Extraemos campos del nombre del fichero
                datos = {"df": [], "S/N": "", "GMT": "",
                         "depth": int(ifile.split("_")[3].split(".")[0]), "region": int(ifile.split("_")[0]),
                         'region_name': site_name, "latitude": lat, "longitude": lon,
                         "datainici": datetime.strptime(ifile.split("_")[1], '%Y%m%d-%H'),
                         "datafin": datetime.strptime(ifile.split("_")[2], '%Y%m%d-%H'), 'images': []}

                # Loads the data on a dataframe
                df = pd.read_csv(filein, sep='\t', skiprows=1, header=None, index_col=0)
                col = df.columns
                df.drop(col[3:], axis=1, inplace=True)
                df.columns = ['Date', 'Time', 'Temp']
                df.dropna(inplace=True)
                print("file", filein)
                self.console_writer(filein, 'action')

                f = open(filein, "r", encoding='iso-8859-15')
                meta = f.readline()
                meta = re.sub('\t+', ' ', meta.strip()).split(' ')
                f.close()
                df.index = [datetime.strptime(df['Date'][i] + ' ' + df['Time'][i], "%d/%m/%y %H:%M:%S") for i
                            in
                            range(1, len(df) + 1)]
                df.drop(['Date', 'Time'], axis=1, inplace=True)
                datos['df'] = df
                igm = '_'.join(meta).find("GMT")
                gmtout = '_'.join(meta)[igm + 3:igm + 6]
                datos['GMT'] = gmtout
                try:
                    datos['S/N'] = int(re.sub('\D', '', meta[meta.index('S/N:') + 1]))
                except:
                    datos['S/N'] = 'XXXXXXXX'
                self.mdata.append(datos)
                self.tempdataold.append(datos.copy())
            self.mdata = sorted(self.mdata, key=lambda k: k['depth'])
            self.tempdataold = sorted(self.tempdataold, key=lambda k: k['depth'])
            self.to_utc()
            self.check_start()
            self.interpolate_hours()  # Interpolates the temperature between different not round hours

        except ValueError:
            self.console_writer("Error, file extension not supported, load a txt",'warning')

    def load_coordinates(self, region):
        """
        Method: load_coordinates(region)
        Purpose: Loads the coordinates of the file from the 'metadata.json' auxiliary file
        Require:
            region: The number of the site where the data is taken from
        Version: 05/2021, MJB: Documentation
        """
        with open('../src/metadata.json') as f:
            data = json.load(f)
        lat = float(data['stations'][str(region)]['lat'])
        lon = float(data['stations'][str(region)]['long'])
        name = data['stations'][str(region)]['site_name']
        return lat, lon, name

    def check_start(self):
        """
            Method: check_start(data)
            Purpose: Checks that the start time is correct
            Require:
                data: The mdata
            Version: 11/2021, MJB: Documentation
        """
        for dat in self.mdata:
            titlestart = dat['datainici'].timestamp()
            filestart = dat['df'].index[0].timestamp()
            if titlestart < filestart:
                self.console_writer("Error, start date on the title of the file set before the start date of the "
                                     "file in depth " + str(dat['depth']), 'warning')

    def interpolate_hours(self):
        """
        Method: interpolate_hours(data)
        Purpose: Interpolates the values of temp in case the hours are not round
        Require:
            data: The mdata
        Version: 05/2021, MJB: Documentation
        """
        for dat in self.mdata:
            for i in range(len(dat['df'].index)):
                if dat['df'].index[i].timestamp() % 3600 == 0:  # Check if the difference between timestamps is an hour
                    pass
                else:
                    # If it isn't, interpolates
                    dfraw = dat['df'].copy()
                    daterange = pd.date_range(dat['datainici'], dat['datafin'], freq='H')
                    dfcontrol = pd.DataFrame(np.arange(len(daterange)), index=daterange)
                    dfmerge = dfraw.merge(dfcontrol, how='outer', left_index=True,
                                          right_index=True).interpolate(method='index', limit_direction='both')
                    dfmerge = dfmerge[dfmerge.index.astype('int64') // 10 ** 9 % 3600 == 0]
                    dfinter = dfmerge.drop(columns='0')
                    sinter = dfinter['Temp'].round(3)
                    dat['df'] = sinter
                    break

    def to_utc(self):
        """
        Method: to_utc(data)
        Purpose: Shift temporal axis
        Require:
        Version: 01/2021, EGL: Documentation
        """
        for i in range(len(self.mdata)):
            gmthshift = int(self.mdata[i]["GMT"][1:])
            # Mirar timedelta
            self.mdata[i]['df'].index = [self.mdata[i]['df'].index[n] - timedelta(hours=gmthshift) for n in
                               range(len(self.mdata[i]['df'].index))]
            self.mdata[i]['datainici'] = self.mdata[i]['datainici'] - timedelta(hours=gmthshift)
            self.mdata[i]['datafin'] = self.mdata[i]['datafin'] - timedelta(hours=gmthshift)
