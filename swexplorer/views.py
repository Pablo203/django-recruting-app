from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.crypto import get_random_string
import string
from django.views.generic import ListView
from .models import Collection
import requests
import csv

# Create your views here.
class CollectionsListView(ListView):
    model = Collection

    queryset = Collection.objects.all()[:10]

    template_name = "collections_list.html"



def fetchData():
  r = requests.get('https://swapi.dev/api/people')
  # Export the data for use in future steps
  return r.json()

def fetchCollection(request):
    jsonData = fetchData()['results']
    fileName = get_random_string(20) + ".csv"
    dataFile = open('csvFiles/%s' % fileName, 'w')
    collection = Collection(
        filePath = 'csvFiles/%s' % fileName,
        fileName = fileName
    )
    csv_writer = csv.writer(dataFile)
    count = 0

    for data in jsonData:
        if count == 0:
            header = data.keys()
            csv_writer.writerow(header)
            count += 1
    csv_writer.writerow(data.values())
 
    dataFile.close()
    collection.save()

    return redirect('collectionsList')