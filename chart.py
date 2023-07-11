import sys
import influxdb_client
import folium
import time as mytime
import os

if os.path.exists("tmp/log"):
    os.remove("tmp/log")

total_time_start = mytime.time()


userid = sys.argv[1]
start_timestamp = sys.argv[2]
end_timestamp = sys.argv[3]

# Connect to InfluxDB
bucket = "alex"
org = "SoDaSense"
token = "Z5oh-daPx5m78z9gwR9OduqZzo51WXjwR9GwwUy8eY6QKxZgafrF9yf96MGySCjPN11AdfkHfp2bAsiVeDaMsw=="
url = "http://192.168.48.222:18086"

client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

query_api = client.query_api()

query = f'''combined = from(bucket: "alex")
   |> range(start: {start_timestamp}, stop: {end_timestamp})
   |> filter(fn: (r) => r._measurement == "location" and r.user_id == "{userid}" and (r._field == "longitude" or r._field == "latitude"))
   |> aggregateWindow(every: 15s, fn: median, createEmpty: false)
   |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
combined'''


start_time = mytime.time()
result = query_api.query(org=org, query=query)
end_time = mytime.time()
execution_time = end_time - start_time

with open("tmp/log", "a") as log_file:
    log_file.write("Query execution time: " +
                   str(execution_time) + " seconds\n")

lat = []
lng = []
time = []
start_time = mytime.time()
for table in result:
    for row in table:
        lat.append(row['latitude'])
        lng.append(row['longitude'])
        timestamp = row['_time']
        time.append(timestamp)

end_time = mytime.time()
execution_time = end_time - start_time

with open("tmp/log", "a") as log_file:
    log_file.write("Lists execution time: " +
                   str(execution_time) + " seconds\n")

with open("tmp/log", 'a') as f:
    f.write("Number of points: " + str(len(lat)))
    f.write('\n')

if len(lat) == 0:
    exit()

start_time = mytime.time()
routes = []
current_route = []
previous_time = None
time_threshold = 1_000  # Adjust the time threshold as per your requirement

for i in range(len(lat)):
    if previous_time is None:
        current_route.append((lat[i], lng[i]))
    else:
        time_gap = (time[i] - previous_time).total_seconds()
        if time_gap > time_threshold:
            routes.append(current_route)
            current_route = [(lat[i], lng[i])]
        else:
            current_route.append((lat[i], lng[i]))
    previous_time = time[i]

routes.append(current_route)
end_time = mytime.time()
execution_time = end_time - start_time

with open("tmp/log", "a") as log_file:
    log_file.write("Routes identification time: " +
                   str(execution_time) + " seconds\n")

if len(routes) == 0:
    exit()


start_time = mytime.time()
# Define colors for each route
colors = ['blue', 'red', 'green', 'purple', 'orange',
          'darkblue', 'darkred', 'darkgreen', 'cadetblue', 'pink']

# Create a map centered on the mean of the latitude and longitude values
center_lat = sum(lat) / len(lat)
center_lng = sum(lng) / len(lng)
m = folium.Map(location=[center_lat, center_lng], zoom_start=12)

# Add markers for each point in each route with different colors
for i, route in enumerate(routes):
    color = colors[i % len(colors)]  # Assign color from the colors list
    for point in route:
        folium.CircleMarker(
            location=point,
            radius=4,  # Adjust the radius of the marker as per your requirement
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=1.0
        ).add_to(m)


# Add markers for each point in each route with different colors
for i, route in enumerate(routes):
    color = colors[i % len(colors)]  # Assign color from the colors list
    for point in route:
        folium.CircleMarker(
            location=point,
            radius=4,  # Adjust the radius of the marker as per your requirement
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=1.0
        ).add_to(m)

    # Add start and end markers for each route
    start_point = route[0]
    end_point = route[-1]
    folium.Marker(
        location=start_point,
        icon=folium.Icon(color='green', icon='flag', prefix='fa'),
    ).add_to(m)
    folium.Marker(
        location=end_point,
        icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa'),
    ).add_to(m)

# Save the map to an HTML file
m.save(f"./tmp/tmp_{userid}_heatmap.html")
end_time = mytime.time()
execution_time = end_time - start_time

with open("tmp/log", "a") as log_file:
    log_file.write("Chart drawing time: " +
                   str(execution_time) + " seconds\n")

total_time_end = mytime.time()
execution_time = total_time_end - total_time_start

with open("tmp/log", "a") as log_file:
    log_file.write("Total execution time: " +
                   str(execution_time) + " seconds\n")
