
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
import json5
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
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"

def call_groq_api(prompt):
    # Make the request to the GROQ API
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Define the model you want to use (e.g., GPT-3.5 or GPT-4)
    model = "llama3-70b-8192" # You can change this to "gpt-4" or any other available model

    # Build the request payload with the model
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Error in API call: {response.status_code}, {response.text}")

    # Log the raw response for inspection
    logging.info(f"API Response: {response.text[:500]}...")  # Log first 500 characters for brevity
    return response.text

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
    # Try multiple methods to extract JSON
    patterns = [
        r'```json\n(.*?)\n```',  # Markdown with json specified
        r'```(.*?)```',  # Generic markdown code block
        r'({.*})',  # Raw JSON
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
            try:
                # Remove trailing commas
                candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    # If no pattern matched, try extracting the outermost braces
    start = text.find('{')
    end = text.rfind('}') + 1
    if start >= 0 and end > 0:
        candidate = text[start:end]
        try:
            candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from response")


def build_app_zip(data):
    try:
        required_keys = ['type', 'login', 'upload', 'layout', 'app_name',
                         'framework', 'language', 'pages', 'color_scheme']
        if not all(k in data for k in required_keys):
            raise ValueError("Missing required fields in input data")

        prompt = build_prompt_from_data(data)
        logging.info(f"Generated prompt (truncated): {prompt[:200]}...")

        # Call the API to get the response text
        response_text = call_groq_api(prompt)
        logging.info(f"Raw API response (first 500 chars): {response_text[:500]}")

        # Save the raw response
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        raw_output_path = os.path.join(OUTPUT_DIR, "raw_groq_output.txt")
        with open(raw_output_path, "w", encoding="utf-8") as f:
            f.write(response_text)
        logging.info(f"Saved raw response to {raw_output_path}")

        # Try extracting JSON
        try:
            files = extract_json(response_text)
            logging.info(f"Successfully extracted JSON structure with keys: {files.keys()}")
        except Exception as e:
            error_path = os.path.join(OUTPUT_DIR, "bad_json_response.txt")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(response_text)
            logging.error(f"JSON parsing failed - saved bad response to {error_path}")
            raise ValueError(f"Failed to parse API response as JSON: {str(e)}")

        # Validate the extracted structure
        if not isinstance(files, dict) or not any(
                section in files for section in ["frontend", "backend", "documentation", "api"]):
            logging.error(f"Invalid file structure received: {files}")
            raise ValueError("API response did not contain expected file sections")

        # Create project directory
        project_id = str(uuid.uuid4())
        project_path = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(project_path, exist_ok=True)

        # Write files
        written_files = 0
        for section in ["frontend", "backend", "documentation", "api"]:
            if section in files and files[section]:
                section_path = os.path.join(project_path, section)
                os.makedirs(section_path, exist_ok=True)

                for filename, content in files[section].items():
                    if not content:  # Skip empty files
                        continue

                    filepath = os.path.join(section_path, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)

                    if not isinstance(content, str):
                        content = json.dumps(content, indent=2)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    written_files += 1
                    logging.info(f"Wrote file: {filepath}")

        if written_files == 0:
            raise ValueError("No files were generated from the API response - all sections were empty")

        # Create zip
        zip_base = os.path.join(OUTPUT_DIR, project_id)
        shutil.make_archive(zip_base, 'zip', project_path)
        logging.info(f"Created zip archive at {zip_base}.zip")

        return f"{project_id}.zip"

    except Exception as e:
        logging.error(f"Error in build_app_zip: {str(e)}", exc_info=True)
        raise

@api_view(['POST'])
def generate_app(request):
    try:
        data = request.data
        zip_filename = build_app_zip(data)

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
@permission_classes([AllowAny])
def download_zip(request, filename):
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
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def preview_file(request, project_id, section, filename):
    filepath = os.path.join("output", "projects", str(project_id), section, filename)

    if not os.path.exists(filepath):
        return JsonResponse({"error": "File not found"}, status=404)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return JsonResponse({"filename": filename, "content": content})