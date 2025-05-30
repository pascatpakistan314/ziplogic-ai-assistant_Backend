import json
import os
from datetime import datetime

OUTPUT_DIR = "output"
BLUEPRINT_LOG = os.path.join(OUTPUT_DIR, "blueprints.json")

def save_blueprint(project_id, prompt, response):
    blueprint = {
        "id": project_id,
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "response": response,
    }

    if os.path.exists(BLUEPRINT_LOG):
        with open(BLUEPRINT_LOG, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(blueprint)

    with open(BLUEPRINT_LOG, "w") as f:
        json.dump(data, f, indent=2)













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
from . ai_gemini import call_gemini_api


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
    """
    More robust prompt builder with framework aliases
    """
    # Normalize inputs
    language = data['language'].lower().strip()
    framework = data['framework'].lower().strip()

    # Handle framework name variations
    framework_aliases = {
        'django rest': ['django rest', 'django-rest', 'django rest framework'],
        'flask': ['flask'],
        'fastapi': ['fastapi', 'fast api'],
        'react': ['react', 'react.js'],
        'next.js': ['next.js', 'next']
    }

    # Find matching framework
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
    """
    Comprehensive JSON extractor with multiple fallback strategies
    """

    def try_parse(json_str):
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try fixing common issues
            fixed = json_str
            # Fix trailing commas
            fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
            # Fix unescaped quotes
            fixed = re.sub(r'(?<!\\)"', r'\"', fixed)
            fixed = fixed.replace('\\"', '"')
            # Fix single quotes
            fixed = fixed.replace("'", '"')
            return json.loads(fixed)

    # Strategy 1: Direct parse
    try:
        return try_parse(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Remove markdown code blocks
    clean_text = re.sub(r'```(json)?', '', text, flags=re.IGNORECASE)
    try:
        return try_parse(clean_text)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Extract JSON portion
    start = clean_text.find('{')
    end = clean_text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            return try_parse(clean_text[start:end])
        except json.JSONDecodeError:
            pass

    # Strategy 4: Last resort - manual repair
    try:
        # Add commas between objects
        repaired = re.sub(r'}\s*{', '},{', clean_text[start:end])
        # Ensure proper array formatting
        repaired = re.sub(r'\[\s*{', '[{', repaired)
        repaired = re.sub(r'}\s*]', '}]', repaired)
        return try_parse(repaired)
    except json.JSONDecodeError as e:
        # Save problematic response for debugging
        with open(os.path.join(OUTPUT_DIR, 'json_parse_error.txt'), 'w') as f:
            f.write(f"Original:\n{text}\n\nCleaned:\n{clean_text}\n\nAttempted Parse:\n{clean_text[start:end]}")
        raise Exception(f"Failed to parse JSON after multiple attempts: {str(e)}")


def build_app_zip(data):
    """
    Main application builder with comprehensive error handling
    """
    try:
        # Validate input data
        required_keys = ['type', 'login', 'upload', 'layout', 'app_name',
                         'framework', 'language', 'pages', 'color_scheme']
        if not all(k in data for k in required_keys):
            raise ValueError("Missing required fields in input data")

        # Generate prompt
        prompt = build_prompt_from_data(data)
        logging.info(f"Generated prompt (truncated): {prompt[:200]}...")

        # Call Gemini API
        response_data = call_gemini_api(prompt)

        # Extract generated text
        try:
            generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            logging.error(f"Invalid response structure: {json.dumps(response_data, indent=2)}")
            raise ValueError("Invalid API response structure")

        # Save raw response
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "raw_gemini_output.txt"), "w", encoding="utf-8") as f:
            f.write(generated_text)

        # Parse JSON
        try:
            files = extract_json(generated_text)
        except Exception as e:
            with open(os.path.join(OUTPUT_DIR, "bad_json_response.txt"), "w", encoding="utf-8") as f:
                f.write(generated_text)
            logging.error("JSON parsing failed - saved bad response")
            raise

        # Create project structure
        project_id = str(uuid.uuid4())
        project_path = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(project_path, exist_ok=True)

        # Write files from JSON
        written_files = 0
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
            raise ValueError("No files were generated from the API response")

        # Create zip archive
        zip_base = os.path.join(OUTPUT_DIR, project_id)
        shutil.make_archive(zip_base, 'zip', project_path)

        return f"{project_id}.zip"

    except Exception as e:
        logging.error(f"Error in build_app_zip: {str(e)}", exc_info=True)
        raise


@api_view(['POST'])
def generate_app(request):
    """
    API endpoint with enhanced error handling
    """
    try:
        data = request.data
        zip_filename = build_app_zip(data)

        # Log successful generation
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
