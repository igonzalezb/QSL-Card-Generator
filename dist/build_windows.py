import os
import shutil
import subprocess

def clean_temp_files():
    folders_to_remove = ['build', '__pycache__']

    for folder in folders_to_remove:
        if os.path.exists(folder):
            print(f"Cleaning: {folder}/")
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Could not delete {folder}: {e}")


if __name__ == "__main__":
    print("Starting PyInstaller build process...")
    # check if pyinstaller is installed
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("PyInstaller is not installed. Please install it using 'pip install pyinstaller' and try again.")
        exit(1)
        
    process = subprocess.run(["pyinstaller", "main.spec", "--clean"])

    print("\n" + "=" * 50)

    if process.returncode == 0:
        print("Build completed successfully! Cleaning temporary files...")
        clean_temp_files()
        print("Done!")
    else:
        print("An error occurred during the PyInstaller build process.")

    print("=" * 50 + "\n")