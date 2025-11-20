# RepoTree Generator (`rtree`)

**RepoTree** is a fast, context-aware Python utility designed to generate plain-text representations of directory structures for Git repositories.

Unlike standard `tree` commands, RepoTree is built for developers. Its primary feature is **context-awareness**: it automatically parses `.gitignore` rules to hide build artifacts, caches, and temporary files, ensuring the output represents only the source code and relevant files.

## Features

- **Git-Aware:** Automatically prioritizes `git check-ignore` to filter files exactly as Git sees them.
    
- **Smart Colors:** Blue for directories, Green for files, Yellow for configs (automatically disabled when writing to files to keep text clean).
    
- **Depth Control:** Limit recursion depth to get a high-level overview of massive projects.
    
- **Fallback Logic:** Includes a manual `.gitignore` parser if Git is not installed or the directory is not initialized.
    
- **Visualization Modes:** Supports visual ASCII trees (`├──`), flat file lists (pre-order traversal), and raw modes.
    
- **Flexible Navigation:** Works with absolute paths, relative paths, or the current directory.
    
- **Zero Dependencies:** Written in pure Python 3.6+ (standard library only).
    

## Installation

To use `rtree` globally from any terminal window, clone the repo and install it using pip.

### 1. Clone & Install (Recommended)

This allows you to keep the source code and makes updating the tool easy.

```bash
# Clone the repository
git clone https://github.com/qtremors/file-tree-generator.git

# Navigate to the project folder
cd file-tree-generator

# Install the CLI in editable mode
pip install -e .
```

_The `-e` flag stands for "editable". It links the global command to your local file, so any changes you make to `tree.py` apply immediately._

### 2. Standalone Usage

If you do not wish to install it, you can simply run the script using Python:

```python
python tree.py [arguments]
```


## Usage & Commands

Once installed, use the command `rtree` . Below are the supported arguments and scenarios.

### Arguments Reference

#### 📍 Navigation & Targets

|**Argument**|**Short**|**Description**|
|---|---|---|
|`--repo`|`-r`|**Target Directory.** Can be relative, absolute, or subdirectory. Defaults to CWD if omitted.|
|`--list`||Scans the current directory and lists all valid Git repositories found.|

#### 🎨 Visualization & Depth

|**Argument**|**Short**|**Description**|
|---|---|---|
|`--depth`||**Depth Limit.** Stop scanning after N levels (e.g., `--depth 2`).|
|`--flat`||**Flat Mode.** Output a flat list of paths instead of a tree.|
|`--ascii`||**Force ASCII.** Force standard tree characters (`├──`) (default behavior).|
|`--raw`||**Raw Mode.** Ignore `.gitignore` rules and show everything (including `.git/` contents).|

#### 💾 Output & Formatting

|**Argument**|**Short**|**Description**|
|---|---|---|
|`--out`|`-o`|**Save to file.** If no filename is given, auto-generates one (e.g., `[repo]_tree.txt`).|
|`--no-color`||**Plain Text.** Disable ANSI colors in the terminal.|

---

### Scenarios & Expected Outputs

#### 1. Standard Tree Visualization

Generates a clean tree, respecting `.gitignore`.

```python
rtree -r my-project
```

**Expected Output:**

```
my-project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── .gitignore
├── .git/
└── README.md
```

_(Note: `__pycache__` or `.env` files are hidden automatically.)_

#### 2. Depth Control (High-Level Overview)

Inspect only the top-level folders.

```python
rtree -r my-project --depth 1
```

#### 3. Flat List Mode

Useful for copying file paths for use in other scripts or LLM prompts.

```python
rtree -r my-project --flat
```

**Expected Output:**

```
.git/
.gitignore
README.md
src/
src/main.py
tests/
```

#### 4. Save to File (Auto-naming)

Saves the output to a file. **Note:** Colors are automatically disabled when saving to files.

```python
rtree -r my-project --out
```

**Console Output:**

```
my-project_ascii_tree.txt
```

#### 5. Raw Mode

Debug mode to see everything, including ignored files, virtual environments, and git internals.

```python
rtree -r my-project --raw
```


## How It Works

The script relies on the `RepoTreeVisualizer` class to handle scanning and filtering.

1. **Initialization:** The script accepts a target repository path (`--repo`). If omitted, it defaults to the current working directory. It immediately locates the `.gitignore` file.
    
2. **Ignore Calculation (`_compute_ignored_set`):**
    
    - **Primary Method:** It attempts to run `git check-ignore --stdin` via Python's `subprocess` module. This ensures 100% parity with Git behavior.
        
    - **Secondary Method (Fallback):** If Git is missing, it falls back to `_simple_gitignore_match`. It compiles patterns using `fnmatch` to approximate Git's matching rules.
        
3. **Traversal:**
    
    - It uses `os.walk` to traverse the directory.
        
    - **Depth Logic:** If `--depth` is set, it stops recursion when the specified level is reached.
        
    - **Filtering:** For every file/folder, it checks against the computed `ignored_set`. Special care is taken to always show the root `.gitignore` and `.git` folder.
        
4. **Rendering:**
    
    - **ASCII Tree:** Uses a recursive function to draw `├──`, `│`, and `└──` characters.
        
    - **Color Logic:** Wraps strings in ANSI escape codes (e.g., `\033[94m` for directories) unless `--no-color` or `--out` is used.
        


## Commands

```python
    # --- Basic Usage ---
    # Scan the current directory
    rtree
    python tree.py

    # Scan a specific subdirectory
    rtree -r my-project
    python tree.py -r my-project

    # Scan an absolute path
    rtree -r "C:/Projects/App"
    python tree.py -r "C:/Projects/App"

    # --- Depth Control ---
    # Limit tree to 2 levels deep (great for large repos)
    rtree --depth 2
    python tree.py --depth 2

    # Combine specific target with depth limit
    rtree -r src --depth 3
    python tree.py -r src --depth 3

    # --- Output to File ---
    # Auto-name the output file (e.g., 'folder_tree.txt')
    rtree -o
    python tree.py -o

    # Save to a specific filename
    rtree -o structure.txt
    python tree.py -o structure.txt

    # Scan 'src' and save to 'src.txt'
    rtree -r src -o src.txt
    python tree.py -r src -o src.txt

    # --- Flat List Mode ---
    # Output a flat list of file paths instead of a tree
    rtree --flat
    python tree.py --flat

    # Save the flat list to a file
    rtree --flat -o list.txt
    python tree.py --flat -o list.txt

    # --- Raw / Debug Mode ---
    # Ignore .gitignore rules (shows .git, venv, etc.)
    rtree --raw
    python tree.py --raw

    # See top-level hidden files only
    rtree --raw --depth 1
    python tree.py --raw --depth 1

    # Flat list of every file on disk (ignoring rules)
    rtree --raw --flat
    python tree.py --raw --flat

    # --- Utilities ---
    # List all git repositories found in the current directory
    rtree --list
    python tree.py --list

    # Force disable colored output in the terminal
    rtree --no-color
    python tree.py --no-color
```


## Prerequisites

- **Python 3.6+** (Uses `typing` and `pathlib` logic).
    
- **Git** (Recommended for most accurate ignore-checking, but not strictly required due to fallback logic).
    


## Troubleshooting

- **"Command not found":** Ensure you ran `pip install -e .` inside the folder. If it still fails, make sure your Python `Scripts/` (Windows) or `bin/` (Mac/Linux) folder is in your system PATH.
    
- **Error: 'repo' not found:** Ensure the directory you provide via `--repo` exists.
    
- **Git ignore not working:** If `git` is not in your system PATH, the script relies on Python matching. Complex gitignore patterns (like negation `!`) might not be perfectly emulated in the fallback mode.
    
- **Colors look weird in output files:** The script auto-detects when you use `--out` and disables colors. If you pipe output manually (e.g., `rtree > file.txt`), use the `--no-color` flag to prevent garbage characters.
    

---
