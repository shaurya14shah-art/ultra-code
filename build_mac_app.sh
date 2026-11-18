#!/bin/bash
APP_NAME="UltraCodeNative"
BUNDLE_DIR="$APP_NAME.app"

# Remove any old bundle
rm -rf "$BUNDLE_DIR"
rm -rf "UltraCode.app"

# Create bundle structure
mkdir -p "$BUNDLE_DIR/Contents/MacOS"
mkdir -p "$BUNDLE_DIR/Contents/Resources"

# Compile Swift wrapper
swiftc AppWrapper.swift -o "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"

# Copy Info.plist
cp Info.plist "$BUNDLE_DIR/Contents/Info.plist"

echo "Successfully built $BUNDLE_DIR"
