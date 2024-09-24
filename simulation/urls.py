from django.urls import path

from .import views


urlpatterns = [
  path('', views.DashboardView.as_view(), name='dashboard'),
  path('about', views.AboutView.as_view(), name='about'),
  path('update-dashboard/', views.update_dashboard, name='update_dashboard'),
]
