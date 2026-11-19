import platform
from dataclasses import dataclass
from configparser import ConfigParser
from .ecf32Create import ecf32ProjectWriter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial
import multiprocessing
import pandas as pd
import subprocess
import math
import copy
import time
from glob import glob
import shutil
import os

# stager executions by to prevent rp calls from generating the same tmp dir
def stagger(counter,lock,delay,steps):
    print(f'Initializing process {counter.value}: {steps[counter.value]}')
    with lock:
        ID = counter.value
        counter.value += 1
    time.sleep(ID*delay)

@dataclass(kw_only=True)
class runBatch:
    eddyproFile: str
    multiProcessing: bool = True
    system: str = platform.system().lower()
    root: str = os.path.join(os.path.split(os.path.split(__file__)[0])[0],'bin')

    def __post_init__(self):
        print(f'\n\nIntiating EddyPro Run:\n{self.eddyproFile}\n{datetime.now().isoformat()}\n')
        breakpoint()
        T1 = time.time()
        if self.system == 'windows': self.system = 'win'
        elif self.system == 'darwin': self.system = 'mac'
        cwd = os.getcwd()
        os.chdir(self.root)
        self.settings = ConfigParser()
        self.settings.read(self.eddyproFile)
        self.settings = {section:dict(self.settings[section]) for section in self.settings.sections()}
        dpath = self.settings['RawProcess_General']['data_path']
        if not self.multiProcessing:
            rp_fcc_Args = [os.path.join(self.system,'eddypro_rp'), '-s', self.system, self.eddyproFile]
            subprocess.run(rp_fcc_Args)
            print(f'RP and FCC completed: {time.time()-T1}')
        else:
            if self.multiProcessing is True:
                max_workers = 2
            else:
                max_workers = int(self.multiProcessing)
            timesteps = [datetime.strptime(step,'%Y%m%dT%H%M.float32')
                          for fld in os.listdir(dpath) 
                          if fld.isdigit() 
                          for step in os.listdir(os.path.join(dpath,fld)) 
                          if step.endswith('.float32')]
            timesteps.sort()
            stepSize = math.ceil(len(timesteps)/max_workers)
            timesteps = [[timesteps[i*stepSize].isoformat(),timesteps[:(i+1)*stepSize][-1].isoformat()]for i in range(max_workers)]
            batches = []
            batchSteps = {}
            for i,batch in enumerate(timesteps):
                template = self.settings.copy()
                step = ecf32ProjectWriter(**copy.deepcopy(template))
                step.newFile(start_date=batch[0],end_date=batch[1])
                filename = os.path.join(step.Project['out_path'],f'tmp{i}','ecf32.eddypro')
                # Turn off fcc for batches, re-run fcc after merge
                step.Project['run_fcc'] = 0
                step.writeFile(filename)
                batchSteps[i] = f"{step.Project['pr_start_date']} {step.Project['pr_start_time']} {step.Project['pr_end_date']} {step.Project['pr_end_time']}"
                rpArgs = [os.path.join(self.system,'eddypro_rp'), '-s', self.system, filename]
                batches.append(rpArgs)
            manger = multiprocessing.Manager()
            counter = manger.Value('i',0)
            lock = manger.Lock()
            # Catch outputs for writing to log (realtime output nice, but overly complicates the process)
            sp = partial(
                subprocess.run,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
                )
            with ProcessPoolExecutor(max_workers=max_workers,initializer=stagger,initargs=(counter,lock,0.5,batchSteps.copy())) as executor:
                out = {i:result for i,result in enumerate(executor.map(sp,batches))}
            for p,log in out.items():
                print(f'Process {p}')
                print(f'\n\n{log.stdout}\n\n')
            print(f'RP completed: {time.time()-T1}')
            self.mergeFCC(batches)
        os.chdir(cwd)

    def mergeFCC(self,batches):
        T1 = time.time()
        for out,header in zip(['biomet','fluxnet'],[2,1]):
            fname = self.combine([
                glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output',f'*{out}*.csv'))[0]
                for batch in batches
                if len(glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output',f'*{out}*.csv')))],header,'')
            if out == 'fluxnet':
                self.ex_file = fname
        self.combine([
            glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_user_stats',f'*.csv'))[0] 
            for batch in batches
            if len(glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_user_stats',f'*.csv')))],2,'eddypro_user_stats')
        self.combine([
            glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_stats',f'*.csv'))[0] 
            for batch in batches
            if len(glob(os.path.join(os.path.split(batch[-1])[0],'eddypro_output','eddypro_stats',f'*.csv')))],2,'eddypro_stats')
        for batch in batches:
            batchRoot = os.path.split(batch[-1])[0]
            src = os.path.join(batchRoot,'eddypro_output','eddypro_binned_cospectra')
            self.sa_bin_spectra = os.path.join(self.settings['Project']['out_path'],'eddypro_binned_cospectra')
            os.makedirs(self.sa_bin_spectra,exist_ok=True)
            shutil.copytree(src,self.sa_bin_spectra,dirs_exist_ok=True)
            src = os.path.join(batchRoot,'eddypro_output','eddypro_full_cospectra')
            self.sa_full_spectra = os.path.join(self.settings['Project']['out_path'],'eddypro_full_cospectra')
            os.makedirs(self.sa_full_spectra,exist_ok=True)
            shutil.copytree(src,self.sa_full_spectra,dirs_exist_ok=True)
            shutil.rmtree(batchRoot)
            
        print('Merge completed ...\nRunning FCC')
        # Dump fcc runs to root of temp dir 
        self.settings['FluxCorrection_SpectralAnalysis_General']['ex_file'] = self.ex_file
        self.settings['FluxCorrection_SpectralAnalysis_General']['sa_bin_spectra'] = self.sa_bin_spectra
        self.settings['Project']['bin_sp_avail']='1'
        self.settings['FluxCorrection_SpectralAnalysis_General']['sa_full_spectra'] = self.sa_full_spectra
        self.settings['Project']['full_sp_avail']='1'
        fcc = ecf32ProjectWriter(**copy.deepcopy(self.settings))
        fccName = self.eddyproFile.replace('.eddypro','_fcc.eddypro')
        fcc.writeFile(filepath=fccName)
        fccArgs = [os.path.join(self.system,'eddypro_fcc'), '-s', self.system, fccName]
        print('Run FCC: ')
        subprocess.run(fccArgs)
        print(f'FCC completed: {time.time()-T1}')
        print('file merge??')
        
    def combine(self,files,header,subdir=''):
        try:
            df = pd.concat([pd.read_csv(f,skiprows=header,header=None) for f in files])
            with open(files[0]) as f:
                h = ''.join([f.readline() for l in range(header)])
            fpath = os.path.join(self.settings['Project']['out_path'],subdir)
            os.makedirs(fpath,exist_ok=True)
            fname = os.path.join(fpath,os.path.split(files[0])[-1])
            with open(fname,'w+', newline="") as f:
                f.write(h)
                df.to_csv(f,header=False,index=False)
            return(fname)
        except:
            print('[?????]')
            breakpoint()

if __name__ == '__main__':
    print('CLI parse here ...')