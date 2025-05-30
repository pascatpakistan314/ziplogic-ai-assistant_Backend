
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import FileResponse, Http404
from datetime import datetime
import os
import shutil
import uuid
import json
import requests
import re
import logging
from time import sleep
from json.decoder import JSONDecodeError
from .model_selector import call_model
from .ai_gemini import call_gemini_api
from .ai_gpt import call_openai_api
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny


# Setup logging for debugging
logging.basicConfig(
    filename='output/app_generator.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Constants
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_KEY = "AIzaSyCY4d_sqrw8mQwpvg7eQ4g2_tmnUYN1Ias"

OUTPUT_DIR = "output"
PROJECTS_DIR = os.path.join(OUTPUT_DIR, "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)

# PROMPT_MAP remains the same as in your original code
# PROMPT_MAP as in your code, truncated here for brevity
PROMPT_MAP = {
    ("python", "django rest"): """
You are an expert full-stack developer using Django REST and React. Generate a complete production-ready full-stack web application named '{app_name}' with the following:
- Backend: Django REST Framework
- Frontend: React
- Type: {type}
- Features: Login={login}, File Upload={upload}
- Color Scheme: {color_scheme}
- Layout: {layout}

Include all these components:

1. Backend (Django REST):
   - Project structure with config/ and apps/{app_name}/
   - Proper __init__.py files
   - config/settings.py with CORS, database, JWT (if login='yes'), media/static config
   - config/urls.py + api schema and docs
   - Apps: models.py, views.py (class-based views), serializers.py, urls.py, admin.py
   - JWT auth setup if login='yes'
   - Upload endpoint and settings if upload='yes'
   - Logging and error handling
   - API docs via drf-yasg or drf-spectacular
   - .env.example with all variables
   - Dockerfile + docker-compose.yml

2. Frontend (React):
   - src/
     - components/, pages/, services/, hooks/, context/, assets/
     - API service to connect with backend endpoints
     - Auth context/provider if login='yes'
     - Upload form/component if upload='yes'
     - Layout and routing setup (React Router)
     - Styling with {color_scheme}
     - Reusable UI components with responsiveness
     - Loading/Error boundaries

3. Supporting Files:
   - README.md with full setup (backend + frontend), API usage, deployment guide
   - .gitignore, manage.py, package.json, requirements.txt
   - Test cases using pytest (backend) and React Testing Library/Jest (frontend)

Return complete structured JSON output:
{{
  "backend": {{
    "config/settings.py": "...",
    "apps/{app_name}/models.py": "...",
    ...
  }},
  "frontend": {{
    "src/App.js": "...",
    "src/components/Navbar.jsx": "...",
    ...
  }},
  "documentation": {{
    "setup_instructions": "...",
    "api_endpoints": [...],
    "frontend_structure": "..."
  }}
}}
""",

    ("python", "flask"): """
You are an expert full-stack developer using Flask and React. Build a complete production-grade application named '{app_name}' with:
- Backend: Flask (modular pattern)
- Frontend: React
- Type: {type}
- Features: Login={login}, Upload={upload}
- Color Scheme: {color_scheme}
- Layout: {layout}

1. Backend (Flask):
   - Modular structure with app/
     - __init__.py (factory), config.py, extensions.py
     - models.py, routes/, auth/, uploads/
   - Blueprints for modular routing
   - Flask-JWT-Extended if login='yes'
   - Upload handling if upload='yes'
   - SQLAlchemy + Alembic for DB
   - Error handling, logging
   - .env.example
   - Dockerfile, docker-compose.yml

2. Frontend (React):
   - React with routing, layout, pages
   - Auth context/provider if login='yes'
   - Upload UI if upload='yes'
   - API integration using Axios
   - Color theme with {color_scheme}
   - Responsive layout based on {layout}

3. Documentation:
   - README.md with Flask+React setup
   - requirements.txt, package.json
   - Jest/pytest tests
   - Git ignore files

Return JSON output:
{{
  "backend": {{ "app/__init__.py": "...", ... }},
  "frontend": {{ "src/App.js": "...", ... }},
  "documentation": {{ "setup": "...", "api_routes": [...], "structure": "..." }}
}}
""",

    ("python", "fastapi"): """
You are a FastAPI + React expert. Create a full-stack application named '{app_name}' using:
- Backend: FastAPI (async SQLAlchemy + Pydantic)
- Frontend: React
- Type: {type}
- Features: Login={login}, Upload={upload}
- Theme: {color_scheme}
- Layout: {layout}

1. Backend:
   - main.py, app/ with models.py, schemas.py, routers/, auth.py, upload.py
   - DB: SQLAlchemy async + Alembic
   - JWT with FastAPI Users or custom if login='yes'
   - Upload endpoints if upload='yes'
   - CORS, error handlers
   - OpenAPI docs
   - Docker, .env.example

2. Frontend (React):
   - src/ with pages, components, API services
   - Login flow if login='yes'
   - Upload form if upload='yes'
   - Theme using {color_scheme}
   - Layout structure based on {layout}

3. Extras:
   - README.md with backend/frontend setup
   - requirements.txt, package.json
   - Sample tests with Pytest + React Testing Library

JSON Output:
{{
  "backend": {{ "main.py": "...", ... }},
  "frontend": {{ "src/App.js": "...", ... }},
  "documentation": {{ "api_docs": "...", "setup": "...", "structure": "..." }}
}}
""",

    ("javascript", "react"): """
You are a React expert. Create a complete React application named '{app_name}' with:
- Type: {type}
- Features: Login={login}, Upload={upload}
- Color Theme: {color_scheme}
- Layout: {layout}

Include:
1. src/
   - components/, pages/, services/, hooks/, context/, assets/
   - React Router setup
   - Auth flow (if login='yes')
   - Upload component (if upload='yes')
   - Themed components with {color_scheme}
   - Layout matching {layout}
   - Responsive design

2. Other files:
   - package.json, .env.example, README.md
   - Error boundaries, loading states
   - Testing config if needed

JSON Output:
{{
  "frontend": {{ "src/App.js": "...", ... }},
  "documentation": {{ "structure": "...", "features": "..." }}
}}
""",

    ("typescript", "next.js"): """
You are a Next.js + TypeScript + React expert. Generate a full-stack production-ready app named '{app_name}' with:
- Framework: Next.js (App Router or Pages), TypeScript
- Type: {type}
- Features: Login={login}, Upload={upload}
- Styling: {color_scheme}
- Layout: {layout}

Include:

1. Frontend:
   - pages/ or app/, components/, lib/, context/, services/, types/
   - Auth flow using JWT or NextAuth if login='yes'
   - Upload feature if upload='yes'
   - Responsive layout with {layout}
   - Theme and style matching {color_scheme}
   - Static assets, SEO config

2. Backend (API Routes):
   - API endpoints (for auth, file upload, DB access)
   - DB with Prisma or direct SQL
   - Middleware, error handlers

3. Supporting:
   - next.config.js, tsconfig.json
   - package.json, .env.local.example
   - README.md, Jest tests

Return JSON:
{{
  "frontend": {{ "pages/index.tsx": "...", ... }},
  "api": {{ "pages/api/auth/login.ts": "...", ... }},
  "documentation": {{ "setup": "...", "api": [...], "frontend_structure": "..." }}
}}
"""
}





def build_prompt_from_data(data):
    language = data['language'].lower().strip()
    framework = data['framework'].lower().strip()

    framework_aliases = {
        'django rest': ['django rest', 'django-rest', 'django rest framework'],
        'flask': ['flask'],
        'fastapi': ['fastapi', 'fast api'],
        'react': ['react', 'react.js'],
        'next.js': ['next.js', 'next']
    }

    matched_framework = None
    for key, aliases in framework_aliases.items():
        if framework in aliases:
            matched_framework = key
            break

    if not matched_framework:
        available = [k for k in framework_aliases.keys()]
        raise Exception(f"Unsupported framework. Available options: {available}")

    key = (language, matched_framework)
    base_prompt = PROMPT_MAP.get(key)

    if not base_prompt:
        raise Exception(f"Unsupported language/framework combination: {key}")

    return base_prompt.format(**data)


def extract_json(text):
    # Remove markdown code blocks if any remain
    text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()

    start = text.find('{')
    end = text.rfind('}') + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in text")

    candidate = text[start:end]

    # Remove trailing commas before } or ]
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        # Save error for debugging
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "json_parse_error.txt"), "w", encoding="utf-8") as f:
            f.write(candidate)
        raise e

def build_app_zip(data):
    try:
        required_keys = ['type', 'login', 'upload', 'layout', 'app_name',
                         'framework', 'language', 'pages', 'color_scheme']
        if not all(k in data for k in required_keys):
            missing = [k for k in required_keys if k not in data]
            raise ValueError(f"Missing required fields: {missing}")

        prompt = build_prompt_from_data(data)
        logging.info(f"Prompt generated (start): {prompt[:200]}...")

        response_text = call_openai_api(prompt)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "raw_openai_output.txt"), "w", encoding="utf-8") as f:
            f.write(response_text)

        files = extract_json(response_text)

        project_id = str(uuid.uuid4())
        project_path = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(project_path, exist_ok=True)

        written_files = 0

        framework = data.get('framework', '').lower()

        if framework == 'flask':
            # Flask specific file writing logic with safer checks
            for section in ["frontend", "backend", "documentation", "api"]:
                if section in files:
                    section_path = os.path.join(project_path, section)
                    os.makedirs(section_path, exist_ok=True)
                    for filename, content in files[section].items():
                        filepath = os.path.join(section_path, filename)

                        # Skip directory-like entries for Flask too
                        if filename.endswith('/') or filename.endswith('\\'):
                            logging.warning(f"Flask: Skipping directory entry: {filename}")
                            continue
                        if os.path.isdir(filepath):
                            logging.warning(f"Flask: Skipping write to directory path: {filepath}")
                            continue

                        os.makedirs(os.path.dirname(filepath), exist_ok=True)

                        if not isinstance(content, str):
                            content = json.dumps(content, indent=2)

                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        written_files += 1

        else:
            # Default handling for other frameworks (Django REST, FastAPI, etc.)
            for section in ["frontend", "backend", "documentation", "api"]:
                if section in files:
                    section_path = os.path.join(project_path, section)
                    os.makedirs(section_path, exist_ok=True)
                    for filename, content in files[section].items():
                        filepath = os.path.join(section_path, filename)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        if not isinstance(content, str):
                            content = json.dumps(content, indent=2)
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        written_files += 1

        if written_files == 0:
            raise ValueError("No files generated from the API response")

        zip_base = os.path.join(OUTPUT_DIR, project_id)
        shutil.make_archive(zip_base, 'zip', project_path)

        return f"{project_id}.zip"

    except Exception as e:
        logging.error(f"Error in build_app_zip: {str(e)}", exc_info=True)
        raise


@api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def open_generate_app(request):
    try:
        data = request.data
        zip_filename = build_app_zip(data)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "download_log.txt"), "a", encoding="utf-8") as log:
            log.write(f"{datetime.now()} | Built ZIP: {zip_filename}\n")

        return Response({
            "status": "success",
            "zip_path": zip_filename,
            "download_url": f"/download/{zip_filename}"
        })

    except Exception as e:
        logging.error(f"Error in generate_app: {str(e)}", exc_info=True)
        return Response({
            "error": str(e),
            "details": "See server logs for more information"
        }, status=500)

@api_view(['GET'])
def download_zip(request, filename):
    """
    Secure file download endpoint
    """
    if not re.match(r'^[a-f0-9\-]+\.zip$', filename):
        raise Http404("Invalid filename")

    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(
            open(filepath, 'rb'),
            as_attachment=True,
            filename=f"generated_app_{filename}"
        )
    raise Http404("File not found")


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

@csrf_exempt
def preview_file(request, project_id, section, filename):
    filepath = os.path.join("output", "projects", str(project_id), section, filename)

    if not os.path.exists(filepath):
        return JsonResponse({"error": "File not found"}, status=404)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return JsonResponse({"filename": filename, "content": content})

@api_view(['GET'])
def download_zip(request, filename):
    """
    Secure file download endpoint
    """
    if not re.match(r'^[a-f0-9\-]+\.zip$', filename):
        raise Http404("Invalid filename")

    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(
            open(filepath, 'rb'),
            as_attachment=True,
            filename=f"generated_app_{filename}"
        )
    raise Http404("File not found")


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

@csrf_exempt
def preview_file(request, project_id, section, filename):
    filepath = os.path.join("output", "projects", str(project_id), section, filename)

    if not os.path.exists(filepath):
        return JsonResponse({"error": "File not found"}, status=404)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return JsonResponse({"filename": filename, "content": content})
