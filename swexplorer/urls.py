from django.urls import path
from .views import CollectionsListView, fetchCollection, CollectionListView

urlpatterns = [
    path('', CollectionsListView.as_view(), name='collectionsList'),
    path('fetchCollection/', fetchCollection, name="fetchCollection"),
    path('<str:fileName>/10/', CollectionListView.as_view(), name='collectionList'),
]