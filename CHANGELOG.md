# Changelog


## [1.1.0] - 2025-12-04

### Added

- **Performance Engine**: Implemented "Eager Pruning" (Hybrid Mode). The tool now uses internal pattern matching to skip massive folders (like `node_modules` or `venv`) *before* asking Git about them. This drastically speeds up scans on large repositories.
- **UX**: Added a CLI spinner animation (`| / - \`) to indicate activity during long scans.
- **UX**: Added graceful handling for `Ctrl+C` (KeyboardInterrupt). The tool now exits cleanly without printing a traceback.
- **Quality**: Added a comprehensive unit test suite in `tests/test_rtree.py` covering flat lists, ASCII generation, and gitignore fallbacks.
- **CI/CD**: Added GitHub Actions workflow (`.github/workflows/test.yml`) to automatically run tests across Python 3.8–3.12 on every push.

## [1.0.0] - 2025-11-20

### Added

- **CLI Support**: Added `setup.py` configuration to install the tool globally via `pip`.
    
- **Command Entry Point**: The tool can now be run using the command `rtree` (or `repotree`) from any terminal location.
    
- **Color Support**: Added ANSI color output (Blue for directories, Green for files, Yellow for configs).
    
- **Depth Control**: Added `--depth` argument to limit recursion levels (useful for large directories like `node_modules`).
    
- **Path Flexibility**: Added support for absolute paths (e.g., `C:\Projects`) and relative paths (e.g., `../sibling`).
    
- **Smart Output**: Automatically disables color codes when the `--out` flag is used to prevent corrupting text files.
    

### Changed

- **Default Behavior**: The `--repo` / `-r` argument is now optional. If omitted, the tool scans the current working directory (`.`).
    
- **Refactoring**: Split visualizer logic to separate `color` handling from `structure` logic.
    
- **Documentation**: Updated README to reflect CLI usage and installation steps.
    

### Fixed

- Fixed issue where writing to files included terminal escape codes (colors).
    
- Fixed limitation where the script could only scan direct subdirectories of the current folder.
    

## [0.1.0] - 2025-11-15 (Legacy Script)

### Added

- Initial release of `tree.py`.
    
- **Git Awareness**: Logic to parse `.gitignore` files and hide ignored content.
    
- **Git Fallback**: Added manual `.gitignore` parsing for environments where `git` is not installed.
    
- **Tree Generation**: Recursive algorithm to draw ASCII trees (`├──`, `└──`).
    
- **Flat Mode**: Added `--flat` argument to output a simple list of file paths.
    
- **Raw Mode**: Added `--raw` argument to bypass ignore rules.
    
- **Output**: Support for printing to stdout or saving to auto-named files.