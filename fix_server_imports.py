# This file is needed to ensure all server-related modules are properly imported
# and included in the PyInstaller bundle

# Import all server-related modules to ensure they're included in the build
import realtime_analysis
import dash
import dash_bootstrap_components as dbc
import plotly
import flask

# This is a dummy function that won't be called, but ensures the imports are included
def _include_server_dependencies():
    return (dash, dbc, plotly, flask)
