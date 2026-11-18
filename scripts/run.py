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
import os

@dataclass(kw_only=True)
class run:
    system: str
    eddyproFile: str
    multiProcessing: bool = True
    root: str = os.path.join(os.path.split(os.path.split(__file__)[0])[0],'bin')

    def __post_init__(self):
        cwd = os.getcwd()
        os.chdir(self.root)
        settings = ConfigParser()
        settings.read(self.eddyproFile)
        settings = {section:dict(settings[section]) for section in settings.sections()}
        if not self.multiProcessing:
            args = [os.path.join(self.system,'eddypro_rp'), '-s', self.system, self.eddyproFile]
            subprocess.run(args)
        else:
            if self.multiProcessing is True:
                max_workers = 2
            else:
                max_workers = int(self.multiProcessing)
            timesteps = [datetime.strptime(step,'%Y%m%dT%H%M.float32')
                          for fld in os.listdir(settings['RawProcess_General']['data_path']) 
                          if fld.isdigit() 
                          for step in os.listdir(os.path.join(settings['RawProcess_General']['data_path'],fld)) 
                          if step.endswith('.float32')]
            timesteps.sort()
            stepSize = math.ceil(len(timesteps)/max_workers)
            timesteps = [[timesteps[i*stepSize].isoformat(),timesteps[:(i+1)*stepSize][-1].isoformat()]for i in range(max_workers)]
            batches = []
            for i,batch in enumerate(timesteps):
                template = settings.copy()
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
            self.mergeRP(batches)
        os.chdir(cwd)
        breakpoint()

    def mergeRP(self,batches):
        files = {}
        for out,header in zip(['full_output','biomet','metadata','fluxnet'],[3,2,1,1]):
            files[out] = [glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output',f'*{out}*.csv'))[0] for batch in batches]
            df = pd.concat([pd.read_csv(f,skiprows=header,header=None) for f in files[out]])
            with open(files[out][0]) as f:
                h = ''.join([f.readline() for l in range(3)])
            with open(os.path.sep.join(files[out][0].split(os.path.join('tmp0','eddypro_output'))),'w+') as f:
                f.write(h)
                df.to_csv(h,index=False)
            breakpoint()


        files['user_stats'] = [glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_user_stats',f'*.csv'))[0] for batch in batches]
        files['eddypro_stats'] = [glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_stats',f'*.csv'))[0] for batch in batches]
        files['eddypro_binned_cospectra'] = [f for batch in batches for f in glob(os.path.join(os.path.split(batch[-1]),'eddypro_output','eddypro_binned_cospectra',f'*.csv'))[0]]
        files['eddypro_full_cospectra'] = [f for batch in batches for f in glob(os.path.join(os.path.split(batch[-1]),'eddypro_output','eddypro_full_cospectra',f'*.csv'))[0]]   

        pd.concat([pd.concat([pd.read_csv(f,header=[0,1,2]) for f in glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','*full_output*.csv'))]) for batch in batches])