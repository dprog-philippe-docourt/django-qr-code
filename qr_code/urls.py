from django.conf import settings
from django.urls import path

from qr_code import views


app_name = 'qr_code'
urlpatterns = [
    path(getattr(settings, 'SERVE_QR_CODE_IMAGE_PATH', 'images/serve-qr-code-image/'), views.serve_qr_code_image, name='serve_qr_code_image')
]
