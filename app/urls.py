from django.urls import path
from app.views import generate_app,download_zip
from .views import preview_file
from .gemini import gemini_generate_app
from .open_ai import open_generate_app
urlpatterns = [
    path("open_generate_app/", open_generate_app , name="generate-app"),
    path("gemini-geneate-app/", gemini_generate_app, name="gemini-geneate-app"),
    path('download/<str:filename>/', download_zip),
    path("preview/<uuid:project_id>/<str:section>/<str:filename>/", preview_file),
]
