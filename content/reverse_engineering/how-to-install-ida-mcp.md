Title: How to Install IDA Pro MCP
Date: 2026-3-19 11:35:42
Modified: 2026-3-19 11:35:42
Category: Reverse Engineering
Tags: IDA,MCP
Slug: how-to-install-ida-mcp
Figure: idapro.png
Summary: ipatool is a command line tool that allows you to search for iOS apps on the App Store and download a copy of the app package, known as an ipa file.

## Choose idapython version
```bash
/Applications/IDA Professional 9.2.app/Contents/MacOS
./idapyswitch
The following Python installations were found:
    #0: 3.14.0 ('') (/opt/homebrew/Cellar/python@3.14/3.14.0/Frameworks/Python.framework/Versions/3.14/Python)
    #1: 3.13.0 ('') (/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/Python)
    #2: 3.12.0 ('') (/Library/Frameworks/Python.framework/Versions/3.12/Python)
    #3: 3.9.0 ('') (/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Python3)
    #4: 3.9.0 ('') (/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Python3)
Please pick a number between 0 and 4 (default: 0)
1
Applying version 3.13.0 ('')
```

```bash
/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/bin/pip3.13
/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/bin/pip3.13 \
  install --break-system-packages \
  https://github.com/mrexodia/ida-pro-mcp/archive/refs/heads/main.zip

/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/bin/pip3.13 \
  install --user \
  https://github.com/mrexodia/ida-pro-mcp/archive/refs/heads/main.zip
```