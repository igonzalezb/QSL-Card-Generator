#!/bin/bash

APP_VERSION=$(grep "APP_VERSION" core/version.py | awk -F'=' '{print $2}' | tr -d ' "' | tr -d "'")

echo "================================================"
echo "📦 Detected version: $APP_VERSION"
echo "================================================"
read -p "Is this the correct version for compilation? (y/n): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "❌ Compilation cancelled. Please update core/version.py and try again!"
    exit 1
fi
echo "✅ Version confirmed. Starting compilation..."
echo ""

# Clean up previous versions (in root and dist)
rm -rf AppDir
rm -f *.AppImage
rm -f dist/*.AppImage
rm -f linuxdeploy*.AppImage
rm -f appdir-lint.sh

# Download tools
wget -nc https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget -nc https://github.com/niess/linuxdeploy-plugin-python/releases/download/continuous/linuxdeploy-plugin-python-x86_64.AppImage
wget -nc https://raw.githubusercontent.com/AppImageCommunity/pkg2appimage/refs/heads/master/appdir-lint.sh
wget -nc https://raw.githubusercontent.com/AppImageCommunity/pkg2appimage/refs/heads/master/excludelist

chmod +x linuxdeploy*.AppImage
chmod +x appdir-lint.sh

# Python configuration
export PYTHON_VERSION=3.10
export PIP_REQUIREMENTS="PyQt6 Pillow adif-io certifi"
PYTHON_BIN=$(which python3)

# Prepare internal structure and copy source code
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/qsl-generator
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/metainfo
mkdir -p AppDir/usr/share/appdata

cp -r core ui docs locales resources *.py *.ui *.svg *.png *.ico *.ttf AppDir/usr/share/qsl-generator/ 2>/dev/null
cp io.github.igonzalezb.qsl-generator.appdata.xml AppDir/usr/share/metainfo/qsl-generator.appdata.xml
cp io.github.igonzalezb.qsl-generator.appdata.xml AppDir/usr/share/appdata/qsl-generator.appdata.xml
cp qsl-generator.desktop AppDir/usr/share/applications/

# Create the internal launcher
cat << 'EOF' > AppDir/usr/bin/qsl-generator
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="$HERE/../share/qsl-generator:$PYTHONPATH"

# LA MAGIA: Le decimos a Python que primero busque librerías gráficas adentro de la AppImage
export LD_LIBRARY_PATH="$HERE/../lib:$HERE/../lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

exec "$HERE/python3" "$HERE/../share/qsl-generator/main.py" "$@"
EOF
chmod +x AppDir/usr/bin/qsl-generator

# Generate the AppImage

./linuxdeploy-x86_64.AppImage \
    --appdir AppDir \
    --plugin python \
    --executable "$PYTHON_BIN" \
    --desktop-file dist/qsl-generator.desktop \
    --icon-file icon.png

    
echo "------------------------------------------------"
echo "🔧 ADDING LIBRARIES XCB/X11..."
echo "------------------------------------------------"

mkdir -p AppDir/usr/lib
cp -P /usr/lib/x86_64-linux-gnu/libxcb*.so* AppDir/usr/lib/ 2>/dev/null || true
cp -P /usr/lib/x86_64-linux-gnu/libxkbcommon*.so* AppDir/usr/lib/ 2>/dev/null || true

echo "📦 Closing the AppImage package..."

./linuxdeploy-x86_64.AppImage --appdir AppDir --output appimage

echo "------------------------------------------------"
echo "🔍 STARTING OFFICIAL QUALITY CHECKS..."
echo "------------------------------------------------"

# Find the generated file
GENERATED_FILE=$(ls *.AppImage 2>/dev/null | grep -v "linuxdeploy")

if [ -f "$GENERATED_FILE" ]; then
    
    # CHECK 1: Validate .desktop file
    echo "▶️ Running desktop-file-validate..."
    if command -v desktop-file-validate >/dev/null 2>&1; then
        # Look for it inside the AppDir that linuxdeploy just built
        desktop_file=$(find AppDir -name "*.desktop" | head -n 1)
        if [ -n "$desktop_file" ]; then
            desktop-file-validate "$desktop_file"
            if [ $? -eq 0 ]; then
                echo "  ✅ Valid .desktop file"
            else
                echo "  ❌ ERROR: The .desktop file has errors. Please check it."
                exit 1
            fi
        else
            echo "  ❌ ERROR: No .desktop file found in AppDir."
            exit 1
        fi
    else
         echo "  ⚠️ 'desktop-file-validate' is not installed. Skipping test. (Install with: sudo apt install desktop-file-utils)"
    fi

    # CHECK 2: Run the official AppDir Linter
    echo "▶️ Running appdir-lint.sh..."
    ./appdir-lint.sh AppDir/
    LINT_RESULT=$?
    
    if [ $LINT_RESULT -eq 0 ]; then
        echo "  ✅ AppDir passed the official linter"
    else
        echo "  ❌ ERROR: The linter detected issues. Build aborted."
        # We don't delete AppDir so you can inspect what went wrong
        exit 1
    fi

    echo "================================================"
    echo "🌟 ALL TESTS PASSED!"
    echo "================================================"
    
    # Move everything and clean up only after tests pass
    mv "$GENERATED_FILE" dist/
    echo "📦 AppImage ready to publish at: dist/$GENERATED_FILE"
    
    echo "🧹 Cleaning up temporary files..."
    rm -rf AppDir
    rm linuxdeploy*.AppImage
    rm appdir-lint.sh
    rm excludelist
    
else
    echo "❌ ERROR: AppImage file could not be generated."
fi