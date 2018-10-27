import requests
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import contextily as ctx
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, render_template, request

from wtforms import Form, StringField, validators
from wtforms.fields.html5 import DateField, TimeField

class RegistrationForm(Form):
    start = StringField('Current Location', [validators.Length(min=6, max=50)])
    dest = StringField('Destination', [validators.Length(min=6, max=50)])
    date = DateField()
    time = TimeField()
   
def add_basemap(ax, zoom, url='http://tile.stamen.com/terrain/tileZ/tileX/tileY.png'):
    xmin, xmax, ymin, ymax = ax.axis()
    basemap, extent = ctx.bounds2img(xmin, ymin, xmax, ymax, zoom=zoom, url=url)
    ax.imshow(basemap, extent=extent, interpolation='bilinear')
    # restore original x/y limits
    ax.axis((xmin, xmax, ymin, ymax))
    
    
def get_route():
    # authentication
    payload = {"client_id": '98914944-a2e6-483f-833b-c9d5e95730a9' ,
               "client_secret": "WrFtiNXG1wWHZCzivEySFcOihwjNAs2huNncHTwdvFQ=",
               "grant_type": "client_credentials",
               "scope": "transportapi:all"
              }
    
    r = requests.post('https://identity.whereismytransport.com/connect/token', 
                      data=payload)
    #print(r)
    if 'access_token' in r.json():
        access_token = r.json()['access_token']
    
    
    # get a journey
    start_lon = 28.226581
    start_lat = -26.051401
    end_lon = 28.056754 
    end_lat = -26.111866
    
    payload = {
        "geometry":{
            "type": "MultiPoint",
            "coordinates":[
                [
                    start_lon, start_lat
                ],
                [
                    end_lon, end_lat
                ]
            ]
        },
        "maxIteneraries": 5,
        "time": "2018-10-27T19:00:00Z",
        "timeType": "ArriveBefore"
    }
    
    
    headers = {
        "Authorization": "Bearer "+ access_token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    journey = requests.post(
        'https://platform.whereismytransport.com/api/journeys', 
        json=payload,
        headers=headers
    )
    #print(journey)

    options = {}
    barplot = {}
    for i, itinerary in enumerate(journey.json()["itineraries"]):
        duration = itinerary['duration']
        distance = itinerary['distance']['value']
        fare = 0
        mode = []
        points = []
        for leg in itinerary['legs']:
            if "fare" in leg:
                fare += leg['fare']['cost']['amount']
            if leg['type'] != 'Walking':
                mode.append(leg['line']['agency']['name'])
            else:
                mode.append(leg['type'])
            points += leg["geometry"]["coordinates"]    
        print(duration, fare, distance, mode)
        options[i] = {"duration": duration,
                    "fare": fare,
                    "distance": distance,
                    "mode": mode,
                    "points": points}
        barplot[i] = {"Duration minutes": duration/60,
                    "Fare ZAR": fare,
                    "Distance KM": distance/1000}

    fig, ax = plt.subplots(len(barplot.keys()), figsize=(5,10))
    for key in list(barplot.keys()):
        y_pos = np.arange(len(barplot[key].keys()))
        print(y_pos)
        print(barplot[key].values())
        ax[key].barh(y_pos, list(barplot[key].values()), align='center', color='green', ecolor='black')
        ax[key].set_yticks(y_pos)
        ax[key].set_yticklabels(barplot[key].keys())
        ax[key].invert_yaxis()  # labels read top-to-bottom
        #ax[key].set_xlabel('Route Details')
        ax[key].set_title('Route Details')

    fig.tight_layout()
    fig.savefig("static/options.png")

    fig, ax = plt.subplots(len(options.keys()), figsize=(6,10))
    for key in list(options.keys()):
        option = options[key]
        df = pd.DataFrame(data=option['points'],columns=['lon', 'lat'])
        df['coordinates'] = list(zip(df.lon, df.lat))
        df['coordinates'] = df['coordinates'].apply(Point)
        gdf = gpd.GeoDataFrame(df, geometry="coordinates")
        gdf.crs = {'init': 'epsg:4326'}
        gdf.to_crs(epsg=3857, inplace=True)
        gdf.plot(figsize=(4, 4), alpha=0.5, edgecolor='red', color='red', ax=ax[key])
        add_basemap(ax[key], zoom=12)
        ax[key].axis('off')
        ax[key].set_title(','.join(list(set(option['mode']))))
    
    fig.tight_layout()
    fig.savefig("static/route.png")
    
    return journey
        
app = Flask(__name__)
    
@app.route('/', methods=['GET', 'POST'])
def index():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        start = form.start.data
        dest = form.dest.data,
        date = form.date.data
        time = form.time.data
        #return redirect(url_for('result'))
        route = get_route()
        return render_template('results_page.html', route=route)
    return render_template('app_new.html', form=form)

# Example of other route
@app.route('/result')
def result():
    route = get_route()
    return render_template('results_page.html', route=route)
