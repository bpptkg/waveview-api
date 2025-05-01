import os
import sys

sys.path.insert(0, os.path.abspath(".."))


project = "WaveView"
copyright = "(c) 2024, WaveView Developers"
author = "WaveView Developers"

release = "0.2.0"

extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.mathjax",
]

autosectionlabel_prefix_document = True

templates_path = ["_templates"]

source_suffix = ".rst"

master_doc = "index"

language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

pygments_style = "sphinx"

html_theme = "sphinx_rtd_theme"

html_favicon = "waveview.svg"
