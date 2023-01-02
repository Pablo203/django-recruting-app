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

    #Get all datasets and order by date - show latest dataset on top
    queryset = Collection.objects.all().order_by('-date')

    template_name = "collections_list.html"

class CollectionListView(ListView):
    model = Collection

    context_object_name = 'collection'

    template_name = 'collection_list.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fileName'] = self.kwargs['fileName']
        context['csvFileContent'] = etl.fromcsv('csvFiles/a' + self.kwargs['fileName'])
        #Limit displayed data to first 10 rows
        context['csvFileContent'] = etl.rowslice(context['csvFileContent'], 10)
        return context

class CollectionListViewShowMore(CollectionListView, ListView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fileName'] = self.kwargs['fileName']
        context['csvFileContent'] = etl.fromcsv('csvFiles/a' + self.kwargs['fileName'])
        #Extend displayed data to 20 rows
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
        #Get headers for display
        context['csvHeaders'] = etl.rowslice(context['csvFile'], 0)

        if self.kwargs['columns'] != '0':
            #Clear string with column names and turn it into list
            columns = self.kwargs['columns'].split("-")
            #Remove last element which is whitespace
            columns.pop()

            #Cut all columns except chosen to show
            table1 = etl.cut(context['csvFile'], columns)
            #Get headers for display
            context['csvContent'] = etl.rowslice(table1, 0)
            #Get names of columns
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
        #Check string for uppercase letters that pollutes date string
        if char in ascii_uppercase:
            dateStr = dateStr.replace(char, '')
    #Cast string to datetime object
    dateStr = datetime.strptime(dateStr, '%Y-%m-%d%H:%M:%S.%f')
    #Change datetime object to date
    dateStr = dateStr.date()
    return dateStr

def cleanCsv(filePath, fileName):
    #Open csv file
    table1 = etl.fromcsv(filePath)
    #Remove unneccessary columns
    table2 = etl.cutout(table1, 'films', 'species', 'vehicles', 'starships', 'created', 'url')
    #Add new field based from another column
    table3 = etl.addfield(table2, 'date', lambda row: row['edited'])
    #Modify column to show wanted date format
    table4 = etl.convert(table3, 'date', lambda row: changeDateFormat(row))
    #Remove used column
    table5 = etl.cutout(table4, 'edited')
    #Resolve all planets for limiting requests numbers
    table6 = etl.convert(table5, 'homeworld', lambda row: requests.get(row).json()['name'])
    
    #To evade error remove old csv file and save new one
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
    
    #Save file and created record
    dataFile.close()
    collection.save()

    #Transform csv file
    cleanCsv('csvFiles/%s' % fileName, fileName)

    return redirect('collectionsList')