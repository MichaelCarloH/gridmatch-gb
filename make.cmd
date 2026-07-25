@echo off
where mingw32-make >nul 2>nul
if errorlevel 1 (
  echo GNU Make was not found. Install it or run the target command shown in Makefile.
  exit /b 1
)
mingw32-make PYTHON="py -3" %*
