import os
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class PackageInstallThread(QThread):
    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, pip_path, requirements):
        super().__init__()
        self.pip_path = pip_path
        self.requirements = requirements

    def run(self):
        if not os.path.exists(self.requirements):
            self.finished_signal.emit(False)
            return

        self.count_packages()
        self.run_pip_install()

    def count_packages(self):
        with open(self.requirements, 'r') as f:
            lines = f.readlines()

        self.package_count = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                self.package_count += 1


    def run_pip_install(self):
        install_process = subprocess.Popen(
            [self.pip_path, "install", "-r", self.requirements],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        installed_count = 0
        for line in install_process.stdout:
            self.output_signal.emit(line.strip())

            if "Collecting" in line or "Successfully installed" in line:
                installed_count += 1
                percentage = int((installed_count/self.package_count) * 100)
                self.progress_signal.emit(percentage)

        install_process.wait()

        if install_process.returncode == 0:
            self.finished_signal.emit(True)
        else:
            self.finished_signal.emit(False)


    
    