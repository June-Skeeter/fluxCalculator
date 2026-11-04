from pandas.api.types import is_float_dtype,is_integer_dtype
from dataclasses import dataclass, field, make_dataclass
from configparser import ConfigParser
from functools import partial
import pandas as pd
import numpy as np
from datetime import datetime
import json
import uuid
# import yaml
import os
import re

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
root = os.path.split(os.path.split(__file__)[0])[0]
eddyproTemplate = fromIniDefault(os.path.join(root,'templates','template.eddypro'))
ghgTemplate = fromIniDefault(os.path.join(root,'templates','template.metadata'))

class ecf32ProjectWriter(eddyproTemplate):

    def newFile(self,start_date,end_date):
        self.Project['file_type'] = '7'
        self.Project['creation_date'] = datetime.now().isoformat()
        self.Project['last_change_date'] = self.Project['creation_date']

        self.Project['binary_hnlines']='0'
        self.Project['binary_eol']='0'
        self.Project['binary_nbytes']='4'
        self.Project['binary_little_end']='1'
        self.Project['use_biom']='0'
        print('Warning: Turn use_biom on')
        # Set times to that of metadata file
        self.Project['pr_start_date'] = start_date.split('T')[0]
        self.Project['pr_start_time'] = ':'.join(start_date.split('T')[1].split(':')[:2])
        self.Project['pr_end_date'] = end_date.split('T')[0]
        self.Project['pr_end_time'] = ':'.join(end_date.split('T')[1].split(':')[:2])
        
        self.FluxCorrection_SpectralAnalysis_General['sa_start_date'] = start_date.split('T')[0]
        self.FluxCorrection_SpectralAnalysis_General['sa_start_time'] = ':'.join(start_date.split('T')[1].split(':')[:2])
        self.FluxCorrection_SpectralAnalysis_General['sa_end_date'] = end_date.split('T')[0]
        self.FluxCorrection_SpectralAnalysis_General['sa_end_time'] = ':'.join(end_date.split('T')[1].split(':')[:2])

        self.RawProcess_TiltCorrection_Settings['pf_start_date'] = start_date.split('T')[0]
        self.RawProcess_TiltCorrection_Settings['pf_start_time'] = ':'.join(start_date.split('T')[1].split(':')[:2])
        self.RawProcess_TiltCorrection_Settings['pf_end_date'] = end_date.split('T')[0]
        self.RawProcess_TiltCorrection_Settings['pf_end_time'] = ':'.join(end_date.split('T')[1].split(':')[:2])
        
        self.RawProcess_TimelagOptimization_Settings['to_start_date'] = start_date.split('T')[0]
        self.RawProcess_TimelagOptimization_Settings['to_start_time'] = ':'.join(start_date.split('T')[1].split(':')[:2])
        self.RawProcess_TimelagOptimization_Settings['to_end_date'] = end_date.split('T')[0]
        self.RawProcess_TimelagOptimization_Settings['to_end_time'] = ':'.join(end_date.split('T')[1].split(':')[:2])

        self.RawProcess_General['dec_date'] = start_date.split('T')[0]
        
    def selectColumns(self,Instruments,FileDescription):
        self.Project['master_sonic'] = Instruments['instr_1_model']
        print('Exclude col_ts, forces to use sonic temp?')
        cols = {k:'' for k in self.Project.keys() if k.startswith('col') and k!='col_ts'}
        vars = {k:v for k,v in FileDescription.items() if k.endswith('variable')}
        for col in cols.keys():
            if col.split('_',1)[-1] in vars.values():
                for key,value in vars.items():
                    if value == col.split('_',1)[-1]:
                        self.Project[col] = key.split('_')[1]
                        continue

    def writeFile(self,filepath):
        self.Project['use_pfile'] = '1'
        self.Project['proj_file'] = filepath
        self.RawProcess_General['data_path'] = os.path.split(filepath)[0]
        filepath = filepath.replace('.metadata','.eddypro')
        self.Project['file_name'] = filepath
        self.Project['out_path'] = os.path.join(os.path.split(filepath)[0],'eddypro_out_test')
        # self.Project['file_prototype'] = os.path.split(filepath)[1].replace('.eddypro','_yyyymmddTHHMM.float32')

        epOut = ConfigParser()
        for key in eddyproTemplate.__annotations__:
            if key == 'DEFAULT':
                continue
            epOut.add_section(key)
            epOut[key] = getattr(self,key)
        with open(self.Project['file_name'],'w+') as fout:
            fout.write(';EDDYPRO_PROCESSING\n')
            epOut.write(fout, space_around_delimiters=False)


# Metadata format of LICOR .ghg files
class ghgMetadataWriter(ghgTemplate):
    
    def newFile(self,site_id,latitude,longitude,altitude='',canopy_height='',site_name='',start_date='',stop_date=''):
        self.Project['start_date'] = start_date
        self.Project['end_date'] = stop_date
        self.Site['site_id'] = site_id
        self.Site['site_name'] = site_name
        self.Site['latitude'] = latitude
        self.Site['longitude'] = longitude
        self.Site['altitude'] = altitude
        self.Site['canopy_height'] = canopy_height

    def writeFiles(self,filepath):
        filepath = os.path.abspath(filepath)
        self.Project['file_name'] = filepath
        self.Project['creation_date'] = datetime.now().isoformat()
        self.Project['last_change_date'] = self.Project['creation_date']
        ghgMetadataFile = ConfigParser()
        for key in ghgTemplate.__annotations__:
            if key == 'DEFAULT':
                continue
            ghgMetadataFile.add_section(key)
            ghgMetadataFile[key] = getattr(self,key)
        with open(self.Project['file_name'],'w+') as fout:
            fout.write(';GHG_METADATA\n')
            ghgMetadataFile.write(fout, space_around_delimiters=False)
        EP = ecf32ProjectWriter()
        EP.newFile(self.Project['start_date'],self.Project['end_date'])
        EP.selectColumns(self.Instruments,self.FileDescription)
        EP.writeFile(filepath)

    def asDictionary(self,flat=False):
        if flat:
            return({(key,subKey):value for key,values in self.__dict__.items() if key in ghgTemplate.__annotations__ for subKey,value in values.items()})
        else:
            # for yaml, etc.
            return({key:value for key,value in self.__dict__.items() if key in ghgTemplate.__annotations__})

@dataclass(kw_only=True)
class highFrequency(ghgMetadataWriter):
    outputPath: str
    dataIntervalSeconds: str = 1800
    missingSampleAllowance: float = 0.1 # default pct from eddypro
    fileNameTemplate: str = "%Y%m%dT%H%M.float32"
    def loadDataFrame(self,dataframe):
        expectedShape = int(pd.to_timedelta(f"{self.dataIntervalSeconds}s").total_seconds()/dataframe.index.diff().median().total_seconds())
        flag = [c for c,v in dataframe.dtypes.items() if str(v) != 'float32']
        if len(flag):
            exit(f"Columns are not in float32 format: {flag}")
        if dataframe.index.duplicated().sum():
            exit('Duplicates detected')
        dataFrequencyHz = 1/dataframe.index.diff().total_seconds().to_series().median()
        if dataFrequencyHz < 1:
            exit(f'Format not suited for Hz < 20, detected frequency was {dataFrequencyHz}')
        self.Timing['acquisition_frequency'] = dataFrequencyHz
        self.Timing['file_duration'] = int(self.dataIntervalSeconds/60)
        print('Warning: serialize with json to ensure consitencey')
        hash = str(uuid.uuid5(uuid.NAMESPACE_DNS,str(self.asDictionary())))
        dataFrequencyHz = f"{int(dataFrequencyHz)}Hz"
        if len(dataframe.columns.names)==1:
            metadata = {col:{'variableName':col,'dataType':str(dataframe[col].dtype)} for col in dataframe.columns}
        else:
            metadata = {col[0]:{vn:col[i] for i,vn in enumerate(dataframe.columns.names)} for col in dataframe.columns}
        ix = pd.date_range(
            dataframe.index.min().floor(f"{self.dataIntervalSeconds}s"),
            dataframe.index.max().ceil(f"{self.dataIntervalSeconds}s"),
            freq=f"{self.dataIntervalSeconds}s")
        ix = [ix[j:j+2] for j in range(len(ix)-1)]
        fp = ''
        names = []
        for i in ix:
            yyyymm = f"{i[1].year}{str(i[1].month).zfill(2)}"
            if yyyymm not in fp:
                fp = os.path.join(self.outputPath,hash,yyyymm)
                os.makedirs(fp,exist_ok=True)
            df = dataframe.loc[(
                (dataframe.index > i[0])
                &
                (dataframe.index <= i[1])
                )]
            if df.empty:
                continue
            elif len(df) > expectedShape:
                # breakpoint()
                exit('Too man samples, unexpected error')
            elif len(df) < expectedShape:
                if len(df) < expectedShape * (1-self.missingSampleAllowance):
                    print(f'Insufficient samples for timestep {i[0]}:{i[1]}')
                    continue
                else:
                    # If short, but within tolerance, pad with NaN to expected shape
                    short = expectedShape - df.shape[0]
                    print(f'Short by {short} samples for timestep {i[0]}:{i[1]}, padding with NaN')
                    pad = np.empty((short)*df.shape[1])*np.nan
                    dataOut = np.concatenate((df.values.T.flatten(),pad))
            else:
                dataOut = df.values.T.flatten()
            os.makedirs(fp,exist_ok=True)
            fn = i[1].strftime(self.fileNameTemplate)#.replace('UUID',hash))
            fn = os.path.join(fp,fn)
            names.append(fn)
            print(f"Writing: {fn}")
            print(df.shape)
            # Transpose to fortran order and flatten to 1D
            dataOut.tofile(fn)
            mdfn = fn.replace('.float32','.json')
            mdout = {'.shape':df.shape,'.frequency':dataFrequencyHz,'start_time':df.index[0].isoformat()}|metadata
            with open(mdfn,'w+') as f:
                json.dump(mdout,f,indent=4)
        if len(names):
            return(hash)
        else:
            return(False)