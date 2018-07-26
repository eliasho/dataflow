'''
Created on 18.05.2018

@author: yvo
'''

import datetime
from ..FileDataReader import AsciiFileDateReader
from DataObjects.Glacier import Glacier
from DataObjects.Enumerations.DateEnumerations import DateQualityTypeEnum

from DataObjects.Exceptions.GlacierNotFoundError import GlacierNotFoundError

class VawFileReader(AsciiFileDateReader):
    '''
    Super class for all file types generated by VAW. The file type is mainly used by Andreas Bauder
    for length change data and observations. The file contains a specific header information
    containing the pkVaw of a glacier and a glacier name.
    
    Common parts of the header line:
        - Pos. 1: Glacier short name
        - Pos. 2: VAW Identifier 
    
    Attributes:
        - _numberHeaderLines              Number of header lines used in the data file.
        - _numberDataLines                Number of lines containing data.
        - _headerLineContent              Dictionary with position and name of header line values.
        - _HEADER_POSITION_SHORTNAME      Common position in the header line of the short name.
        - _HEADER_POSITION_VAWIDENTIFIER  Common position in the header line of the VAW identifier.
        - _dataSource                     Source of the data as defined in the header
        - _DATA_SOURCE_PREFIX             Prefix for data source references used (to be removed)
    '''
    
    _numberHeaderLines = -1
    
    _numberDataLines = -1
        
    _headerLineContent = dict()
    
    _HEADER_POSITION_SHORTNAME     = 1
    _HEADER_POSITION_VAWIDENTIFIER = 2
    
    _dataSource = None
    
    _DATA_SOURCE_PREFIX = "# © "
    
    def __init__(self, fullFileName, glaciers):
        '''
        Constructor of the class.
        
        @type fullFileName: string
        @param fullFileName: Absolute path of the file.
        @type glaciers: Dictionary
        @param glaciers: Dictionary with glaciers.
        
        @raise GlacierNotFoundError: Exception if glacier was not found or initialised.
        '''
        
        # Definition of the header line content
        self._headerLineContent[self._HEADER_POSITION_SHORTNAME] = "Glacier short name"
        self._headerLineContent[self._HEADER_POSITION_VAWIDENTIFIER] = "VAW identifier"

        super().__init__(fullFileName)

        self.parseHeader()
        
        print("Given data file -> " + fullFileName)
        
        givenVawId = int(self._headerLineContent[self._HEADER_POSITION_VAWIDENTIFIER])

        # Looking for the corresponding glacier in the given glacier collection.
        glacierFound = None
        for glacier in glaciers.values():
            
            # Comparing the current glacier with the VAW internal ID of the given file header.
            if glacier.pkVaw == givenVawId:
                glacierFound = glacier
        
        if glacierFound != None:
            self._glacier = glacierFound

        else:
            message = "No corresponding glacier found. Header information given VAW-PK {0} and short name {1}".format(
                    self._headerLineContent[self._HEADER_POSITION_VAWIDENTIFIER], self._headerLineContent[self._HEADER_POSITION_SHORTNAME])
            raise GlacierNotFoundError(message)

    @property
    def numberDataLines(self):
        '''
        Returns the number of lines parsed containing observation data. Returns -1 in case the file was 
        not parsed yet.
        
        @rtype: integer
        @return: Number of data lines in the file parsed
        '''
        
        return self._numberDataLines
        
    def parseHeader(self):
        '''
        Parsing the header information of the text file. The header information
        has to include the pkVaw and the name of the glacier.
        
        During parsing the header, the protected glacier member will be created.
        '''
        
        with open(self._fullFileName, "r") as vaw:
            
            lineCounter = 0
            
            for line in vaw:
        
                lineCounter += 1
                
                try:
                        
                    if lineCounter == 1:
                            
                        self._getMetadata(line)
                        
                    if self._numberHeaderLines == lineCounter:
                        
                        self._dataSource = line.strip()
                        self._dataSource = self._dataSource.replace(self._DATA_SOURCE_PREFIX, "")


                #TODO: Implementing own exceptions.
                except Exception as e:

                    errorMessage = "{0} @ {1}: {2}".format(vaw, lineCounter, e)
                    print(errorMessage)
        
    def _reformateDate(self, dateVaw):
        '''
        Helper function to reformat the VAW format of the date. A VAW format will have
        values as 00.00.2018 identifying a not known date of the year 2018.
        Such kind of values are translated into 01.09. of the corresponding year.
        
        @type dateVaw: string
        @param dateVaw: String-representation of the date as string in the format dd.mm.yyyy
        
        @rtype: Array [DateTime, integer]
        @return: Array with a correct date object and the quality of the date (e.g. 1 = known, 11 = estimated).
        '''
    
        dateVawParts = dateVaw.split(".")
    
        day   = None
        month = None
        year  = None
    
        quality = None
    
        if dateVawParts[0] == "00" or dateVawParts[1] == "00":
            quality = 11
        else:
            quality = 1
    
        if dateVawParts[0] == "00":
            day = 1
        else:
            day = int(dateVawParts[0])
        if dateVawParts[1] == "00":
            month = 9
        else:
            month = int(dateVawParts[1])
    
        year = int(dateVawParts[2])
    
        return [datetime.date(year, month, day), quality]
    
    def _reformateDateMmDd(self, mmdd, yyyy):
        
        return self._reformateDateYyyyMmDd("{0}{1}".format(yyyy, mmdd))

    def _reformateDateYyyyMmDd(self, yyyymmdd):
        '''
        Helper function to reformat the string YYYYMMDD into a datetime object.
        
        @type dateVaw: string
        @param dateVaw: String-representation of the date as string in the format yyyymmdd
        
        @rtype: Array [DateTime, integer]
        @return: Array with a correct date object and the quality of the date (e.g. 1 = known, 11 = estimated).
        '''
        
        dateParts = [
            yyyymmdd[6:],
            yyyymmdd[4:6],
            yyyymmdd[:4]]
        
        day   = None
        month = None
        year  = None
    
        quality = None
    
        if dateParts[0] == "00" or dateParts[1] == "00":
            quality = DateQualityTypeEnum.Estimated
        else:
            quality = DateQualityTypeEnum.Precisely
    
        if dateParts[0] == "00":
            day = 1
        else:
            day = int(dateParts[0])
        if dateParts[1] == "00":
            month = 9
        else:
            month = int(dateParts[1])
    
        year = int(dateParts[2])
    
        return [datetime.date(year, month, day), quality]
    
    def _getMetadata(self, metadataLine):
        '''
        Helper function to retrieve the key values of the header (e.g. pkVaw, name).
        The values of the header line is written to the dictionary
        containing the header line content.
        
        @type metadataLine: string
        @param metadataLine: Entire line of the header.
        '''

        lineParts = metadataLine.split(";")
        
        for key, value in self._headerLineContent.items():
            
            description = value
            headerValue = lineParts[key].strip()
            
            self._headerLineContent[key] = headerValue