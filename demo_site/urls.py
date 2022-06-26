from django.conf.urls import include
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="qr-code-demo/", permanent=True)),
    path("qr-code-demo/", include("qr_code_demo.urls", namespace="qr_code_demo")),
    path("qr-code/", include("qr_code.urls", namespace="qr_code")),
]
