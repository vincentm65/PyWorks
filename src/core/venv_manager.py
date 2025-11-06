import os
import subprocess
import pathlib
import venv

class VenvManager():
    def __init__(self, project_path):
        self.project_path = project_path

    def venv_exists(self):
        return os.path.exists(os.path.join(self.project_path, ".venv"))

    def create_venv(self):
        try:
            venv_dir = os.path.join(self.project_path, ".venv")
            venv.create(venv_dir, with_pip=True)
            return True
        except Exception as e: 
            print(f".venv creation fail: {e}!")
            return False

    def get_python_path(self):
        if self.venv_exists():
            python_path = os.path.join(self.project_path, ".venv", "Scripts", "python.exe")
        else:
            python_path = ""
        return python_path

    def get_pip_path(self):
        if self.venv_exists():
            pip_path = os.path.join(self.project_path, ".venv", "Scripts", "pip.exe")
        else:
            pip_path = ""
        return pip_path

    def validate_venv(self):
        python_path = self.get_python_path()

        if not python_path:
          return False

        try:
            subprocess.run(
                [python_path, "-c", "import sys; print(sys.version)"],
                capture_output=True,
                check=True
            )
            return True
        except Exception as e:
            print(f"Error validating .venv {e}")
            return False
