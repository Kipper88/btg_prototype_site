from django.urls import path
from .views import Entity, Login, Logout

urlpatterns = [
    path('', Entity.IndexView.as_view(), name='index'),
    path('entity/create-group/', Entity.CreateGroup.as_view(), name='create_group'),
    path('entity/create-entity/', Entity.CreateEntity.as_view(), name='create_entity'),
    path('entity/get-entity/', Entity.GetEntityOne.as_view(), name='get_entity'),
    path('entity/manage/', Entity.Manage.as_view(), name='manage'),
    path('entity/settings/', Entity.Settings.as_view(), name='settings'),
    path('entity/settings-entity/', Entity.SettingsEntity.as_view(), name='settings_entity'),
    path('entity/add-record/', Entity.AddRecord.as_view(), name='add_entity_record'),
    
    path('login/', Login.as_view(), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
]