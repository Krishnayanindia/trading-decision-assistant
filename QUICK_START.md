# Quick Start - Android App in 5 Minutes

## Option 1: Test on Your Computer First (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app on desktop to verify it works
python trading_app_kivy.py
```

## Option 2: Build Android APK (Takes 20-30 minutes)

### Windows Users:

```bash
# Install Buildozer (one-time)
pip install buildozer cython

# Build the APK (in the same directory as buildozer.spec)
cd /path/to/project
buildozer android debug

# APK will be at: bin/tradingassistant-1.0-debug.apk
```

### macOS/Linux Users:

```bash
# Install dependencies
pip install buildozer cython
brew install openjdk  # macOS only

# Build
buildozer android debug
```

## Option 3: Run on Android Emulator

```bash
# If you have Android Studio installed
buildozer android debug
buildozer android debug -- logcat

# Then in another terminal:
adb install bin/tradingassistant-1.0-debug.apk
```

## What You Get

✅ **Exact same app** as your Python version
✅ **No CORS issues** - runs natively on Android
✅ **All features included**:
   - RSI & Stochastic analysis
   - Real-time data from Yahoo Finance
   - 17+ pre-loaded stock/ETF symbols
   - Auto-refresh every 30 seconds
   - Beautiful mobile UI

## Common Issues & Fixes

**"buildozer not found"**
```bash
pip install buildozer --upgrade
```

**"Java not found"**
- Download JDK: https://www.oracle.com/java/technologies/downloads/
- Set JAVA_HOME environment variable

**"First build taking too long?"**
- First build downloads ~5GB of Android SDK
- Subsequent builds are much faster
- This is normal - be patient!

**"APK won't install"**
```bash
# Try with -r flag to replace existing
adb install -r bin/tradingassistant-1.0-debug.apk

# Or enable "Unknown Sources" in phone Settings > Security
```

## That's It! 🎉

Your Android trading app is ready. The Python code runs exactly the same way - no rewrites needed, no CORS issues!

For detailed setup: See `ANDROID_BUILD_GUIDE.md`
