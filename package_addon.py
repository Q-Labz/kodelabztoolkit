import os
import zipfile
import datetime

def package_addon():
    """
    Package the KodeLabz Toolkit add-on into a ZIP file for Blender installation.
    """
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the source directory (kodelabz_toolkit folder)
    source_dir = os.path.join(script_dir, "kodelabz_toolkit")
    
    # Create a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define the output ZIP filename
    zip_filename = os.path.join(script_dir, f"kodelabz_toolkit_v0.1_{timestamp}.zip")
    
    # Create a new ZIP file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all files and directories in the source directory
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                # Get the full path of the file
                file_path = os.path.join(root, file)
                
                # Get the relative path for the ZIP file
                rel_path = os.path.relpath(file_path, script_dir)
                
                # Add the file to the ZIP
                zipf.write(file_path, rel_path)
    
    print(f"Add-on packaged successfully: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    package_addon()
