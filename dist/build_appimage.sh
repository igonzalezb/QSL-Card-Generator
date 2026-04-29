#!/bin/bash

# Clean up previous versions (in root and dist)
rm -rf AppDir
rm -f *.AppImage
rm -f dist/*.AppImage
rm -f linuxdeploy-plugin-python-x86_64.AppImage linuxdeploy-x86_64.AppImage

# Download tools
wget -nc https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget -nc https://github.com/niess/linuxdeploy-plugin-python/releases/download/continuous/linuxdeploy-plugin-python-x86_64.AppImage
chmod +x linuxdeploy*.AppImage

# Python configuration
export PYTHON_VERSION=3.10
export PIP_REQUIREMENTS="PyQt6 Pillow adif-io"
PYTHON_BIN=$(which python3)

# Prepare internal structure and copy source code
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/qsl-generator
cp -r core ui docs locales resources *.py *.ui AppDir/usr/share/qsl-generator/ 2>/dev/null

# Create the internal launcher
cat << 'EOF' > AppDir/usr/bin/qsl-generator
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="$HERE/../share/qsl-generator:$PYTHONPATH"
exec python3 "$HERE/../share/qsl-generator/main.py" "$@"
EOF
chmod +x AppDir/usr/bin/qsl-generator

# Generate the AppImage
./linuxdeploy-x86_64.AppImage --appdir AppDir \
    --plugin python \
    --executable "$PYTHON_BIN" \
    --desktop-file dist/qsl-generator.desktop \
    --icon-file icon.svg \
    --output appimage

# Move result to DIST and Cleanup
echo "------------------------------------------------"
GENERATED_FILE=$(ls *.AppImage 2>/dev/null | grep -v "linuxdeploy")

if [ -f "$GENERATED_FILE" ]; then
    echo "✅ AppImage generated: $GENERATED_FILE"
    
    mv "$GENERATED_FILE" dist/
    echo "📦 Executable moved to: dist/$GENERATED_FILE"
    
    echo "🧹 Cleaning up temporary files..."
    rm -rf AppDir
    rm linuxdeploy-x86_64.AppImage
    rm linuxdeploy-plugin-python-x86_64.AppImage
    
    echo "✨ Process finished. Everything is clean."
else
    echo "❌ Error: Generated AppImage file not found."
fi