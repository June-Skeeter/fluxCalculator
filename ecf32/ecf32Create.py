from dataclasses import dataclass, field, make_dataclass
from configparser import ConfigParser
from functools import partial
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

@dataclass(kw_only=True)
class ecf32Write:
    outputPath: str
    siteID: str
    dataframe: pd.DataFrame
    dataInterval: str = '1800s'
    missingSampleAllowance: float = 0.1 # default pct from eddypro
    fileNameTemplate: str = field(default='siteID_%Y%m%dT%H%M_mxn.float32',init=False)

    def __post_init__(self):
        self.fileNameTemplate = self.fileNameTemplate.replace('siteID',self.siteID)
        ix = pd.date_range(
            self.dataframe.index.min().floor(self.dataInterval),
            self.dataframe.index.max().ceil(self.dataInterval),
            freq=self.dataInterval)
        ix = [ix[j:j+2] for j in range(len(ix)-1)]
        for i in ix:
            df = self.dataframe.loc[(
                (self.dataframe.index > i[0])
                &
                (self.dataframe.index <= i[1])
                )]
            if len(df) > pd.to_timedelta(self.dataInterval).total_seconds()/df.index.diff().mean().total_seconds():
                exit('Too man samples, unexpected error')
            elif len(df) < pd.to_timedelta(self.dataInterval).total_seconds()/df.index.diff().mean().total_seconds()*(1-self.missingSampleAllowance):
                print(f'Insufficient samples for timestep {i[0]}:{i[1]}')
                continue
            fp = re.sub('yyyy',f"{i[1].year}",self.outputPath,flags=re.IGNORECASE)
            fp = re.sub('mm',f"{i[1].month}",fp,flags=re.IGNORECASE)
            os.makedirs(fp,exist_ok=True)
            fn = i[1].strftime(self.fileNameTemplate)
            fn = fn.replace('mxn.ecf32',f'{df.shape[0]}x{df.shape[1]}.float32')
            fn = os.path.join(fp,fn)
            df.astype('float32').values.tofile(fn)
        self.dataframe.to_csv('testData/testData.csv')

def fieldBuilder(name,base):
    def getSec(base,name):
        if type(base) is ConfigParser:
            return(dict(base[name]))
        return(base[name])

    value = partial(getSec,base=base,name=name)
    if value() is not None:
        typ = type(value())
        if typ not in [dict,list]:  
            return (name,type(value()),value())
        else:
            return (name,type(value()),field(default_factory=value))            
    else:
        return (name)

def fromIniDefault(filePath,bases=(),asDataclass=True,namespace=None):
    config = ConfigParser()
    config.read(filePath)
    className = os.path.split(filePath)[-1].rsplit('.',1)[0]
    if not asDataclass: return(config)
    dc = make_dataclass(
        className,
        [fieldBuilder(fld,config) for fld in config.sections()],
        bases=bases,
        namespace=namespace,
        kw_only=True
    )
    return dc
eddyproTemplate = fromIniDefault(os.path.join(os.path.split(__file__)[0],'templates','eddyproTemplate.eddypro'))
ghgTemplate = fromIniDefault(os.path.join(os.path.split(__file__)[0],'templates','ghgTemplate.metadata'))


@dataclass(kw_only=True)
class ecf32ProjectWriter(eddyproTemplate):

    def __post_init__(self):
        self.Project['file+type'] = 7
        self.Project['creation_date'] = datetime.now().isoformat()
        self.Project['last_change_date'] = self.Project['creation_date']

#     def setDates(self,dateStart,dateStop):
#         dateStart=datetime.fromisoformat(dateStart)
#         if dateStop is None: dateStop = datetime.now()
#         else: dateStop=datetime.fromisoformat(dateStop)
#         for key,value in eddyproTemplate().__dict__.items():
#             for dval in [k.split('start_date')[0] for k in value if 'start_date' in k]:
#                 value[f"{dval}start_date"] = dateStart.strftime('%Y-%m-%d')
#                 value[f"{dval}start_time"] = dateStart.strftime('%H:%M')
#                 value[f"{dval}end_date"] = dateStop.strftime('%Y-%m-%d')
#                 value[f"{dval}end_time"] = dateStop.strftime('%H:%M')
#             setattr(self,key,value)

#     def fill(self,ghgMetadataFile):
#         for key,value in ghgMetadataFile.Project.items():
#             if key in getattr(self,'Project'):
#                 self.Project[key]=value
#         self.Project['master_sonic'] = ghgMetadataFile.Instruments['instr_1_id']
#         for key,value in self.Project.items():
#             if key.startswith('col_'):
#                 col = key.split('col_')[-1]
#                 if col in ghgMetadataFile.variableColumns:
#                     self.Project[key] = ghgMetadataFile.variableColumns[col]
#         self.Project['file_name'] = ghgMetadataFile.Project['file_name'].replace('.metadata','.eddypro')
#         self.writeFile()

#     def writeFile(self):
#         # self.fill(ghgMetadataFile)
#         epOut = ConfigParser()
#         for key in eddyproTemplate.__annotations__:
#             if key == 'DEFAULT':
#                 continue
#             epOut.add_section(key)
#             epOut[key] = getattr(self,key)
#         with open(self.Project['file_name'],'w+') as fout:
#             fout.write(';EDDYPRO_PROCESSING\n')
#             epOut.write(fout)


# Metadata format of LICOR .ghg files
class ghgMetadataWriter(ghgTemplate):
    
    def newFile(self,site_id,latitude,longitude,altitude='',canopy_height='',site_name=''):
        self.Project['creation_date'] = datetime.now().isoformat()
        self.Project['last_change_date'] = self.Project['creation_date']
        self.Site['site_id'] = site_id
        self.Site['site_name'] = site_name
        self.Site['latitude'] = latitude
        self.Site['longitude'] = longitude
        self.Site['altitude'] = longitude
        self.Site['canopy_height'] = canopy_height

    def setDates(self,start_date,stop_date):
        self.Project['start_date'] = start_date
        self.Project['end_date'] = stop_date

    def setInstrument(self,ix,manufacturer,model,id,height='',north_offset='',northward_separation='',eastward_separation='',vertical_separation='',tube_length='',tube_diameter=''):
        self.Instruments[f"instr_{ix}_manufacturer"] = manufacturer
        self.Instruments[f"instr_{ix}_model"] = model
        self.Instruments[f"instr_{ix}_id"] = id
        if ix == 1 and height and north_offset:
            self.Instruments[f"instr_{ix}_height"] = str(height)
            self.Instruments[f"instr_{ix}_north_offset"] = str(north_offset)
        elif ix > 1:
            self.Instruments[f"instr_{ix}_northward_separation"]=str(northward_separation)
            self.Instruments[f"instr_{ix}_eastward_separation"]=str(eastward_separation)
            self.Instruments[f"instr_{ix}_vertical_separation"]=str(vertical_separation)
            if tube_length != '':
                self.Instruments[f"instr_{ix}_tube_length"]=tube_length
                self.Instruments[f"instr_{ix}_tube_diameter"]=tube_diameter
                # Set to 0, overwritten with data from the file anyway
                self.Instruments[f"instr_{ix}_tube_flowrate"]='0.00'

    def setFileDescription(self,traces):
        self.instrumentList = [self.Instruments[f'instr_{i+1}_id'] for i,_ in enumerate([k for k in self.Instruments.keys() if k.endswith('_id')])]
    #     self.getInstrumentList()
    #     col_n = [k for k in self.FileDescription.keys() if k.startswith('col_1')]
    #     columns = {k.replace('_1_','_n_'):self.FileDescription.pop(k) for k in col_n}
    #     # To prevent duplication, get variable translation, then select preffered opton
    #     selectedVariables = self.variableSelection(traces)
    #     self.variableColumns = {}
    #     for ix,values in enumerate(traces.values()):
    #         i = ix + 1
    #         if values['variableName'] not in selectedVariables:
    #             self.FileDescription[f'col_{i}_variable'] = 'ignore'
    #         else:
    #             variable = selectedVariables[values['variableName']]
    #             self.FileDescription[f'col_{i}_variable'] = variable
    #             self.variableColumns[variable] = i
    #             self.FileDescription[f"col_{i}_instrument"] = self.translate('instrument',variable)
    #             self.logMessage('set units, type, etc.')

    # def variableSelection(self,traces):
    #     # map all variables onto preferred vairables (first in list from ghgTranslator *if any present*)
    #     vnList = [values['variableName'] for values in traces.values()]
    #     variables = {
    #         names[0]:var for var,names in {
    #             var:[name for name in names if name in vnList]
    #             for var,names in ghgTranslator['variable'].items()
    #             }.items() 
    #         if len(names)
    #         }
    #     return(variables)

    # def translate(self,key,value):
    #     if key in ['measurementType']:
    #         for key,v in ghgTranslator[key].items():
    #             if value in v or value == v:
    #                 return(key)
    #         return('')
    #     elif key == 'instrument':
    #         for instrument in self.instrumentList:
    #             if instrument.rsplit('_')[0] not in ghgTranslator['instrument'].keys():
    #                 self.logMessage(f'Add variables for {instrument.rsplit("_")[0]}')
    #             elif value in ghgTranslator['instrument'][instrument.rsplit("_")[0]]:
    #                 return(instrument)
    #         self.logMessage(f'Could not par instrument for {value}')
    #         return('')

    # def writeFiles(self,filepath):
    #     self.Project['file_name'] = filepath
    #     ghgMetadataFile = ConfigParser()
    #     for key in ghgMetadata.__annotations__:
    #         if key == 'DEFAULT':
    #             continue
    #         ghgMetadataFile.add_section(key)
    #         ghgMetadataFile[key] = getattr(self,key)
    #     with open(self.Project['file_name'],'w+') as fout:
    #         fout.write(';GHG_METADATA\n')
    #         ghgMetadataFile.write(fout)
    def asDictionary(self,flat=False):
        if flat:
            # for dataframes
            return({(key,subKey):value for key,values in self.__dict__.items() for subKey,value in values.items() if key in ghgTemplate.__annotations__})
        else:
            # for yaml, etc.
            return({key:value for key,value in self.__dict__.items() if key in ghgTemplate.__annotations__})
