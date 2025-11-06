# Task 3.4 Reference - Parts 4-9

This document contains the remaining steps for integrating VenvManager and PackageInstallThread into main.py.

You've completed Parts 1-3 (imports, __init__ variables, and Tools menu). Here are the remaining parts:

---

## Part 4: Initialize venv when creating a new project

**Location:** In `new_file()` method (around lines 118-132)

**Find this code:**
```python
try:
    project_path = create_project(name, location)
    self.set_current_project_path(project_path)
    print(f"New project created at: {project_path}")
except FileExistsError as e:
    print(str(e))
```

**Change it to:**
```python
try:
    project_path = create_project(name, location)
    # Initialize venv for new project
    self.venv_manager = initialize_project_venv(project_path)
    self.set_current_project_path(project_path)
    print(f"New project created at: {project_path}")
except FileExistsError as e:
    print(str(e))
```

**What this does:** When creating a new project, immediately initialize the venv_manager so it's ready to use.

---

## Part 5: Initialize venv when opening existing project

**Location:** In `open_file()` method (around lines 134-145)

**Find this code:**
```python
self.canvas.scene.clear()
self.canvas.scene.connections = []
self.set_current_project_path(project_path)

print(f"Project opened: {project_path}")
```

**Change it to:**
```python
self.canvas.scene.clear()
self.canvas.scene.connections = []
# Initialize venv for existing project
self.venv_manager = initialize_project_venv(Path(project_path))
self.set_current_project_path(project_path)

print(f"Project opened: {project_path}")
```

**What this does:** When opening an existing project, initialize the venv_manager (and create venv if it doesn't exist).

---

## Part 6: Enable "Install Dependencies" menu when project opens

**Location:** In `set_current_project_path()` method (around lines 189-206)

**Find this line:**
```python
self.stop_action.setEnabled(True)
```

**After that line, add:**
```python
self.install_deps_action.setEnabled(True)
```

**What this does:** Enable the "Install Dependencies" menu item when a project is loaded.

---

## Part 7: Cleanup venv_manager when project closes

**Location:** In `close_current_project()` method (around lines 208-222)

**After this line:**
```python
self.project_name = None
```

**Add:**
```python
self.venv_manager = None
```

**Then, after this line:**
```python
self.stop_action.setEnabled(False)
```

**Add:**
```python
self.install_deps_action.setEnabled(False)
```

**What this does:** Clean up the venv_manager reference and disable the menu item when closing a project.

---

## Part 8: Create the `install_dependencies()` method

**Location:** Add this new method after `reload_script()` (after line 248)

```python
def install_dependencies(self):
    """Install packages from requirements.txt using the project's venv."""
    if not self.current_project_path:
        print("No project open.")
        return

    if not self.venv_manager:
        print("Virtual environment not initialized.")
        return

    # Check if venv exists
    if not self.venv_manager.venv_exists():
        print("Virtual environment not found. Creating...")
        if not self.venv_manager.create_venv():
            print("Failed to create virtual environment.")
            return

    # Get paths
    pip_path = self.venv_manager.get_pip_path()
    requirements_file = str(self.current_project_path / "requirements.txt")

    # Create and start the install thread
    self.install_thread = PackageInstallThread(pip_path, requirements_file)

    # Connect signals
    self.install_thread.output_signal.connect(self.console.append_output)
    self.install_thread.progress_signal.connect(self._on_install_progress)
    self.install_thread.finished_signal.connect(self._on_install_finished)

    # Update status and start
    self.status_bar.show_temporary_message("Installing dependencies...", 0)  # 0 = don't auto-clear
    self.console.append_output("=== Installing dependencies ===\n")
    self.install_thread.start()
```

**What this does:**
1. Validates that a project is open and venv exists
2. Gets the pip path from venv_manager
3. Creates a PackageInstallThread
4. Connects its signals to update the console and status bar
5. Starts the thread (runs in background)

---

## Part 9: Add progress and completion handlers

**Location:** Add these two helper methods after `install_dependencies()`

```python
def _on_install_progress(self, percentage):
    """Update status bar with installation progress."""
    self.status_bar.show_temporary_message(f"Installing dependencies... {percentage}%", 0)

def _on_install_finished(self, success):
    """Handle completion of package installation."""
    if success:
        self.console.append_output("\n=== Installation complete ✓ ===\n")
        self.status_bar.show_temporary_message("✓ Dependencies installed", 3000)
    else:
        self.console.append_output("\n=== Installation failed ✗ ===\n")
        self.status_bar.show_temporary_message("✗ Installation failed", 3000)
```

**What these do:**
- `_on_install_progress()`: Called repeatedly during installation to update status bar with percentage
- `_on_install_finished()`: Called once when installation completes (success or failure)

---

## Quick Checklist

- [ ] Part 4: Add venv init to `new_file()`
- [ ] Part 5: Add venv init to `open_file()`
- [ ] Part 6: Enable menu in `set_current_project_path()`
- [ ] Part 7: Cleanup in `close_current_project()`
- [ ] Part 8: Create `install_dependencies()` method
- [ ] Part 9: Create `_on_install_progress()` and `_on_install_finished()` methods

---

## Testing After Completion

Once you've implemented all parts, test by:

1. Create a new project → venv should be created automatically
2. Add a package to requirements.txt (e.g., `requests`)
3. Click Tools → Install Dependencies
4. Watch the console for output
5. Check that status bar shows progress
6. Verify completion message

---

## Key Concepts

**Signal Connections:**
- `output_signal` → `console.append_output` (shows pip output)
- `progress_signal` → `_on_install_progress` (updates status bar with %)
- `finished_signal` → `_on_install_finished` (shows completion message)

**Thread Safety:**
The PackageInstallThread runs in the background. It can't directly update the GUI, so it uses signals to safely communicate with the main thread.

**VenvManager Lifecycle:**
- Created when project opens: `self.venv_manager = initialize_project_venv(...)`
- Used during package install: `pip_path = self.venv_manager.get_pip_path()`
- Cleaned up when project closes: `self.venv_manager = None`

---

## Common Issues

**Import errors:** Make sure you added all imports in Part 1:
```python
from utils.project_manager import create_project, validate_project, get_project_name, initialize_project_venv
from core.venv_manager import VenvManager
from core.package_installer import PackageInstallThread
```

**Menu item doesn't work:** Check that you:
1. Created the action in `_create_menubar()`
2. Connected it to `install_dependencies` method
3. Enable it in `set_current_project_path()`

**Console doesn't show output:** Verify you connected the signal:
```python
self.install_thread.output_signal.connect(self.console.append_output)
```

---

Good luck! When you're done, show me the updated main.py and I'll review it for you.
