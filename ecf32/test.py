import pandas as pd
import numpy as np
import os
from ecf32Create import highFrequency, ghgMetadataWriter


index = pd.date_range('2026-10-18T00:00:05+00:00','2026-10-19T00:01:00+00:00',freq='0.1s')
df = pd.DataFrame(
    index = index,
    data = {'a':np.random.random(len(index)),'b':np.random.random(len(index)),'c':np.array([i for i,_ in enumerate(index)])}
)
df.columns = pd.MultiIndex.from_tuples([('a','x'),('b','y'),('c','b')])
df.columns.names = ['variableName','units']
outputPath = os.path.join(os.path.split(__file__)[0],'testData')
highFrequency(outputPath=outputPath,siteID='testSite',fileID='testFile').loadDataFrame(dataframe=df.astype('float32'))