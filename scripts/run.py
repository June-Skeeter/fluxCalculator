import platform
from dataclasses import dataclass
from configparser import ConfigParser
from .ecf32Create import ecf32ProjectWriter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial
import pandas as pd
import subprocess
import math
import copy
from glob import glob
import shutil
import os

@dataclass(kw_only=True)
class runBatch:
    eddyproFile: str
    multiProcessing: bool = True
    system: str = platform.system().lower()
    root: str = os.path.join(os.path.split(os.path.split(__file__)[0])[0],'bin')

    def __post_init__(self):
        if self.system == 'windows': self.system = 'win'
        elif self.system == 'darwin': self.system = 'mac'
        cwd = os.getcwd()
        os.chdir(self.root)
        self.settings = ConfigParser()
        self.settings.read(self.eddyproFile)
        self.settings = {section:dict(self.settings[section]) for section in self.settings.sections()}
        if not self.multiProcessing:
            args = [os.path.join(self.system,'eddypro_rp'), '-s', self.system, self.eddyproFile]
            subprocess.run(args)
        else:
            if self.multiProcessing is True:
                max_workers = 2
            else:
                max_workers = int(self.multiProcessing)
            timesteps = [datetime.strptime(step,'%Y%m%dT%H%M.float32')
                          for fld in os.listdir(self.settings['RawProcess_General']['data_path']) 
                          if fld.isdigit() 
                          for step in os.listdir(os.path.join(self.settings['RawProcess_General']['data_path'],fld)) 
                          if step.endswith('.float32')]
            timesteps.sort()
            stepSize = math.ceil(len(timesteps)/max_workers)
            timesteps = [[timesteps[i*stepSize].isoformat(),timesteps[:(i+1)*stepSize][-1].isoformat()]for i in range(max_workers)]
            batches = []
            for i,batch in enumerate(timesteps):
                template = self.settings.copy()
                step = ecf32ProjectWriter(**copy.deepcopy(template))
                step.newFile(start_date=batch[0],end_date=batch[1])
                filename = os.path.join(step.Project['out_path'],f'tmp{i}','ecf32.eddypro')
                # Turn off fcc for batches, re-run fcc after merge
                step.Project['run_fcc'] = 0
                step.writeFile(filename)
                args = [os.path.join(self.system,'eddypro_rp'), '-s', self.system, filename]
                batches.append(args)
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                executor.map(subprocess.run,batches)
            print('RP completed')
            self.mergeRP(batches)
        os.chdir(cwd)
        breakpoint()

    def mergeRP(self,batches):
        for out,header in zip(['full_output','biomet','metadata','fluxnet'],[3,2,1,1]):
            print(out,header)
            self.combine([glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output',f'*{out}*.csv'))[0] for batch in batches],header)
        self.combine([glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_user_stats',f'*.csv'))[0] for batch in batches],2)
        self.combine([glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_stats',f'*.csv'))[0] for batch in batches],2)
        for batch in batches:
            src = os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_binned_cospectra')
            dst = os.path.join(self.settings['Project']['out_path'],'eddypro_binned_cospectra')
            os.makedirs(dst,exist_ok=True)
            shutil.copytree(src,dst,dirs_exist_ok=True)
            src = os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_full_cospectra')
            dst = os.path.join(self.settings['Project']['out_path'],'eddypro_full_cospectra')
            os.makedirs(dst,exist_ok=True)
            shutil.copytree(src,dst,dirs_exist_ok=True)
        print('Merge completed')
        
    def combine(self,files,header):
        df = pd.concat([pd.read_csv(f,skiprows=header,header=None) for f in files])
        with open(files[0]) as f:
            h = ''.join([f.readline() for l in range(header)])
        with open(os.path.join(self.settings['Project']['out_path'],os.path.split(files[0])[-1]),'w+', newline="") as f:
            f.write(h)
            df.to_csv(f,index=False)

if __name__ == '__main__':
    print('CLI parse here ...')