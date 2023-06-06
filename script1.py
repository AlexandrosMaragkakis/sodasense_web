# folium heatmap
import sys
import psycopg2 # install the binary version!
import folium
from folium import plugins
import os

print(os.getcwd())

# Connect to TimescaleDB
userid = sys.argv[1]


#conn = psycopg2.connect("dbname=sodasense user=postgres password=password host=192.168.48.222 port=5432")
CONNECTION = "dbname=sodasense user=postgres password=password host=192.168.48.222 port=5432"
with psycopg2.connect(CONNECTION) as conn:
    cursor = conn.cursor()
    # use the cursor to interact with your database
    # cursor.execute("SELECT * FROM table")

    # Retrieve latitude and longitude values from the database
    lat = []
    lng = []
    cursor.execute(f"SELECT latitude, longitude FROM coordinates WHERE userid='{userid}' LIMIT 10")
    for row in cursor.fetchall():
        lat.append(row[0])
        lng.append(row[1])




    

# Create a map centered on the mean of the latitude and longitude values
center_lat = sum(lat) / len(lat)
center_lng = sum(lng) / len(lng)
m = folium.Map(location=[center_lat, center_lng], zoom_start=12)

# Create a heatmap layer using the latitude and longitude values
heatmap_data = list(zip(lat, lng))
heatmap_layer = plugins.HeatMap(heatmap_data)
m.add_child(heatmap_layer)
m.save("tmp_heatmap.html")
os.system("chmod 777 tmp_heatmap.html")