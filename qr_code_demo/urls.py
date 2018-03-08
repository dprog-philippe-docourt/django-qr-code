from django.conf.urls import url

from qr_code_demo import views

app_name = "qr_code_demo"
urlpatterns = [
    url(r'^$', views.index, name='index')
]
