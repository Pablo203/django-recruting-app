from django.urls import path
from .views import CollectionsListView, fetchCollection

urlpatterns = [
    path('', CollectionsListView.as_view(), name='collectionsList'),
    path('fetchCollection/', fetchCollection, name="fetchCollection")
]