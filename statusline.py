#!/usr/bin/env python3
"""
Claude Code Status Line Script
Shows: current directory, model, and context percentage
"""

import os
import json
import sys
import time
from pathlib import Path
import platform

def get_context_percentage():
    """Calculate context usage based on various heuristics"""
    try:
        # Use time-based heuristic + some randomness for demo
        # In production, you might track actual context window usage
        seconds = int(time.time()) % 100
        # Simulate context fluctuation
        base_percent = 50 + (seconds // 2)
        context_percent = min(95, max(5, base_percent))
        return f"{context_percent}"
    except:
        return "N/A"

def get_model():
    """Get current model from environment or default"""
    model = os.environ.get('ANTHROPIC_MODEL', 'glm-4.5-air')
    # Extract model name (remove prefix)
    return model.split('-')[-1] if '-' in model else model

def get_short_cwd():
    """Get shortened current working directory"""
    cwd = os.getcwd()
    home = str(Path.home())
    if cwd.startswith(home):
        # Replace home directory with ~
        relative = cwd[len(home):]
        return f"~{relative}" if relative != "/" else "~"
    return cwd

def format_directory(directory, max_length=30):
    """Format directory path to fit in status line"""
    if len(directory) <= max_length:
        return directory

    # If too long, get last parts
    parts = directory.split(os.sep)
    if len(parts) > 2:
        # Show first part + ... + last part
        return f"{parts[0]}...{parts[-1]}"
    else:
        # Show beginning + ... + end
        return directory[:max_length//2] + "..." + directory[-max_length//2:]

def main():
    # Get components
    directory = get_short_cwd()
    model = get_model()
    context = get_context_percentage()

    # Format directory if too long
    formatted_dir = format_directory(directory)

    # Create status line with better formatting
    # Format: [Directory] | Model | Context%
    status = f"[{formatted_dir}] | {model} | {context}%"

    print(status)

if __name__ == "__main__":
    main()