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


class CollectionCountListView(ListView):
    model = Collection

    context_object_name = 'collection'

    template_name = 'collection_count_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = self.kwargs['columns']
        context['fileName'] = self.kwargs['fileName']
        context['csvFile'] = etl.fromcsv('csvFiles/a' + self.kwargs['fileName'])
        context['csvHeaders'] = etl.rowslice(context['csvFile'], 0)

        if self.kwargs['columns'] != '0':
            columns = self.kwargs['columns'].split("-")
            columns.pop()

            table1 = etl.cut(context['csvFile'], columns)
            context['csvContent'] = etl.rowslice(table1, 0)
            headers = table1.header()

            #Prepare field to count combinations, using joined fields values
            counterTable = etl.addfield(table1, 'counterField', lambda row: ','.join(f"{row[name]}" for name in headers))
            #Count combinations using earlier prepared field
            countedCombinations = etl.valuecounter(counterTable, 'counterField')

            #Remove duplicates from table to prepare data for showing on website
            counterTableNoDup = etl.mergeduplicates(counterTable, 'counterField')
            #Move table with counted values to the end
            counterTableNoDup = etl.movefield(counterTableNoDup, 'counterField', len(headers))
            #Replace field with combined values from all fields with counted values number
            counterTableNoDup = etl.convert(counterTableNoDup, 'counterField', lambda row: countedCombinations[row])

            context['csvCount'] = counterTableNoDup

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
    table2 = etl.cutout(table1, 'films', 'species', 'vehicles', 'starships', 'created', 'url')
    table3 = etl.addfield(table2, 'date', lambda row: row['edited'])
    table4 = etl.convert(table3, 'date', lambda row: changeDateFormat(row))
    table5 = etl.cutout(table4, 'edited')
    table6 = etl.convert(table5, 'homeworld', lambda row: requests.get(row).json()['name'])
    
    etl.tocsv(table6, ("csvFiles/a" + fileName))
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