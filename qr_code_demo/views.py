from django.shortcuts import render


def index(request):
    return render(request, 'qr_code_demo/index.html')
