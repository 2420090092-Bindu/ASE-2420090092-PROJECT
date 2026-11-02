from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
import os
import re


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    """
    Clean AI-generated text without damaging normal words.
    """

    if text is None:
        return ""

    text = str(text)

    # Convert escaped newlines into real newlines
    text = text.replace("\\r\\n", "\n")
    text = text.replace("\\n", "\n")
    text = text.replace("\\r", "\n")

    # Fix only known AI formatting artifacts.
    # IMPORTANT:
    # Do NOT remove every 'n' from words because that damages
    # words such as introduces, function, dependency, input, etc.
    replacements = {
        "securitynrelated": "security-related",
        "denialnofnservicenlike": "denial-of-service-like",
        "Endntonend": "End-to-end",
        "endntonend": "end-to-end",
        "textnprocessing": "text-processing",
        "securitynorie ted": "security-oriented",
        "securitynorie": "security-orie",
        "misnwire": "miswire",
        "sideneffects": "side effects",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Fix a few very specific corrupted phrases
    specific_replacements = {
        "i troduces": "introduces",
        "i troduce": "introduce",
        "fu ction": "function",
        "fu ctions": "functions",
        "depe dency": "dependency",
        "depe dencies": "dependencies",
        "co firm": "confirm",
        "k own": "known",
        "k ownngood": "known-good",
        "i put": "input",
        "i puts": "inputs",
        "ru time": "runtime",
        "u i te tio ally": "unintentionally",
        "u i te tio al": "unintentional",
        "cha ges": "changes",
        "cha ge": "change",
        "wi e spread": "widespread",
        "widespread": "widespread",
        "si gle": "single",
        "Comprehe sive": "Comprehensive",
        "comprehe sive": "comprehensive",
        "sce arios": "scenarios",
        "respo ses": "responses",
        "respo se": "response",
        "prenpatch": "pre-patch",
        "prepatch": "pre-patch",
        "i cluding": "including",
        "i clude": "include",
        "i tegration": "integration",
        "i tegrated": "integrated",
        "i te sive": "intensive",
        "u der": "under",
        "i crease": "increase",
        "i troduced": "introduced",
        "i correct": "incorrect",
        "i correctly": "incorrectly",
        "vul erable": "vulnerable",
        "i teraction": "interaction",
        "i teractions": "interactions",
        "u expected": "unexpected",
        "ha dling": "handling",
        "ha dler": "handler",
        "ha dlers": "handlers",
        "fu ctio al": "functional",
        "fu ctional": "functional",
        "pot e tially": "potentially",
        "pote tially": "potentially",
        "legitimate traffic": "legitimate traffic",
        "k own": "known",
        "bou dary": "boundary",
        "co ditions": "conditions",
        "Comprehe sive": "Comprehensive",
        "be chmark": "benchmark",
        "i tegration": "integration",
        "i te grated": "integrated",
        "i ntegration": "integration",
        "securit ynoriented": "security-oriented",
        "securitynorie ted": "security-oriented",
    }

    for old, new in specific_replacements.items():
        text = text.replace(old, new)

    # Remove excessive spaces while preserving newlines
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces before punctuation
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    return text.strip()


# ============================================================
# REPORTLAB SAFE PARAGRAPH
# ============================================================

def paragraph_text(text, style):
    """
    Convert normal text into a safe ReportLab paragraph.
    """

    text = clean_text(text)

    # Escape ReportLab special characters
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    return Paragraph(text, style)


# ============================================================
# DEPENDENCY NORMALIZATION
# ============================================================

def normalize_dependency_map(dependency_map):
    """
    Convert different dependency-map formats into:

    [
        {
            "file": "app.py",
            "function": "home",
            "dependencies": ["autocorrect", "simplify_text"]
        }
    ]
    """

    rows = []

    if not dependency_map:
        return rows

    def add_function(file_name, function_name, dependencies):

        if not function_name:
            return

        # Ignore accidental metadata
        if str(function_name).lower() in {
            "file",
            "filename",
            "path",
            "functions",
            "classes",
            "imports",
            "dependencies"
        }:
            return

        if dependencies is None:
            dependencies = []

        if not isinstance(dependencies, list):
            dependencies = [dependencies]

        cleaned_dependencies = []

        for dependency in dependencies:

            if dependency is None:
                continue

            dependency = str(dependency).strip()

            if not dependency:
                continue

            # Ignore accidental metadata
            if dependency.lower() in {
                "none",
                "null",
                "file",
                "filename",
                "path"
            }:
                continue

            cleaned_dependencies.append(dependency)

        rows.append(
            {
                "file": os.path.basename(str(file_name))
                if file_name
                else "app.py",

                "function": str(function_name),

                "dependencies": cleaned_dependencies
            }
        )

    # --------------------------------------------------------
    # Dictionary format
    # --------------------------------------------------------

    if isinstance(dependency_map, dict):

        for file_name, value in dependency_map.items():

            # Example:
            #
            # {
            #     "app.py": {
            #         "home": [
            #             "autocorrect",
            #             "simplify_text"
            #         ]
            #     }
            # }

            if isinstance(value, dict):

                # Handle wrapper:
                #
                # {
                #   "dependencies": {
                #       "home": [...]
                #   }
                # }

                if (
                    "dependencies" in value
                    and isinstance(value["dependencies"], dict)
                ):
                    value = value["dependencies"]

                for function_name, dependencies in value.items():

                    if function_name in {
                        "file",
                        "filename",
                        "path",
                        "functions",
                        "classes",
                        "imports"
                    }:
                        continue

                    add_function(
                        file_name,
                        function_name,
                        dependencies
                    )

            # Example:
            #
            # {
            #     "home": [
            #         "autocorrect",
            #         "simplify_text"
            #     ]
            #
            elif isinstance(value, list):

                add_function(
                    "app.py",
                    file_name,
                    value
                )

    # --------------------------------------------------------
    # List format
    # --------------------------------------------------------

    elif isinstance(dependency_map, list):

        for item in dependency_map:

            if not isinstance(item, dict):
                continue

            file_name = (
                item.get("file")
                or item.get("filename")
                or item.get("path")
                or "app.py"
            )

            function_name = (
                item.get("function")
                or item.get("function_name")
                or item.get("name")
            )

            dependencies = (
                item.get("dependencies")
                or item.get("calls")
                or []
            )

            if function_name:
                add_function(
                    file_name,
                    function_name,
                    dependencies
                )

    return rows


# ============================================================
# PAGE FOOTER
# ============================================================

def footer(canvas, doc):
    """
    Add page number to every page.
    """

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        9
    )

    page_number = canvas.getPageNumber()

    canvas.drawCentredString(
        A4[0] / 2,
        0.45 * inch,
        f"Page {page_number}"
    )

    canvas.restoreState()


# ============================================================
# MAIN PDF GENERATOR
# ============================================================

def generate_pdf_report(
    project_name,
    changed_files,
    changed_functions,
    dependency_map,
    ai_analysis,
    output_path
):

    # Create reports directory if necessary
    output_directory = os.path.dirname(output_path)

    if output_directory:
        os.makedirs(
            output_directory,
            exist_ok=True
        )

    # --------------------------------------------------------
    # PDF DOCUMENT
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=15,
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=normal_style,
        leftIndent=15,
        firstLineIndent=-8,
        spaceAfter=4
    )

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "AI Security Patch Impact Analyzer",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Project:</b> {project_name}",
            normal_style
        )
    )

    story.append(
        Spacer(1, 10)
    )

    # ========================================================
    # CHANGED FILES
    # ========================================================

    story.append(
        Paragraph(
            "Changed Files",
            heading_style
        )
    )

    file_rows = [
        [
            Paragraph(
                "<b>File</b>",
                normal_style
            )
        ]
    ]

    if isinstance(changed_files, dict):

        for file_name in changed_files.keys():

            file_rows.append(
                [
                    paragraph_text(
                        os.path.basename(
                            str(file_name)
                        ),
                        normal_style
                    )
                ]
            )

    elif isinstance(changed_files, list):

        for file_name in changed_files:

            file_rows.append(
                [
                    paragraph_text(
                        os.path.basename(
                            str(file_name)
                        ),
                        normal_style
                    )
                ]
            )

    else:

        file_rows.append(
            [
                paragraph_text(
                    str(changed_files),
                    normal_style
                )
            ]
        )

    file_table = Table(
        file_rows,
        colWidths=[
            6.5 * inch
        ]
    )

    file_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )

    story.append(file_table)

    # ========================================================
    # CHANGED FUNCTIONS
    # ========================================================

    story.append(
        Paragraph(
            "Changed Functions",
            heading_style
        )
    )

    function_rows = [
        [
            Paragraph(
                "<b>Change Type</b>",
                normal_style
            ),
            Paragraph(
                "<b>File</b>",
                normal_style
            ),
            Paragraph(
                "<b>Function</b>",
                normal_style
            )
        ]
    ]

    if isinstance(changed_functions, dict):

        change_types = [
            (
                "Added",
                "added_functions"
            ),
            (
                "Removed",
                "removed_functions"
            ),
            (
                "Modified",
                "modified_functions"
            )
        ]

        for change_name, key in change_types:

            items = changed_functions.get(
                key,
                []
            )

            for item in items:

                if isinstance(item, dict):

                    file_name = (
                        item.get("file")
                        or "Unknown"
                    )

                    function_name = (
                        item.get("function")
                        or item.get("name")
                        or "Unknown"
                    )

                else:

                    file_name = "Unknown"
                    function_name = str(item)

                function_rows.append(
                    [
                        paragraph_text(
                            change_name,
                            normal_style
                        ),
                        paragraph_text(
                            os.path.basename(
                                str(file_name)
                            ),
                            normal_style
                        ),
                        paragraph_text(
                            function_name,
                            normal_style
                        )
                    ]
                )

    function_table = Table(
        function_rows,
        colWidths=[
            1.3 * inch,
            2.0 * inch,
            3.2 * inch
        ]
    )

    function_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )

    story.append(function_table)

    # ========================================================
    # DEPENDENCY SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "Dependency Summary",
            heading_style
        )
    )

    dependency_rows = [
        [
            Paragraph(
                "<b>File</b>",
                normal_style
            ),
            Paragraph(
                "<b>Function</b>",
                normal_style
            ),
            Paragraph(
                "<b>Dependencies</b>",
                normal_style
            )
        ]
    ]

    normalized_dependencies = normalize_dependency_map(
        dependency_map
    )

    if normalized_dependencies:

        for item in normalized_dependencies:

            dependencies = item["dependencies"]

            if dependencies:

                dependency_text = ", ".join(
                    str(dep)
                    for dep in dependencies
                )

            else:

                dependency_text = "None"

            dependency_rows.append(
                [
                    paragraph_text(
                        item["file"],
                        normal_style
                    ),
                    paragraph_text(
                        item["function"],
                        normal_style
                    ),
                    paragraph_text(
                        dependency_text,
                        normal_style
                    )
                ]
            )

    else:

        dependency_rows.append(
            [
                paragraph_text(
                    "None",
                    normal_style
                ),
                paragraph_text(
                    "None",
                    normal_style
                ),
                paragraph_text(
                    "None",
                    normal_style
                )
            ]
        )

    dependency_table = Table(
        dependency_rows,
        colWidths=[
            1.5 * inch,
            2.0 * inch,
            3.0 * inch
        ]
    )

    dependency_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )

    story.append(dependency_table)

    # ========================================================
    # AI SECURITY ANALYSIS
    # ========================================================

    story.append(
        Paragraph(
            "AI Security Analysis",
            heading_style
        )
    )

    if isinstance(ai_analysis, dict):

        ai_text = (
            ai_analysis.get("ai_analysis")
            or ai_analysis.get("analysis")
            or ai_analysis.get("result")
            or ""
        )

    else:

        ai_text = str(ai_analysis)

    ai_text = clean_text(ai_text)

    lines = ai_text.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            story.append(
                Spacer(1, 4)
            )
            continue

        # Remove Markdown bold markers
        line = line.replace("**", "")

        # ----------------------------------------------------
        # Numbered headings
        # ----------------------------------------------------

        numbered_heading = re.match(
            r"^(\d+)\.\s*(.+)$",
            line
        )

        if numbered_heading:

            number = numbered_heading.group(1)
            heading = numbered_heading.group(2)

            story.append(
                Paragraph(
                    f"<b>{number}. {heading}</b>",
                    heading_style
                )
            )

            continue

        # ----------------------------------------------------
        # Bullet points
        # ----------------------------------------------------

        if line.startswith("•"):

            content = line[1:].strip()

            story.append(
                paragraph_text(
                    "• " + content,
                    bullet_style
                )
            )

            continue

        if line.startswith("- "):

            content = line[2:].strip()

            story.append(
                paragraph_text(
                    "• " + content,
                    bullet_style
                )
            )

            continue

        # ----------------------------------------------------
        # Normal paragraph
        # ----------------------------------------------------

        story.append(
            paragraph_text(
                line,
                normal_style
            )
        )

    # ========================================================
    # END OF REPORT
    # ========================================================

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "<b>End of Report</b>",
            normal_style
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )

    return output_path