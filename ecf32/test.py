import pandas as pd
import numpy as np
from ecf32Create import ecf32Write, ghgMetadataWriter


index = pd.date_range('2026-10-18T00:00:05+00:00','2026-10-19T00:01:00+00:00',freq='0.1s')
df = pd.DataFrame(
    index = index,
    data = {'a':np.random.random(len(index)),'b':np.random.random(len(index))}
)
df.columns = pd.MultiIndex.from_tuples([('a','x'),('b','y')])
df.columns.names = ['variableName','units']
breakpoint()
# ecf32Write(outputPath='testData/YYYY/mm',siteID='test',dataframe=df)