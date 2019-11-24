from __future__ import division, print_function
import os,sys,time,datetime
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
from matplotlib import pyplot as plt
from pylab import rcParams
import networkx as nx
import pandas as pd
plt.rcParams["figure.figsize"] = (15,10)
app = Flask(__name__)
print("Application started. Connect at http://127.0.0.1:5000")

def dataPreprocessing(data):
    '''
        dateTime       1225 non-null object
        duration       1225 non-null int64
        name           1136 non-null object
        phoneNumber    1225 non-null int64
        rawType        1225 non-null int64
        timestamp      1225 non-null int64
        type           1225 non-null object
    '''
    data = data[data['type'].isin(["INCOMING", "OUTGOING"])]
    data.name.fillna(data.phoneNumber, inplace=True)
    if(len(data > 1500)):
        data = data[:1499]
    incData = data[data['type'] == "INCOMING"]
    outData = data[data['type'] == "OUTGOING"]
    uniqueNames = data['name'].value_counts().index.to_list()
    nxCount = data['name'].value_counts().to_dict()
    nxIncoming = incData['name'].value_counts().to_dict()
    nxOutgoing = outData['name'].value_counts().to_dict()
    nxDuration = dict()
    for i in range(len(data)):
        name, duration = data.iloc[i]['name'], data.iloc[i]['duration'] 
        if(name not in nxDuration):
            nxDuration[name] = duration
        else:
            nxDuration[name] += duration
    nxDuration = {x:y for x,y in nxDuration.items() if y!=0}
    return normalization(nxCount), normalization(nxDuration), normalization(nxIncoming), normalization(nxOutgoing), uniqueNames

def drawGraph(name, uniqueNames, criterion, scaling=5000):
    g = nx.Graph()
    g.add_node(name)
    nodes = []
    for i in range(len(uniqueNames)):
        nodes.append((name,uniqueNames[i]))
    g.add_edges_from(nodes)
    currentTime = time.time()    
    formattedTime = datetime.datetime.fromtimestamp(currentTime).strftime('%Y%m%d_%H%M%S')
    img = 'static/{}_{}.png'.format(name, formattedTime)
    nx.draw(g, nodelist=criterion.keys(), node_size=[v * scaling for v in criterion.values()],with_labels=True)
    plt.savefig(img)
    plt.clf()
    return img

def normalization(data):
    keys = data.keys()
    minValue, maxValue = min(data.values()), max(data.values())
    diff = maxValue - minValue
    for i in keys:
        data[i] = ((data[i] - minValue) / diff)
    return data

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html',button_text = "Generate")

@app.route('/generate', methods=['POST'])
def generate():
    csvFile = request.files['file']
    name = request.form['username']
    criterion = request.form['graphCriterion']
    nxCount, nxDuration, nxIncoming, nxOutgoing, uniqueNames = dataPreprocessing(pd.read_csv(csvFile))
    if(criterion == "count"):
        img = drawGraph(name, uniqueNames, nxCount)
    elif(criterion == "duration"):
        img = drawGraph(name, uniqueNames, nxDuration, scaling=9000)
    elif(criterion == "incoming"):
        img = drawGraph(name, uniqueNames, nxIncoming)
    else:
        img = drawGraph(name, uniqueNames, nxOutgoing)
    return render_template("result.html", result = img )

if __name__ == '__main__':
    app.run(debug=True)

