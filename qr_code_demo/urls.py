from django.conf.urls import url

from qr_code_demo import views

urlpatterns = [
    url(r'^$', views.index, name='index')
]
