from quart import Quart
from quart import render_template
from quart import jsonify
from quart import redirect, request, url_for
import twint
from quart import make_response
import asyncio
from quart import send_file
import csv
import json
import codecs
import os
types_of_encoding = ["utf8", "cp1252"]

app = Quart(__name__)
app.clients = set()

@app.route('/')
@app.route('/index')
async def index():    
    return await render_template('index.html', title='Home')

@app.route('/search')
async def search():
    #for task in asyncio.Task.all_tasks():
    #    task.cancel()
    searchTerm = request.args.get('sterm')
    page = request.args.get('page')
    if page is None:
        page = 0
    else:
        page = int(page)
        if page <= 0:
            page = 1
    data = [searchTerm, page]
    return await render_template('search.html', title="Search", sterm=searchTerm, page=page)

# get db data for searched tweets from Database
@app.route('/getdata')
async def getdata():    
    searchTerm = request.args.get('sterm')
    page = request.args.get('page')
    return await jsonify({'status':'OK'})

# collect tweets data using twint module
@app.route('/searchtweets')
async def searchtweets():
    if os.path.exists("outputs/search.csv"):
        os.remove("outputs/search.csv")  
    sterm = request.args.get('sterm')
    dbname = sterm + '.db'
    #twint config
    c = twint.Config()
    c.Store_csv = True
    c.Output = "outputs/search.csv"
    c.Custom["tweet"] = ["id", "user_id", "username", "name", "tweet", "retweets_count"]

    # equivalent to `-s` bitcoin
    c.Search = sterm
    # set database name
    #c.Database = "asasdf"
    # Custom output format
    c.Format = "Tweet id: {id} | Username: {username}"
    # set limit for search
    #c.Limit = 2    
    c.Resume = "history_ids.txt"
    twint.run.Search(c)

    return jsonify({'status':'OK'})

@app.route('/getcsvdata')
async def getcsvdata():    
    page = request.args.get('page')    
    csvfile = codecs.open('outputs/search.csv', encoding = 'utf8', errors ='replace')   
    reader = csv.reader(csvfile)
    headers = next(reader, None)
    column = {}
    for h in headers:
        column[h] = []
    
    if page is None:
        page = 0
    
    page = int(page) - 1
    print(page)

    for i in range(10*page):
        next(reader)
    
    for i in range(10):
        row = next(reader)
        for h, v in zip(headers, row):
            column[h].append(v)
    
    # calculate row count
    row_count = sum(1 for row in reader) 
    row_count = row_count + 10*page + 10

    result = {
        'data': column,
        'count': row_count
    }
    
    return json.dumps(result)

@app.route('/getcsvdatacount')
async def getcsvdatacount():
    if os.path.exists("outputs/search.csv"):
        csvfile = codecs.open('outputs/search.csv', encoding = 'utf8', errors ='replace')  
        reader = csv.reader(csvfile)
        row_count = sum(1 for row in reader) - 1
    else:
        row_count = 0
    result = {
        'count': row_count
    }
    return json.dumps(result)

# download csv
@app.route('/getcsv', methods = ['GET', 'POST'])
def getCSV():    
    return send_file('outputs/search.csv',
                     mimetype='text/csv',
                     attachment_filename='search_result.csv',
                     as_attachment=True)

if __name__ == "__main__":
    app.run()