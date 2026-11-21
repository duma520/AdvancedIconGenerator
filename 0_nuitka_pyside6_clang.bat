nuitka --standalone ^
    --enable-plugin=pyside6 ^
    --enable-plugin=tk-inter ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=icon.ico ^
    --include-data-files=icon.ico=icon.ico ^
    --include-package=PySide6 ^
    --include-package=PIL ^
    --include-package=numpy ^
    --include-package=matplotlib ^
    --include-module=cairosvg ^
    --include-module=emoji ^
    --follow-imports ^
    --nofollow-import-to=cupy ^
    --disable-plugin=anti-bloat ^
    --jobs=4 ^
    --clang ^
    --output-dir=build_output ^
    AdvancedIconGenerator.py

