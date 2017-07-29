import configparser # What we use to get the options from the text file passed.


class ThreeParser():

    def __init__(self, options, whitelist):
        self._options = options # Directory to the Options.txt file.
        self._whitelist = whitelist # Directory to the Whitelist.txt file.
        
    def getOptions(self):
        
        try:
            # Creation of the configparser object.
            parser = configparser.RawConfigParser()
            parser.read(self._options)

            # Creation of the dictionary with all the commands.
            optionDict = {'cmdSym':parser.get('ThreebotOptions', 'commandStarter'),
                          'cToken':parser.get('ThreebotOptions', 'clientToken'),
                          'enWL':parser.get('ThreebotOptions', 'enabledWhitelist')}
                         #'optionVariable':parser.get('ThreebotOptions', 'option')}

            # Whitelist check.
            if optionDict['enWL'] == 'True':
                optionDict['enWL'] = True
            else:
                optionDict['enWL'] = False
            
            return optionDict
        
        except: # This is bad coding..
            raise TypeError("Destination passed is invalid, or invalid option format!")

    def getWhitelist(self):

        # This is pretty self explanatory.
        
        try:
            parser = open(self._whitelist, 'r')
            
            wList = []
            for line in parser:
                wList += [line.strip('\n')]
                
            return wList
        
        except: # See above
            raise TypeError("Destination passed is invalid, or invalid whitelist format!")
        
    def getAll(self): # Basically cramming everything ThreeParser does into a tuple.
        return (self.getOptions(), self.getWhitelist())
