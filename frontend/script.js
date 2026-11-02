const API_URL = "http://127.0.0.1:8000";


// ===============================
// Upload Project
// ===============================

async function uploadProject() {

    const fileInput = document.getElementById("projectFile");
    const status = document.getElementById("projectStatus");

    if (fileInput.files.length === 0) {
        status.innerText = "Please select a ZIP file first.";
        return;
    }

    const file = fileInput.files[0];

    const formData = new FormData();
    formData.append("file", file);

    status.innerText = "Uploading project...";

    try {

        const response = await fetch(
            `${API_URL}/upload`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (response.ok) {

            status.innerText =
                "Project uploaded successfully!";

        } else {

            status.innerText =
                data.detail || "Project upload failed.";
        }

    } catch (error) {

        status.innerText =
            "Error connecting to backend.";

        console.error(error);
    }
}


// ===============================
// Upload Patch
// ===============================

async function uploadPatch() {

    const fileInput = document.getElementById("patchFile");
    const status = document.getElementById("patchStatus");

    if (fileInput.files.length === 0) {

        status.innerText =
            "Please select a ZIP file first.";

        return;
    }

    const file = fileInput.files[0];

    const formData = new FormData();
    formData.append("file", file);

    status.innerText =
        "Uploading patch...";

    try {

        const response = await fetch(
            `${API_URL}/upload-patch`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (response.ok) {

            status.innerText =
                "Patch uploaded successfully!";

        } else {

            status.innerText =
                data.detail || "Patch upload failed.";
        }

    } catch (error) {

        status.innerText =
            "Error connecting to backend.";

        console.error(error);
    }
}


// ===============================
// Analyze Project
// ===============================

async function analyzeProject() {

    const changedFiles =
        document.getElementById("changedFiles");

    const changedFunctions =
        document.getElementById("changedFunctions");

    const aiReport =
        document.getElementById("aiReport");


    // Show loading messages

    changedFiles.innerText =
        "Analyzing...";

    changedFunctions.innerText =
        "Analyzing...";

    aiReport.innerText =
        "AI analysis in progress...";


    try {

        const response = await fetch(
            `${API_URL}/ai-analysis`
        );

        const data = await response.json();


        // ===============================
        // Check for backend error
        // ===============================

        if (!response.ok) {

            changedFiles.innerText =
                "Analysis failed.";

            changedFunctions.innerText =
                "";

            aiReport.innerText =
                data.detail ||
                data.error ||
                "Unknown error.";

            return;
        }


        // ===============================
        // Changed Files
        // ===============================

        const files = new Set();


        if (data.changed_functions) {

            for (
                const item of
                (data.changed_functions.added_functions || [])
            ) {

                files.add(item.file);
            }


            for (
                const item of
                (data.changed_functions.removed_functions || [])
            ) {

                files.add(item.file);
            }


            for (
                const item of
                (data.changed_functions.modified_functions || [])
            ) {

                files.add(item.file);
            }
        }


        if (files.size === 0) {

            changedFiles.innerText =
                "No changed files detected.";

        } else {

            changedFiles.innerText =
                Array.from(files).join("\n");
        }


        // ===============================
        // Changed Functions
        // ===============================

        if (data.changed_functions) {

            changedFunctions.innerText =
                JSON.stringify(
                    data.changed_functions,
                    null,
                    2
                );

        } else {

            changedFunctions.innerText =
                "No changed functions found.";
        }


        // ===============================
        // AI Security Report
        // ===============================

        if (data.ai_analysis) {


            // If AI response is an object

            if (
                typeof data.ai_analysis === "object"
            ) {

                aiReport.innerText =
                    data.ai_analysis.ai_analysis ||
                    JSON.stringify(
                        data.ai_analysis,
                        null,
                        2
                    );


            // If AI response is already text

            } else {

                aiReport.innerText =
                    data.ai_analysis;
            }


        } else {

            aiReport.innerText =
                "No AI analysis returned.";
        }


    } catch (error) {

        changedFiles.innerText =
            "Error connecting to backend.";

        changedFunctions.innerText =
            "";

        aiReport.innerText =
            "Could not connect to FastAPI backend.";

        console.error(error);
    }
}


// ===============================
// Download PDF Report
// ===============================

function downloadReport() {

    window.open(
        `${API_URL}/generate-report`,
        "_blank"
    );
}