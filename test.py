import pandas as pd, numpy as np, matplotlib.pyplot as plt, time
from sklearn.cluster import DBSCAN
from sklearn import metrics
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
import folium

from folium import plugins 
import branca.colormap as cm


# define the number of kilometers in one radian
kms_per_radian = 6371.0088

# load the data set
df = pd.read_csv('data/summer-travel-gps-full.csv', encoding='utf-8')

# represent points consistently as (lat, lon)
coords = df[['lat', 'lon']].values

# define epsilon as 1.5 kilometers, converted to radians for use by haversine
epsilon = 1.5 / kms_per_radian

start_time = time.time()
db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
cluster_labels = db.labels_

# get the number of clusters
num_clusters = len(set(cluster_labels))

# all done, print the outcome
message = 'Clustered {:,} points down to {:,} clusters, for {:.1f}% compression in {:,.2f} seconds'
print(message.format(len(df), num_clusters, 100*(1 - float(num_clusters) / len(df)), time.time()-start_time))
print('Silhouette coefficient: {:0.03f}'.format(metrics.silhouette_score(coords, cluster_labels)))


# turn the clusters in to a pandas series, where each element is a cluster of points
clusters = pd.Series([coords[cluster_labels==n] for n in range(num_clusters)])

def get_centermost_point(cluster):
    count = len(cluster)
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)    
    ## To find the furthest point
#     centermost_point = max(cluster, key=lambda point: great_circle(point, centroid).m)
#     return tuple(centermost_point)
    
    # to get radius in meter
    radius_m = max(great_circle(point, centroid).m for point in cluster)
    return (centroid, radius_m, count)
    
cent_rad = clusters.map(get_centermost_point)

# unzip the list of centermost points (lat, lon) tuples into separate lat and lon lists
coordinates, rad,count = zip(*cent_rad)
lats, lons = zip(*coordinates)

# from these lats/lons create a new df of one representative point for each cluster
rep_points = pd.DataFrame({ 'lat':lats,'lon':lons, 'rad':rad, 'C_count':count})
rep_points['density'] = rep_points['C_count']/(rep_points['rad'] + 1)
center = [rep_points.lat.mean(), rep_points.lon.mean()]
print(rep_points.lat.mean(), rep_points.lon.mean())

colormap = cm.linear.Blues_09.scale(vmin=rep_points.density.min(),vmax=rep_points.density.max())

map1 = folium.Map(location= center, zoom_start=6,)

#'''
# ADDING CUSTOM FUNCTION
incidents = plugins.MarkerCluster(
            icon_create_function="""
            function (cluster) {
                var markers = cluster.getAllChildMarkers();
                    i = " marker-cluster-";
                    var n = 0;
				for (var j = 0; j < markers.length; j++) {
					n += markers[j].number;
				}
            return i += 10 > n ? "small" : 100 > n ? "medium" : "large", new L.DivIcon({
                html: n ,
                className:"marker-cluster"+i,
                iconSize:new L.Point(40,40)});
            }
            """
            ).add_to(map1)
#''' 


# incidents = plugins.MarkerCluster().add_to(map1)

for lat, lng, rad, d,c in zip(rep_points.lat, 
                              rep_points.lon, 
                              rep_points.rad, 
                              rep_points.density, 
                              rep_points.C_count):

   xxx= folium.Circle(
        location=[lat, lng],
        radius= rad,
        fill=True,
        color=colormap(d)).add_to(map1)
        
   yyy=  folium.Marker(location =[lat, lng], 
                  popup=c,
                  number = c,
                  icon=folium.Icon(color='blue', icon='ok-sign')).add_child(xxx)
   yyy.add_to(incidents)


map1.save(" my_map5.html " ) 

