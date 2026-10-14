"""SQLite library lending lab: database, terminal interface and analysis."""
import os
import sys

# Windows redirected terminals may default to cp1252, which cannot print Vietnamese.
# Do not replace notebook streams or change Unix locale configuration.
if os.name == 'nt':
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
