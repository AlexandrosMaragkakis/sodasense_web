import sqlite3
import folium
from folium import plugins
import datetime
import pandas as pd

lat = []
lng = []
dates = []

def ms_to_current_date(ms):
    return datetime.datetime.fromtimestamp(ms/1000).strftime('%Y-%m-%d %H-%M-%S')

def get_gps_records(db_filename):

    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    for row in cur.execute("SELECT date, lat, lng FROM coordinates"):
        dates.append(ms_to_current_date(row[0])) 
        lat.append(row[1])
        lng.append(row[2])



get_gps_records("db.db")
get_gps_records("db_zamir.db")

column_names = ['date','longitude', 'latitude']
df = pd.DataFrame(list(zip(dates,lng,lat)), columns=column_names)
time_index = list(df['date'].sort_values().astype('str').unique())

data = []
for _, d in df.groupby('date'):
    data.append([[row['latitude'], row['longitude']]for _, row in d.iterrows()]) ## ???????????????????????



# Create a map centered on the mean of the latitude and longitude values
center_lat = sum(lat) / len(lat)
center_lng = sum(lng) / len(lng)
m = folium.Map(location=[center_lat, center_lng], zoom_start=12) # tripoli coordinates center = 37.5101, 22.3726
                                                                 # search internet for city center

# Create a heatmap layer using the latitude and longitude values
heatmap_data = list(zip(lat, lng))
heatmap_layer = plugins.HeatMapWithTime(data,
                                        index=time_index,
                                        radius=14,
                                        max_opacity=0.6,
                                        auto_play=True,
                                        blur=1,)
m.add_child(heatmap_layer)
#heatmap_layer.add_to(m)

# Save the map as an HTML file
m.save("heatmap_timed_test.html")
