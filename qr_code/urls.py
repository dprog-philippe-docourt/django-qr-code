from django.conf.urls import url

from qr_code import views

urlpatterns = [
    url(r'^images/serve_qr_code_image/$', views.serve_qr_code_image, name='serve_qr_code_image')
]
