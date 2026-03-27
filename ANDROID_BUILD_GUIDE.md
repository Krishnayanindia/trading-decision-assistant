# Android Build Guide - Trading Decision Assistant

This guide will help you build and deploy your Kivy trading app to Android.

## What Changed from Desktop to Mobile

✅ **Same Logic** - All trading algorithms (RSI, Stochastic) are identical
✅ **Same Data Source** - Still uses yfinance API
✅ **No CORS Issues** - Runs as native Android app
✅ **Mobile UI** - Touch-friendly Kivy interface

## Prerequisites

### Step 1: Install Required Tools

#### On Windows:

```bash
# Install Java Development Kit (JDK)
# Download from: https://www.oracle.com/java/technologies/downloads/
# Or use: choco install openjdk

# Install Android SDK
# Download Android Studio from: https://developer.android.com/studio
# Or use: choco install android-sdk

# Install Buildozer
pip install buildozer

# Install Cython
pip install cython

# Install other requirements
pip install -r requirements.txt
```

#### On macOS/Linux:

```bash
# Install Java
sudo apt-get install openjdk-11-jdk  # Linux
brew install openjdk               # macOS

# Install Android SDK and NDK
# Follow: https://buildozer.readthedocs.io/en/latest/quickstart.html

# Install Buildozer
pip install buildozer cython
```

### Step 2: Configure Android SDK

```bash
# Set ANDROID_SDK_ROOT environment variable
# Windows:
set ANDROID_SDK_ROOT=C:\Users\YourUsername\AppData\Local\Android\Sdk

# Linux/macOS:
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$HOME/Android/Sdk/ndk/25.1.8937393
```

## Build Steps

### Step 1: Test on Desktop (Optional but Recommended)

```bash
# Run the Kivy app locally first to verify it works
python trading_app_kivy.py
```

### Step 2: Build Android APK

Navigate to the directory containing `buildozer.spec` and run:

```bash
# First build (will download ~5GB of Android SDK/NDK)
buildozer android debug

# Subsequent builds (faster)
buildozer android debug

# For release APK (requires signing)
buildozer android release
```

**Note:** First build takes 15-30 minutes depending on internet speed.

### Step 3: Find Your APK

After successful build, your APK will be at:
```
./bin/tradingassistant-1.0-debug.apk
```

## Deploy to Phone

### Option A: Direct Installation

```bash
# Connect Android phone via USB with debugging enabled
adb install bin/tradingassistant-1.0-debug.apk
```

### Option B: Manual Installation

1. Copy `tradingassistant-1.0-debug.apk` to your phone
2. Open File Manager on phone
3. Tap the APK file
4. Allow "Unknown Sources" in Settings
5. Install

### Option C: Google Play Store (Release)

For production release:
```bash
# Create signed APK for Play Store
buildozer android release

# Sign with your keystore
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore my-release-key.keystore \
  bin/tradingassistant-1.0-release.apk alias_name
```

## Troubleshooting

### Build Fails - "Java not found"
```bash
# Set JAVA_HOME
set JAVA_HOME=C:\Program Files\Java\jdk-11.0.x
```

### Build Fails - "Android SDK not found"
```bash
# Manually set in buildozer.spec:
android.sdk_path = /path/to/android/sdk
android.ndk_path = /path/to/android/ndk/25.1.8937393
```

### "requirements.txt not found"
```bash
# Make sure requirements.txt is in same directory as buildozer.spec
# Current location: ./requirements.txt
```

### APK Installation Fails on Phone
```bash
# Allow installation from unknown sources:
# Settings > Security > Unknown Sources > Enable

# Or use ADB:
adb install -r bin/tradingassistant-1.0-debug.apk
```

### App Crashes on Phone
```bash
# Check logs via ADB
adb logcat | grep python

# Check error details in Kivy logs
```

## App Permissions

The app requests these Android permissions:
- ✅ `INTERNET` - For downloading stock data from yfinance
- ✅ `ACCESS_NETWORK_STATE` - To check internet connectivity

These are automatically added in `buildozer.spec`.

## Performance Notes

- **Data Download**: 2-10 seconds depending on internet
- **Calculations**: <1 second (same Python code as desktop)
- **Memory Usage**: ~80-120 MB at runtime
- **Disk Space**: ~50 MB app size

## File Structure

```
./
├── trading_app_kivy.py          # Main Kivy app
├── requirements.txt              # Python dependencies
├── buildozer.spec               # Android build config
├── ANDROID_BUILD_GUIDE.md       # This file
└── bin/
    └── tradingassistant-1.0-debug.apk  # Your Android app
```

## Key Features on Android

✅ Real-time stock/ETF analysis
✅ RSI & Stochastic indicators
✅ Trading decision signals
✅ Auto-refresh every 30 seconds
✅ Support for 17+ popular tickers
✅ Works offline (cached data)
✅ No CORS issues

## Next Steps

1. Run `buildozer android debug` to create APK
2. Test on Android phone
3. Customize colors/fonts in `trading_app_kivy.py` if desired
4. Deploy to Google Play or share APK directly

## Support

For Buildozer issues: https://buildozer.readthedocs.io/
For Kivy issues: https://kivy.org/doc/stable/
For yfinance issues: https://github.com/ranaroussi/yfinance

Happy trading! 🚀
