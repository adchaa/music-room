from django.urls import path,re_path
from . import views
from . import consumers

urlpatterns = [
    path("login", views.login_view, name="login"),
    path("signup", views.signup_view, name="signup"),
    path('logout', views.logout_view, name='logout'),
    path('',views.home,name="home"),
    path('create-or-join/', views.create_or_join_room, name='create_or_join_room'),
    path('random-room/', views.create_or_join_room, name='random_room'),
    path('room/<int:room_id>/', views.music_room_detail, name='music_room_detail'),
    path('room/<int:room_id>/skip/', views.skip_room, name='skip_room'),
    path('room/delete/<int:room_id>/', views.delete_room, name='delete_room'),

]