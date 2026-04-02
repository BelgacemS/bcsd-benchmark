# Constantes partagees entre les scrapers (langages cibles, extensions, dossiers)

# Mapping langage -> dossier + extension (pour atcoder)
LANG_MAP = {
    "C":    {"folder": "C",    "ext": ".c"},
    "C++":  {"folder": "Cpp",  "ext": ".cpp"},
    "Rust": {"folder": "Rust", "ext": ".rs"},
    "Go":   {"folder": "Go",   "ext": ".go"},
}

# Nom du langage -> nom du dossier (pour rosetta)
LANG_DIRS = {
    "C": "C",
    "C++": "Cpp",
    "Rust": "Rust",
    "Go": "Go",
}

# Nom du langage -> extension (pour rosetta)
EXT_MAP = {
    "C": ".c",
    "C++": ".cpp",
    "Rust": ".rs",
    "Go": ".go",
}
