#parses pick and place file and makes scope go in that direction
import codecs
import csv
from collections import defaultdict

#PickAndPlaceCSV = csv.reader(codecs.open('ladybugboard.csv', 'rU', 'utf-16'), delimiter=' ', quotechar='|')

#for row in PickAndPlaceCSV:
#    print (', '.join(row))


        

def ParseEDAPickAndPlace(FileName='ladybugboard.csv',UnitsPerMil = 0.0254):
    '''using EasyEDA pick and place CSV file
    returns a dictionary, with each key being the 11 types of information
    including:

    Designator
    Footprint
    Mid X
    Mid Y
    Ref X
    Ref Y
    Pad X
    Pad Y
    Layer
    Rotation
    Comment
    
    we're most interested in the position info. all those converted to units of
    milimeters
    '''

    
    columns = defaultdict(list)
    reader = csv.reader(codecs.open(FileName, 'rU', 'utf-16'), delimiter='\t')
    headers = next(reader)
    #print(headers)
    rows = {}
    column_nums = range(len(headers)) # Do NOT change to xrange
    #print(column_nums)
    for row in reader:
        ID = row[0]
        
        #print(rows)
        for i in column_nums:
            if 'mil' in row[i]: #brute force remove mils change units
                row[i] = ConvertUnits(row[i],UnitsPerMil)
            
            columns[headers[i]].append(row[i])

            

        rows[ID] = {headers[j]: row[j] for j in range(1,len(headers))}

            #print(row[i])
    # Following line is only necessary if you want a key error for invalid column names
    columns = dict(columns)
    #print(rows)
    return columns, rows
    
def GetLocations(FileName = 'ladybugboard.csv',UnitsPerMil = 0.0254, Sorted = True):

    #if not FileName:
    #    FileName = filedialog.askopenfilename()
    
    columns, rows = ParseEDAPickAndPlace(FileName,UnitsPerMil)

    Designators = {}
    
    for i in range(len(columns['Designator'])):
        designator = columns['Designator'][i]
        MidX = columns['Mid X'][i]
        MidY = columns['Mid Y'][i]
        Designators[designator] = MidX,MidY
        

    return Designators, columns, rows

def ConvertUnits(MilString,UnitsPerMil):

    MilFloat = float("".join([i for i in MilString if (i.isdigit() or i == '.')]))
    UnitFloat = round((MilFloat * UnitsPerMil),2)
    
    return UnitFloat


def main():
    global Designators, Columns, rows
    Designators, Columns, rows = GetLocations() #argparse?
    

if __name__ == '__main__':
    main()
