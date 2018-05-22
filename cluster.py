
import pandas as pd
from math import radians, cos, sin, asin, sqrt, atan2
import math

import os
#import matplotlib.pyplot as plt
#import shapefile

#from mpl_toolkits.basemap import Basemap
from gmplot import gmplot

input_path = "/media/sf_E_DRIVE/Recommendation/Dataset/Foursquare/checkin/"
output_path = "/media/sf_E_DRIVE/Recommendation/Analysis/Foursquare/output/"

def point_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6373.0 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def decide_transition(center_time_list):
    if len(center_time_list) > 1:
        center_time_min = [center_time[0] for center_time in center_time_list]
        center_time_max = [center_time[1] for center_time in center_time_list]
        for i in center_time_max:
            for j in center_time_min:
                if i < j:
                    print("Detected one transition case!")
                    return 1
    return 0

def greedy_clustering(user):

    # sort by visiting freq
    vid_freq = user.groupby(['vid']).size().sort_values(ascending = False)
    vid_geo = user.groupby(['vid'])['lat', 'lon'].mean()

    center_no = 0
    center_list_geo = []
    center_list_time = []
    vid_frame = pd.DataFrame({'vid': vid_freq.index, 'freq': vid_freq.values})
    vid_frame['center'] = -1

    for i in range(0, len(vid_freq.index)):
        vid_i = vid_freq.index[i]
        if vid_frame.loc[vid_frame['vid'] == vid_i, 'center'].values == -1:
            center_no = center_no + 1
            Center = []
            Center.append(vid_i)
            for j in range(i + 1, len(vid_freq.index)):
                vid_j = vid_freq.index[j]

                if vid_frame.loc[vid_frame['vid'] == vid_j, 'center'].values == -1:
                    lon1, lat1 = vid_geo.loc[vid_i, ['lat', 'lon']].values[1], vid_geo.loc[vid_i, ['lat', 'lon']].values[0]
                    lon2, lat2 = vid_geo.loc[vid_j, ['lat', 'lon']].values[1], vid_geo.loc[vid_j, ['lat', 'lon']].values[0]
                    if point_distance(lon1, lat1, lon2, lat2) < 10:
                        Center.append(vid_j)
                        vid_frame.ix[vid_frame['vid'] == vid_j, 'center'] = center_no

            if vid_freq[Center].sum() > vid_freq.sum() * 0.02:
                user_sel = user.loc[user['vid'].isin(Center)]
                center_geo = user_sel[['lat', 'lon']]
                center_geo = center_geo.drop_duplicates()
                center_zip = list(zip(center_geo.lat, center_geo.lon))
                center_list_geo.append(center_zip)

                user_sel['t_utc'] = pd.to_datetime(user_sel['t_utc'], format = '%a %b %d %H:%M:%S +0000 %Y', utc = True)
                center_time = [min(user_sel['t_utc']), max(user_sel['t_utc'])]
                center_list_time.append(center_time)

    ui = str(user['vid'].iloc[0])
    print("user:" + ui)
    print("# of centers:" + str(len(center_list_geo)))
    result = decide_transition(center_list_time)
    # user_plot(ui, center_list_geo)
    return result;

def user_statistic(data):
    per_user = data.groupby(['uid']).size()
    per_user = data.groupby(['uid']).apply(greedy_clustering)
    per_user.to_csv(output_path + "transition_count.csv")

    return 0;

# plot user clusters
def user_plot(ui, center_list_geo):
    # Place map
    gmap = gmplot.GoogleMapPlotter(40.7128, -74.006, 13)
    color_list = ['#DC143C', '#4169E1', '#FF8C00', '#00FF00', '#FFFF00', '#FFC0CB', '#8A2B12', '#C0C0C0']

    for idx, center in enumerate(center_list_geo):
        lats, lons = zip(*center)
        gmap.scatter(lats, lons, color_list[idx], size = 20, marker = True)

    # Draw
    gmap.draw(output_path + ui + ".html")
    return 0;

if __name__ == '__main__':

    data = pd.read_csv(input_path + "dataset_TSMC2014_NYC.txt", sep = '\t', names = ['uid', 'vid', 'vcid', 'vcn', 'lat', 'lon', 't_off', 't_utc'])
    user_statistic(data)
