from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.analyzer.parser import get_python_files, analyze_python_file
from backend.analyzer.ai_analyzer import analyze_patch
from backend.analyzer.pdf_report import generate_pdf_report

import os
import zipfile
import shutil


app = FastAPI()

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = "uploads"
REPORT_FOLDER = "reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "AI Security Patch Impact Analyzer is running!"
    }


# ============================================================
# UPLOAD OLD PROJECT
# ============================================================

@app.post("/upload")
async def upload_zip(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".zip"):
        return {
            "error": "Please upload a ZIP file only."
        }

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    # Save ZIP
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Folder name without .zip
    project_name = file.filename[:-4]

    extract_folder = os.path.join(
        UPLOAD_FOLDER,
        project_name
    )

    # Remove old folder if it already exists
    if os.path.exists(extract_folder):
        shutil.rmtree(extract_folder)

    os.makedirs(extract_folder, exist_ok=True)

    # Extract ZIP
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_folder)

    return {
        "message": "Old project uploaded and extracted successfully!",
        "zip_file": file.filename,
        "saved_location": file_path,
        "extracted_to": extract_folder
    }


# ============================================================
# UPLOAD PATCHED PROJECT
# ============================================================

@app.post("/upload-patch")
async def upload_patch(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".zip"):
        return {
            "error": "Please upload a ZIP file only."
        }

    # Save patched ZIP
    file_path = os.path.join(
        UPLOAD_FOLDER,
        "patched_" + file.filename
    )

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Always use this folder for patched project
    extract_folder = os.path.join(
        UPLOAD_FOLDER,
        "PatchedProject"
    )

    # Remove previous patched project
    if os.path.exists(extract_folder):
        shutil.rmtree(extract_folder)

    os.makedirs(extract_folder, exist_ok=True)

    # Extract patched ZIP
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_folder)

    return {
        "message": "Patched project uploaded and extracted successfully!",
        "zip_file": file.filename,
        "saved_location": file_path,
        "extracted_to": extract_folder
    }


# ============================================================
# FIND OLD PROJECT
# ============================================================

def get_old_project():

    sample_project = os.path.join(
        UPLOAD_FOLDER,
        "SampleProject"
    )

    if os.path.isdir(sample_project):
        return sample_project

    return None


# ============================================================
# FIND PATCHED PROJECT
# ============================================================

def get_patched_project():

    patched_project = os.path.join(
        UPLOAD_FOLDER,
        "PatchedProject"
    )

    if os.path.isdir(patched_project):
        return patched_project

    return None


# ============================================================
# LIST OLD PROJECT PYTHON FILES
# ============================================================

@app.get("/python-files")
def list_python_files():

    project = get_old_project()

    if project is None:
        return {
            "error": "No old project uploaded."
        }

    python_files = get_python_files(project)

    return {
        "project_folder": project,
        "python_files": python_files
    }


# ============================================================
# ANALYZE OLD PROJECT
# ============================================================

@app.get("/analyze")
def analyze_project():

    project = get_old_project()

    if project is None:
        return {
            "error": "No old project uploaded."
        }

    python_files = get_python_files(project)

    result = {}

    for file in python_files:
        result[file] = analyze_python_file(file)

    return result


# ============================================================
# LIST PATCHED PROJECT PYTHON FILES
# ============================================================

@app.get("/patch-python-files")
def list_patch_python_files():

    project = get_patched_project()

    if project is None:
        return {
            "error": "No patched project uploaded."
        }

    python_files = get_python_files(project)

    return {
        "project_folder": project,
        "python_files": python_files
    }


# ============================================================
# ANALYZE PATCHED PROJECT
# ============================================================

@app.get("/analyze-patch")
def analyze_patch_project():

    project = get_patched_project()

    if project is None:
        return {
            "error": "No patched project uploaded."
        }

    python_files = get_python_files(project)

    result = {}

    for file in python_files:
        result[file] = analyze_python_file(file)

    return result


# ============================================================
# COMPARE OLD AND PATCHED PROJECTS
# ============================================================

@app.get("/compare")
def compare_projects():

    old_project = get_old_project()
    patched_project = get_patched_project()

    # Check old project
    if old_project is None:
        return {
            "error": "No old project uploaded."
        }

    # Check patched project
    if patched_project is None:
        return {
            "error": "No patched project uploaded."
        }

    # Get Python files
    old_files = get_python_files(old_project)
    patched_files = get_python_files(patched_project)

    # Convert paths into relative paths
    old_file_map = {}

    for file in old_files:

        relative_path = os.path.relpath(
            file,
            old_project
        )

        old_file_map[relative_path] = file

    patched_file_map = {}

    for file in patched_files:

        relative_path = os.path.relpath(
            file,
            patched_project
        )

        patched_file_map[relative_path] = file

    # All Python files
    all_files = (
        set(old_file_map.keys())
        | set(patched_file_map.keys())
    )

    added_functions = []
    removed_functions = []
    modified_functions = []

    for relative_file in sorted(all_files):

        # ----------------------------------------------------
        # File added
        # ----------------------------------------------------

        if relative_file not in old_file_map:

            patched_analysis = analyze_python_file(
                patched_file_map[relative_file]
            )

            for function in patched_analysis["functions"]:

                added_functions.append({
                    "file": relative_file,
                    "function": function
                })

            continue

        # ----------------------------------------------------
        # File removed
        # ----------------------------------------------------

        if relative_file not in patched_file_map:

            old_analysis = analyze_python_file(
                old_file_map[relative_file]
            )

            for function in old_analysis["functions"]:

                removed_functions.append({
                    "file": relative_file,
                    "function": function
                })

            continue

        # ----------------------------------------------------
        # File exists in both versions
        # ----------------------------------------------------

        old_analysis = analyze_python_file(
            old_file_map[relative_file]
        )

        patched_analysis = analyze_python_file(
            patched_file_map[relative_file]
        )

        old_functions = set(
            old_analysis["functions"]
        )

        patched_functions = set(
            patched_analysis["functions"]
        )

        # Added functions
        for function in sorted(
            patched_functions - old_functions
        ):

            added_functions.append({
                "file": relative_file,
                "function": function
            })

        # Removed functions
        for function in sorted(
            old_functions - patched_functions
        ):

            removed_functions.append({
                "file": relative_file,
                "function": function
            })

        # ----------------------------------------------------
        # Modified functions
        # ----------------------------------------------------

        common_functions = (
            old_functions & patched_functions
        )

        for function in sorted(common_functions):

            old_dependencies = old_analysis[
                "dependencies"
            ].get(function, [])

            patched_dependencies = patched_analysis[
                "dependencies"
            ].get(function, [])

            if old_dependencies != patched_dependencies:

                modified_functions.append({
                    "file": relative_file,
                    "function": function
                })

    return {
        "old_project": old_project,
        "patched_project": patched_project,
        "added_functions": added_functions,
        "removed_functions": removed_functions,
        "modified_functions": modified_functions
    }


# ============================================================
# AI PATCH ANALYSIS - MILESTONE 5
# ============================================================

@app.get("/ai-analysis")
def ai_analysis():

    old_project = get_old_project()
    patched_project = get_patched_project()

    # Check old project
    if old_project is None:
        return {
            "error": "No old project uploaded."
        }

    if patched_project is None:
        return {
            "error": "No patched project uploaded."
        }

    # --------------------------------------------------------
    # Get files
    # --------------------------------------------------------

    old_files = get_python_files(old_project)
    patched_files = get_python_files(patched_project)

    # --------------------------------------------------------
    # Analyze old project
    # --------------------------------------------------------

    old_analysis = {}

    for file in old_files:
        old_analysis[file] = analyze_python_file(file)

    # --------------------------------------------------------
    # Analyze patched project
    # --------------------------------------------------------

    patched_analysis = {}

    for file in patched_files:
        patched_analysis[file] = analyze_python_file(file)

    # --------------------------------------------------------
    # Create file maps
    # --------------------------------------------------------

    old_file_map = {}

    for file, analysis in old_analysis.items():

        relative_path = os.path.relpath(
            file,
            old_project
        )

        old_file_map[relative_path] = analysis

    patched_file_map = {}

    for file, analysis in patched_analysis.items():

        relative_path = os.path.relpath(
            file,
            patched_project
        )

        patched_file_map[relative_path] = analysis

    # --------------------------------------------------------
    # Detect changed functions
    # --------------------------------------------------------

    added_functions = []
    removed_functions = []
    modified_functions = []

    all_files = (
        set(old_file_map.keys())
        | set(patched_file_map.keys())
    )

    for relative_file in sorted(all_files):

        # File added
        if relative_file not in old_file_map:

            new_analysis = patched_file_map[relative_file]

            for function in new_analysis["functions"]:

                added_functions.append({
                    "file": relative_file,
                    "function": function
                })

            continue

        # File removed
        if relative_file not in patched_file_map:

            old_analysis_data = old_file_map[relative_file]

            for function in old_analysis_data["functions"]:

                removed_functions.append({
                    "file": relative_file,
                    "function": function
                })

            continue

        old_data = old_file_map[relative_file]
        new_data = patched_file_map[relative_file]

        old_functions = set(
            old_data["functions"]
        )

        new_functions = set(
            new_data["functions"]
        )

        # Added
        for function in sorted(
            new_functions - old_functions
        ):

            added_functions.append({
                "file": relative_file,
                "function": function
            })

        # Removed
        for function in sorted(
            old_functions - new_functions
        ):

            removed_functions.append({
                "file": relative_file,
                "function": function
            })

        # Modified
        common_functions = (
            old_functions & new_functions
        )

        for function in sorted(common_functions):

            old_dependencies = old_data[
                "dependencies"
            ].get(function, [])

            new_dependencies = new_data[
                "dependencies"
            ].get(function, [])

            if old_dependencies != new_dependencies:

                modified_functions.append({
                    "file": relative_file,
                    "function": function
                })

    # --------------------------------------------------------
    # Prepare changed functions
    # --------------------------------------------------------

    changed_functions = {
        "added_functions": added_functions,
        "removed_functions": removed_functions,
        "modified_functions": modified_functions
    }

    # --------------------------------------------------------
    # Build dependency map
    # --------------------------------------------------------

    dependency_map = {}

    for relative_file, analysis in patched_file_map.items():

        dependency_map[relative_file] = analysis.get(
            "dependencies",
            {}
        )

    # --------------------------------------------------------
    # Send data to AI
    # --------------------------------------------------------

    ai_result = analyze_patch(
        changed_functions,
        dependency_map
    )

    # --------------------------------------------------------
    # Return complete result
    # --------------------------------------------------------

    return {
        "changed_functions": changed_functions,
        "dependency_map": dependency_map,
        "ai_analysis": ai_result
    }


# ============================================================
# GENERATE PDF REPORT - MILESTONE 6
# ============================================================

@app.get("/generate-report")
def generate_report():

    # --------------------------------------------------------
    # Run existing AI analysis
    # --------------------------------------------------------

    analysis_result = ai_analysis()

    # If there is an error, return it
    if "error" in analysis_result:

        return analysis_result

    # --------------------------------------------------------
    # Get changed functions
    # --------------------------------------------------------

    changed_functions = analysis_result[
        "changed_functions"
    ]

    # --------------------------------------------------------
    # Get dependency map
    # --------------------------------------------------------

    dependency_map = analysis_result[
        "dependency_map"
    ]

    # --------------------------------------------------------
    # Get AI analysis
    # --------------------------------------------------------

    ai_result = analysis_result[
        "ai_analysis"
    ]

    # --------------------------------------------------------
    # Create list of changed files
    # --------------------------------------------------------

    changed_files = set()

    for item in changed_functions[
        "added_functions"
    ]:

        changed_files.add(
            item["file"]
        )

    for item in changed_functions[
        "removed_functions"
    ]:

        changed_files.add(
            item["file"]
        )

    for item in changed_functions[
        "modified_functions"
    ]:

        changed_files.add(
            item["file"]
        )

    # --------------------------------------------------------
    # Convert set into dictionary
    # --------------------------------------------------------

    changed_files_dict = {}

    for file_name in sorted(changed_files):

        changed_files_dict[file_name] = "Changed"

    # --------------------------------------------------------
    # PDF OUTPUT PATH
    # --------------------------------------------------------

    pdf_path = os.path.join(
        REPORT_FOLDER,
        "security_patch_report.pdf"
    )

    # --------------------------------------------------------
    # Generate PDF
    # --------------------------------------------------------

    generate_pdf_report(
        project_name="AI-Security-Patch-Impact-Analyzer",
        changed_files=changed_files_dict,
        changed_functions=changed_functions,
        dependency_map=dependency_map,
        ai_analysis=ai_result,
        output_path=pdf_path
    )

    # --------------------------------------------------------
    # Check that PDF was actually created
    # --------------------------------------------------------

    if not os.path.exists(pdf_path):

        return {
            "error": "PDF generation failed. The report file was not created."
        }

    # --------------------------------------------------------
    # Return PDF to browser
    # --------------------------------------------------------

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="security_patch_report.pdf"
    )