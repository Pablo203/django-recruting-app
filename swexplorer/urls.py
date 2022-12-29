from django.urls import path
from .views import CollectionsListView, fetchCollection, CollectionListView, CollectionListViewShowMore

urlpatterns = [
    path('', CollectionsListView.as_view(), name='collectionsList'),
    path('fetchCollection/', fetchCollection, name="fetchCollection"),
    path('<str:fileName>/10/', CollectionListView.as_view(), name='collectionList'),
    path('<str:fileName>/20/', CollectionListViewShowMore.as_view(), name='collectionList20'),
]