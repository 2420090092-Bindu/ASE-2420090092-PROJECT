import os
import ast


# ============================================================
# GET ALL PYTHON FILES
# ============================================================

def get_python_files(project_path):

    python_files = []

    for root, dirs, files in os.walk(project_path):

        for file in files:

            if file.endswith(".py"):

                python_files.append(
                    os.path.join(root, file)
                )

    return python_files


# ============================================================
# FUNCTION CALL VISITOR
# ============================================================

class FunctionCallVisitor(ast.NodeVisitor):

    def __init__(self):

        self.calls = []

    def visit_Call(self, node):

        if isinstance(node.func, ast.Name):

            self.calls.append(
                node.func.id
            )

        self.generic_visit(node)


# ============================================================
# ANALYZE PYTHON FILE
# ============================================================

def analyze_python_file(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        source_code = f.read()

    tree = ast.parse(source_code)

    functions = []
    classes = []
    imports = []
    dependencies = {}

    for node in tree.body:

        # Functions
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):

            functions.append(
                node.name
            )

            visitor = FunctionCallVisitor()

            visitor.visit(node)

            dependencies[node.name] = (
                visitor.calls
            )

        # Classes
        elif isinstance(
            node,
            ast.ClassDef
        ):

            classes.append(
                node.name
            )

        # import something
        elif isinstance(
            node,
            ast.Import
        ):

            for alias in node.names:

                imports.append(
                    alias.name
                )

        # from something import something
        elif isinstance(
            node,
            ast.ImportFrom
        ):

            if node.module:

                imports.append(
                    node.module
                )

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "dependencies": dependencies
    }