
from pyunicorn.eventseries import eca
import pandas as pd
import rasterio
import numpy as np
import os


# def judgment_read_data(Path, Moth, File):
#     Data = []
#     for j, i in enumerate(File):
#         with rasterio.open(Path + Moth + i) as Src_read:
#             profile = Src_read.profile
#             temp = Src_read.read()[0]
#             temp = pd.DataFrame(temp)
#             temp[temp == profile.data['nodata']] = np.nan
#             temp = temp.values
#         Data.append(temp)
#     Data = np.array(Data)
#     return Data


def read_data(Path, Moth, File, Judgment1, Judgment2, Profile):
    for j, i in enumerate(File):
        with rasterio.open(Path + Moth + i) as Src_read:
            temp = Src_read.read()[0]
            # print(temp[0][0])
            temp1 = pd.DataFrame(temp)
            temp1[temp1 == Profile.data['nodata']] = np.nan
            temp1[np.isnan(Judgment1)] = np.nan
            temp1[(~np.isnan(temp1)) & (temp1 < Judgment1)] = 1
            temp1[(~np.isnan(temp1)) & (temp1 >= Judgment1)] = 0
            temp2 = pd.DataFrame(temp)
            # print(temp2[0][0])
            temp2[temp2 == Profile.data['nodata']] = np.nan
            # print(Judgment1[0][0])
            temp2[np.isnan(Judgment2)] = np.nan
            temp2[(~np.isnan(temp2)) & (temp2 <= Judgment2)] = 0
            temp2[(~np.isnan(temp2)) & (temp2 > Judgment2)] = 1
            # print(temp2[0][0])
            temp1 = temp1.values.reshape(-1, 1)
            temp2 = temp2.values.reshape(-1, 1)
        # print(float(profile.data['nodata']))
        if j == 0:
            data1 = temp1
            data2 = temp2
        else:
            data1 = np.hstack([data1, temp1])
            data2 = np.hstack([data2, temp2])
    return data1, data2


def Eca(dataA, dataB):
    if (np.isnan(dataA).sum() + np.isnan(dataB).sum()) > 0:
        return np.nan
    ECA_data = eca.ECA(dataA, dataB, delT=0)
    return ECA_data[0]


moths = ['03_04/', '05_06/', '07_08_09/']
path1 = r'E:/temp/LST-NDVI/MOD11-merge/'
path2 = r'E:/temp/LST-NDVI/MOD13-select/'
path3 = r'E:/temp/LST-NDVI/LST_Day_1km-NDVI/LST_Day_1km-NDVI-原格式/'
outpath = r'E:/temp/LST-NDVI/LST_Day_1km-NDVI/LST_NDVI/'
outfile1 = r'LST_min.tif'
outfile2 = r'LST_max.tif'

for moth in moths:
    file1 = os.listdir(path1 + moth)
    file2 = os.listdir(path2 + moth)
    file3 = os.listdir(path3 + moth)

    judgment = []
    profiles = []
    for j, i in enumerate(file3):
        with rasterio.open(path3 + moth + i) as Src_read:
            profile = Src_read.profile
            profiles.append(profile)
            temp = Src_read.read()[0]
            temp = pd.DataFrame(temp)
            temp[temp == profile.data['nodata']] = np.nan
            temp = temp.values
        judgment.append(temp)
    profile.data['dtybe'] = 'float32'
    height = profile.data['height']
    width = profile.data['width']
    judgment = np.array(judgment)
    # data1_1 = read_data(path1, moth, file1, judgment[0], 0.1)
    # data1_9 = read_data(path1, moth, file1, judgment[1], 0.9)
    data1 = read_data(path1, moth, file1, judgment[0], judgment[1], profiles[0])
    data2 = read_data(path2, moth, file2, judgment[2], judgment[3], profiles[2])
    # data2_9 = read_data(path2, moth, file2, judgment[3], 0.9, profiles[3])
    min1 = pd.DataFrame(np.array([-i for i in map(Eca, data1[0], data2[0])]).reshape(height, width))
    min2 = pd.DataFrame(np.array([i for i in map(Eca, data1[0], data2[1])]).reshape(height, width))
    max1 = pd.DataFrame(np.array([-i for i in map(Eca, data1[1], data2[0])]).reshape(height, width))
    max2 = pd.DataFrame(np.array([i for i in map(Eca, data1[1], data2[1])]).reshape(height, width))
    min_data = min1.mask((~np.isnan(min2)) & (min2 > -min1), min2).values
    max_data = max1.mask((~np.isnan(max2)) & (max2 > -max1), max2).values
    min_data[min_data == -0] = 0
    max_data[max_data == -0] = 0
    min_data *= 100
    max_data *= 100
    min_data[np.isnan(min_data)] = -3000
    max_data[np.isnan(max_data)] = -3000
    with rasterio.open(outpath + moth + outfile1, 'w', **profile) as srt_write1:
        srt_write1.write(min_data.astype(profile.data['dtype']), 1)
    with rasterio.open(outpath + moth + outfile2, 'w', **profile) as srt_write2:
        srt_write2.write(max_data.astype(profile.data['dtype']), 1)


