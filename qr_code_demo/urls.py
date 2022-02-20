from django.urls import path, include

from qr_code_demo import views

app_name = "qr_code_demo"
urlpatterns = [
    path("", views.index, name="index"),
    path("qr-code/", include("qr_code.urls", namespace="qr_code")),
]
