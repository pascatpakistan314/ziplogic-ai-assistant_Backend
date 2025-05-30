import os, shutil, zipfile
from datetime import datetime
from slugify import slugify

def build_app_zip(blueprint):
    app_name = slugify(blueprint.get("app_name", "myapp"))
    login = blueprint.get("login", False)
    upload = blueprint.get("upload", False)
    layout = blueprint.get("layout", "single")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"output/{app_name}_{timestamp}"
    os.makedirs(base_path, exist_ok=True)

    backend_dir = os.path.join(base_path, "backend")
    os.makedirs(backend_dir, exist_ok=True)
    views_code = f"# App: {app_name}\n\ndef index(request):\n    return 'Hello from {app_name}'\n"

    if login:
        views_code += "\n# Login handler\ndef login_view(request):\n    return 'Login placeholder'\n"

    if upload:
        views_code += "\n# Upload handler\ndef upload_file(request):\n    return 'Upload placeholder'\n"

    with open(os.path.join(backend_dir, "views.py"), "w") as f:
        f.write(views_code)
    frontend_dir = os.path.join(base_path, "frontend")
    os.makedirs(frontend_dir, exist_ok=True)
    layout_note = f"// Layout type: {layout}\n"
    layout_note += f"export default function App() {{ return <div>{app_name} - {blueprint['type']}</div>; }}"

    with open(os.path.join(frontend_dir, "App.jsx"), "w") as f:
        f.write(layout_note)

    # ZIP folder
    zip_name = f"{app_name}_{timestamp}.zip"
    zip_path = os.path.join("output", zip_name)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for folder, _, files in os.walk(base_path):
            for file in files:
                full_path = os.path.join(folder, file)
                rel_path = os.path.relpath(full_path, base_path)
                zipf.write(full_path, rel_path)

    # Clean up original folder
    shutil.rmtree(base_path)

    return f"/output/{zip_name}"
