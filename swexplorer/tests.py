from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from .views import *
from datetime import datetime
import json
from django.utils.crypto import get_random_string
import csv

# Create your tests here.
class UrlsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def setUpCsv(self):
        jsonData = fetchData()['results']
        self.fileName = get_random_string(20) + ".csv"
        self.file = open('csvFiles/a%s' % self.fileName, 'w')
        count = 0
        csv_writer = csv.writer(self.file)
        for data in jsonData:
            if count == 0:
                header = data.keys()
                csv_writer.writerow(header)
                count += 1
    #Save file and create new record
            csv_writer.writerow(data.values())
        self.file.close()
        self.filePath = 'csvFiles/a%s' % self.fileName

    def cleanUp(self):
        if os.path.exists(self.filePath):
            os.remove(self.filePath)

    def test_data_fetch_data(self):
        response = fetchData()
        try:
            json.loads(response)
            return True
        except:
            return False

    def test_changing_date_format(self):
        dateTime = datetime.now()    
        try:
            date = changeDateFormat(datetime.strftime(dateTime, '%Y-%m-%d%H:%M:%S.%f'))
            datetime.strptime(date, '%Y-%m-%d')
            return True
        except:
            return False


    def test_collection_list_view(self):
        response = self.client.get(reverse('collectionsList'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'collections_list.html')

    def test_fetch_collection_show_10(self):
        self.setUpCsv()
        response = self.client.get(reverse('collectionList', kwargs={'fileName': self.fileName}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'collection_list.html')
        self.cleanUp()

    def test_fetch_collection_show_20(self):
        self.setUpCsv()
        response = self.client.get(reverse('collectionList20', kwargs={'fileName': self.fileName}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'collection_list.html')
        self.cleanUp()
    
    def test_collection_count_view(self):
        self.setUpCsv()
        response = self.client.get(reverse('collectionCount', kwargs={'fileName': self.fileName, 'columns': 'height-name-'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'collection_count_list.html')
        self.cleanUp()