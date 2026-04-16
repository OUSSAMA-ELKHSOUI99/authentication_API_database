## when testing on physical device using USB and PC and phone on different network:
run : /c/Android/Sdk/platform-tools/adb reverse tcp:8000 tcp:8000 to open a tunnel to test the API
when you are completely finished testing for the day , run : ../adb reverse --remove tcp:8000, or unplug the USB cable will do.