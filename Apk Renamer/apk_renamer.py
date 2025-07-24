import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import re
import sys
import webbrowser # Import webbrowser module to open URLs

# Attempt to import TkinterDnD2. If it fails, provide instructions to install.
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    # If TkinterDnD2 is not found, show an error and exit.
    messagebox.showerror("Error", "The 'tkinterdnd2' library is not found.\n"
                                  "Please install it using:\n\n"
                                  "pip install tkinterdnd2\n\n"
                                  "Then restart the application.")
    sys.exit(1) # Exit the application if the dependency is missing

# Function to extract app name and version from APK using 'aapt' tool.
# 'aapt' is part of Android SDK Build-Tools and must be in the system's PATH.
def get_apk_info(apk_path):
    """
    Extracts the application label (app name) and version name from an APK file
    using the 'aapt' command-line tool.

    Args:
        apk_path (str): The full path to the APK file.

    Returns:
        tuple: A tuple containing (app_name, version_name) strings.
               Returns (None, None) if 'aapt' is not found, an error occurs,
               or information cannot be extracted.
    """
    try:
        # Construct the command to run 'aapt dump badging' on the APK.
        # We assume 'aapt' is available in the system's PATH.
        cmd = ['aapt', 'dump', 'badging', apk_path]

        # Execute the command and capture its output.
        # 'text=True' decodes stdout/stderr as text, 'check=True' raises an
        # exception for non-zero exit codes.
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        output = result.stdout

        app_name = "UnknownApp"
        version_name = "UnknownVersion"

        # Use regular expressions to find the application label.
        # The label is typically found in a line like: application-label:'My Awesome App'
        label_match = re.search(r"application-label:'([^']+)'", output)
        if label_match:
            # Sanitize the app name for use in a filename (remove spaces, slashes).
            app_name = label_match.group(1).replace(" ", "_").replace("/", "_").replace("\\", "_")

        # Use regular expressions to find the versionName.
        # The version name is typically found in a line like: versionName='1.0'
        version_match = re.search(r"versionName='([^']+)'", output)
        if version_match:
            version_name = version_match.group(1)

        return app_name, version_name

    except FileNotFoundError:
        # Handle the case where 'aapt' executable is not found.
        messagebox.showerror("Error", "aapt not found.\n"
                                      "Please ensure Android SDK Build-Tools are installed and 'aapt' is in your system's PATH.\n"
                                      "You can typically find 'aapt' in 'Android/sdk/build-tools/<version>/'.")
        return None, None
    except subprocess.CalledProcessError as e:
        # Handle errors if 'aapt' runs but returns an error (e.g., invalid APK).
        messagebox.showerror("Error", f"Error running aapt on '{os.path.basename(apk_path)}':\n{e.stderr}")
        return None, None
    except Exception as e:
        # Catch any other unexpected errors during the process.
        messagebox.showerror("Error", f"An unexpected error occurred while parsing APK: {e}")
        return None, None

# Function to rename the APK file based on extracted information.
def rename_apk(apk_path):
    """
    Renames an APK file to 'AppName_VersionName.apk' after extracting
    the necessary information using get_apk_info.

    Args:
        apk_path (str): The full path to the APK file to be renamed.
    """
    app_name, version_name = get_apk_info(apk_path)

    # If info extraction failed, get_apk_info would have already shown an error.
    if app_name is None or version_name is None:
        return

    # Separate the directory and filename from the full path.
    directory, filename = os.path.split(apk_path)
    # Get the base name (without extension) and the extension.
    base_name, ext = os.path.splitext(filename)

    # Construct the new filename.
    new_filename = f"{app_name}_{version_name}.apk"
    # Construct the full new path.
    new_filepath = os.path.join(directory, new_filename)

    try:
        # Check if the new file path is the same as the old one (already correctly named).
        if os.path.normpath(apk_path) == os.path.normpath(new_filepath):
            messagebox.showinfo("Info", f"File is already named correctly:\n'{filename}'")
            return

        # Perform the file renaming operation.
        os.rename(apk_path, new_filepath)
        messagebox.showinfo("Success", f"Renamed:\n'{filename}'\nto\n'{new_filename}'")
    except OSError as e:
        # Handle OS-level errors during renaming (e.g., file in use, permissions).
        messagebox.showerror("Error", f"Failed to rename file:\n{e}")
    except Exception as e:
        # Catch any other unexpected errors during renaming.
        messagebox.showerror("Error", f"An unexpected error occurred during renaming: {e}")

# Main GUI application class.
class APKRenamerApp(TkinterDnD.Tk): # Inherit from TkinterDnD.Tk to enable drag-and-drop
    def __init__(self):
        super().__init__()
        self.title("APK Renamer")
        self.geometry("500x300")
        self.configure(bg="#2c3e50") # Set a dark background color for the window

        # Configure grid to make the main frame expandable with window resizing.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a main frame for content, providing padding and a visual border.
        main_frame = tk.Frame(self, bg="#34495e", bd=5, relief="raised", padx=20, pady=20)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        # Make the content within the main frame expandable.
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        # Add a row for the GitHub link
        main_frame.grid_rowconfigure(2, weight=0)


        # Create the drag-and-drop target label.
        self.drop_label = tk.Label(
            main_frame,
            text="Drag & Drop APK File Here",
            bg="#ecf0f1", # Light background for contrast
            fg="#2c3e50", # Dark text color
            font=("Inter", 16, "bold"), # Modern font with bold style
            relief="groove", # Grooved border
            borderwidth=3, # Border thickness
            wraplength=350, # Wrap text if it exceeds this width
            padx=20,
            pady=40
        )
        self.drop_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Register the label as a drop target for files.
        self.drop_label.drop_target_register(DND_FILES)
        # Bind the drop event to the handle_drop method.
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

        # Add an instructions label about the 'aapt' dependency.
        instructions_label = tk.Label(
            main_frame,
            text="Note: This tool requires 'aapt' from Android SDK Build-Tools to be in your system's PATH.",
            bg="#34495e",
            fg="#bdc3c7", # Lighter grey text for notes
            font=("Inter", 10, "italic"), # Italicized font for notes
            wraplength=400 # Wrap text for readability
        )
        instructions_label.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Add the GitHub source code link
        self.github_link_label = tk.Label(
            main_frame,
            text="https://github.com/shahabsaalami",
            fg="#66ccff",  # Blue color for a link
            bg="#34495e",
            font=("Inter", 10, "underline"), # Underline to indicate it's a link
            cursor="hand2" # Change cursor to hand on hover
        )
        self.github_link_label.grid(row=2, column=0, sticky="s", padx=10, pady=5)
        self.github_link_label.bind("<Button-1>", lambda e: self.open_github_link("https://github.com/shahabsaalami"))

    def handle_drop(self, event):
        """
        Handles the file drop event.
        Processes the first dropped file if it's an APK.
        """
        # event.data contains the path(s) of the dropped file(s).
        # tk.splitlist handles multiple paths and paths with spaces (enclosed in braces).
        files = self.tk.splitlist(event.data)
        if files:
            apk_path = files[0] # Process only the first dropped file for simplicity.

            if apk_path.lower().endswith(".apk"):
                # Update the label to show that processing is underway.
                self.drop_label.config(text=f"Processing: {os.path.basename(apk_path)}...")
                self.update_idletasks() # Force GUI update immediately.

                # Call the renaming function.
                rename_apk(apk_path)

                # Reset the label text after processing.
                self.drop_label.config(text="Drag & Drop APK File Here")
            else:
                # Show a warning if the dropped file is not an APK.
                messagebox.showwarning("Invalid File", "Please drop an APK file (.apk).")
                # Reset the label text.
                self.drop_label.config(text="Drag & Drop APK File Here")

    def open_github_link(self, url):
        """Opens the specified URL in the default web browser."""
        webbrowser.open_new(url)

# Entry point for the application.
if __name__ == "__main__":
    # Check if any command-line arguments are provided (e.g., an APK path from right-click).
    if len(sys.argv) > 1:
        apk_file_path = sys.argv[1]
        if os.path.exists(apk_file_path) and apk_file_path.lower().endswith(".apk"):
            rename_apk(apk_file_path)
            sys.exit(0) # Exit after processing the file
        else:
            # If the argument is not a valid APK path, show an error and exit.
            messagebox.showerror("Error", f"Invalid file path provided: {apk_file_path}\n"
                                          "Please ensure it's a valid APK file.")
            sys.exit(1)
    else:
        # If no command-line arguments, launch the GUI for drag-and-drop.
        app = APKRenamerApp()
        app.mainloop() # Start the Tkinter event loop.
