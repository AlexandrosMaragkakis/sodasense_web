import sqlite3
import folium
from folium import plugins
from flask import Flask, render_template


app = Flask(__name__)

@app.route('/')
def heatmap():
    # Connect to the SQLite database
    con = sqlite3.connect("db.db")
    cur = con.cursor()

    # Retrieve latitude and longitude values from the database
    lat = []
    lng = []
    for row in cur.execute("SELECT lat, lng FROM coordinates"):
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

    # Render the template with the map
    return render_template('heatmap.html', map=m._repr_html_())

if __name__ == '__main__':
    app.run()
