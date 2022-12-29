from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.crypto import get_random_string
from string import ascii_uppercase
from django.views.generic import ListView
from .models import Collection
import requests
import csv
import petl as etl
import logging
from datetime import datetime
import os
_logger = logging.getLogger('django')

# Create your views here.
class CollectionsListView(ListView):
    model = Collection

    context_object_name = 'collections'

    queryset = Collection.objects.all().order_by('-date')[:10]

    template_name = "collections_list.html"

class CollectionListView(ListView):
    model = Collection

    context_object_name = 'collection'

    template_name = 'collection_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fileName'] = self.kwargs['fileName']
        context['csvFileContent'] = etl.fromcsv('csvFiles/a' + self.kwargs['fileName'])
        context['csvFileContent'] = etl.rowslice(context['csvFileContent'], 10)
        return context

class CollectionListViewShowMore(CollectionListView, ListView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fileName'] = self.kwargs['fileName']
        context['csvFileContent'] = etl.fromcsv('csvFiles/a' + self.kwargs['fileName'])
        context['csvFileContent'] = etl.rowslice(context['csvFileContent'], 20)
        return context

def fetchData():
  r = requests.get('https://swapi.dev/api/people')
  # Export the data for use in future steps
  return r.json()

def changeDateFormat(dateStr):
    for char in dateStr:
        if char in ascii_uppercase:
            dateStr = dateStr.replace(char, '')
    dateStr = datetime.strptime(dateStr, '%Y-%m-%d%H:%M:%S.%f')
    dateStr = dateStr.date()
    return dateStr

def cleanCsv(filePath, fileName):
    table1 = etl.fromcsv(filePath)
    table2 = etl.cutout(table1, 'films')
    table3 = etl.cutout(table2, 'species')
    table4 = etl.cutout(table3, 'vehicles')
    table5 = etl.cutout(table4, 'starships')
    table6 = etl.cutout(table5, 'created')
    table7 = etl.cutout(table6, 'url')
    table8 = etl.addfield(table7, 'date', lambda row: row['edited'])
    table9 = etl.convert(table8, 'date', lambda row: changeDateFormat(row))
    table10 = etl.cutout(table9, 'edited')
    table11 = etl.convert(table10, 'homeworld', lambda row: requests.get(row).json()['name'])
    
    etl.tocsv(table11, ("csvFiles/a" + fileName))
    if os.path.exists(filePath):
        os.remove(filePath)

def fetchCollection(request):
    #Get data from API
    jsonData = fetchData()['results']
    #Generate unique name for file and create file in system
    fileName = get_random_string(20) + ".csv"
    dataFile = open('csvFiles/%s' % fileName, 'w')
    #Prepare new record in database
    collection = Collection(
        filePath = 'csvFiles/%s' % fileName,
        fileName = fileName
    )
    csv_writer = csv.writer(dataFile)
    count = 0

    #Convert data from JSON to CSV
    for data in jsonData:
        if count == 0:
            header = data.keys()
            csv_writer.writerow(header)
            count += 1
    #Save file and create new record
    csv_writer.writerow(data.values())
 
    dataFile.close()
    collection.save()

    #Transform csv file
    cleanCsv('csvFiles/%s' % fileName, fileName)

    return redirect('collectionsList')