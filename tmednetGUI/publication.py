import sys, getopt, os
import file_manipulation as fm
import user_interaction as ui

#Gets the parameters from the command line to execute the publication script
#TODO it uses fm-load_data properly, keep working

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
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv, 'hi:o:', ['idir=', 'ofile='])
    except getopt.GetoptError:
        print('publication.py -i <inputdirectory> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt =='-h':
            print('publication.py -i <inputdirectory> -o <outputfile>')
            sys.exit()
        elif opt in ('-i', '--idir'):
            inputdir = arg
        elif opt in ('-o', '--ofile'):
            outputfile = arg
        print(opts)
    print('Input directory is ', inputdir)
    print('Output file is ', outputfile)
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
if __name__ == '__main__':
    main(sys.argv[1:])