# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "Costa"
copyright = "2021, Gregor Strugala"
author = "Gregor Strugala"

# The full version, including alpha/beta/rc tags
release = "0.0.1"


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "IPython.sphinxext.ipython_directive",
    "IPython.sphinxext.ipython_console_highlighting",
    "matplotlib.sphinxext.plot_directive"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Omit parentheses in functions/methods cross-references
add_function_parentheses = False


# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_theme_options = {
    'logo': "logo.pdf",
    'show_relbar_bottom': True,
    'github_button': True,
    'github_user': "gstrugala",
    'github_repo': "costa",
    'description': "Impute missing values in a performance table"
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {
    'python': ("https://docs.python.org/3", None),
    'numpy': ("https://numpy.org/doc/stable/", None),
    'pandas': ("https://pandas.pydata.org/pandas-docs/stable", None)
}


# -- Matplotlib plot directive configuration ---------------------------------
plot_html_show_source_link = False
plot_html_show_formats = False
