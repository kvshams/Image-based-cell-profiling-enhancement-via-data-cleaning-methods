import resource, os
import pandas as pd
import numpy as np
import sqlite3

from statsmodels import robust
from scipy import stats


def limit_memory(maxsize):
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (maxsize, hard))


limit_memory(16 * 10e9)

moa = pd.read_csv('moa.txt', sep="\t")
moas = list(moa['Metadata_broad_sample'])

selected_drugs = moas
selected_drugs += ['DMSO']

dff = pd.read_csv('feature_list.txt', sep="\t", header=None)
features = list(dff.iloc[:, 0])
features += ['TableNumber', 'ImageNumber', 'ObjectNumber']

plates = [24277, 24280, 24293, 24294, 24295, 24296, 24297, 24300, 24301, 24302, 24303, 24304, 24305, 24306, 24307,
          24308, 24309, 24310, 24311, 24313, 24319, 24320, 24321, 24352, 24357, 25937, 25938, 25939, 25943, 25944,
          25945, 25949, 25955, 25962, 25965, 25966, 25967, 25968, 25983, 25984, 25985, 25986, 25987, 25988, 25989,
          25990, 25991, 25992, 26224, 26232, 26239, 26247, ]

for pl in plates:
    # address
    os.system('wget ftp://parrot.genomics.cn/gigadb/pub/10.5524/100001_101000/100351/Plate_' + str(
        pl) + '.tar.gz --directory-prefix=/home/jupyter/Image_Analysis/edit/Data/test_data')

    os.system('tar xvzf /home/jupyter/Image_Analysis/edit/Data/test_data/Plate_' + str(pl) + '.tar.gz')
    os.system('rm -rf /home/jupyter/Image_Analysis/edit/Data/test_data/Plate_' + str(pl) + '.tar.gz')

    # address
    path = 'gigascience_upload/Plate_' + str(pl) + '/extracted_features/' + str(pl) + '.sqlite'
    print(os.getcwd())
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    print('####### opening database tables')
    cytoplasm = pd.read_sql_query("select * from Cytoplasm", conn)
    cytoplasm = cytoplasm[cytoplasm.columns.intersection(features)]

    nuclei = pd.read_sql_query("select * from Nuclei", conn)
    nuclei = nuclei[nuclei.columns.intersection(features)]

    cells = pd.read_sql_query("SELECT * FROM Cells;", conn)
    cells = cells[cells.columns.intersection(features)]

    images = pd.read_sql_query("SELECT * FROM Image;", conn)
    wells = images[['TableNumber', 'ImageNumber', 'Image_Metadata_Well']]
    wells = wells.rename(columns={'Image_Metadata_Well': 'Metadata_Well'})

    print('####### merging')
    merged = cells.merge(nuclei, on=['TableNumber', 'ImageNumber', 'ObjectNumber'])
    merged = merged.merge(cytoplasm, on=['TableNumber', 'ImageNumber', 'ObjectNumber'])
    merged = merged.merge(wells, on=['TableNumber', 'ImageNumber'])

    # address
    path = '/home/jupyter/Image_Analysis/edit/Data/test_data/gigascience_upload/Plate_' + str(
        pl) + '/profiles/mean_well_profiles.csv'
    mean_profile = pd.read_csv(path)
    broad_sample = mean_profile[['Metadata_Well', 'Metadata_broad_sample']]

    merged = merged.merge(broad_sample, on=['Metadata_Well'])

    del merged['TableNumber']
    del merged['ImageNumber']
    del merged['ObjectNumber']

    data = merged[merged['Metadata_broad_sample'].isin(selected_drugs)]

    conn.close()
    os.system('rm -rf /home/jupyter/Image_Analysis/edit/Data/test_data')

    data.to_csv('plate' + str(pl) + '.csv')
    print('####### plate saved!')
