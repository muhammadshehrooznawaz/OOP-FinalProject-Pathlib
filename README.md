# OOP Final Project — pathlib Library Analysis

## BS Data Science | 2nd Semester | Object-Oriented Programming

---

## Group Members

* **Muhammad Shehrooz Nawaz** _ F25BDATS1M02066 
* **Muhammad Ibadullah Bhutta** _ F25BDATS1M02070 
* **Shahzaib Asif** _ F25BDATS1M02073 

---


## Youtube video link of presentation
https://youtu.be/yit5EDWA1tw?si=OXnaVfI0OGQGlmgb

---


## Library Chosen: pathlib

pathlib is a Python **standard library** module (Python 3.4+) that provides an object-oriented interface for filesystem path manipulation. Instead of string-based os.path operations, pathlib wraps every path in a class hierarchy that cleanly demonstrates four core OOP principles.

---

## Project Description

This project performs an in-depth Object-Oriented Design (OOD) analysis of Python's pathlib module. We:

1. **Mapped the full class hierarchy** — from object → PurePath → Path → platform-specific subclasses
2. **Identified all four OOP principles** with real code examples from the library source
3. **Critiqued the design** of the PurePath/Path split (pure vs. I/O operations)
4. **Compared pathlib to the os.path module** (the functional alternative)
5. **Built SmartPath** — our own subclass of Path that adds data-science-friendly features

---

## Repository Structure

```
/
├── README.md                        ← you are here
├── report/
│   └── OOP_Final_Project_Report.docx   ← full written report (PDF also included)
├── code/
│   └── smart_path.py               ← custom SmartPath extension + OOP demos
└── diagrams/
    └── class_hierarchy.html        ← UML-style class hierarchy diagram (open in browser)
```

---

## Custom Extension: SmartPath

SmartPath subclasses pathlib.Path and adds:

| Method | What it does |
|--------|-------------|
| checksum(algorithm) | Computes MD5 / SHA256 / SHA1 hash of a file |
| word_count() | Returns {chars, words, lines} for text files |
| metadata() | Returns a complete JSON-ready metadata dict |
| safe_copy(dest) | Copies file, auto-resolves name collisions |
| backup(backup_dir) | Creates a timestamped backup of a file |
| find_duplicates() | Scans a directory tree for duplicate files by content |
| to_dict() | Serialises path info to a JSON-ready dictionary |

---

## How to Run

No installation required — pathlib is part of the Python standard library.

```bash
# Clone the repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# Run the demo (Python 3.9+ required)
python3 code/smart_path.py
```

Expected output shows all four OOP principles demonstrated and all SmartPath features in action.

---

## Key OOP Concepts Demonstrated

- **Inheritance** — SmartPath → Path → PurePath → object
- **Encapsulation** — internal _require_file() guard; all low-level os calls hidden
- **Polymorphism** — describe_path() works on any PurePath subclass; __truediv__ overridden
- **Abstraction** — users never call os.stat(), open(), or scandir() directly

---
