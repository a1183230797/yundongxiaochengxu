# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Pomodoro Clock application with a graphical user interface built using tkinter. The application helps users implement the Pomodoro Technique for time management, featuring work/break cycles, task management, and statistics tracking.

## Development Commands

### Running the Application
```bash
# Run the Pomodoro Clock
python pomodoro_clock.py
```

### Running the Statusline
```bash
# Test the statusline script
python statusline.py
```

## Architecture

### Core Components

1. **PomodoroClock Class (`pomodoro_clock.py`)**
   - Main application class handling UI and logic
   - Manages three modes: work, short_break, long_break
   - Uses threading for non-blocking timer operations
   - Implements settings persistence via JSON file

2. **Statusline Script (`statusline.py`)**
   - Standalone Python script for Claude Code status line
   - Displays current directory, model name, and context percentage
   - Uses environment variables for model configuration

### Key Architecture Patterns

- **Threading**: Timer operations run in a separate daemon thread to prevent UI blocking
- **Settings Management**: JSON-based configuration with merge functionality
- **Event Handling**: Proper cleanup of event handlers to prevent memory leaks
- **UI State Management**: Caching of display values to minimize unnecessary updates

### Critical Methods

- `timer_thread()`: Core timer logic running in background thread
- `timer_finished()`: Handles timer completion and mode transitions
- `create_widgets()`: Constructs the complete UI layout
- `load_settings()` / `save_settings()`: Settings persistence
- `update_time_display()`: UI update with change detection

### Data Flow

1. **Settings**: Loaded from `pomodoro_settings.json` or defaults
2. **Timer State**: Managed via `is_running`, `is_paused`, `time_left`
3. **Statistics**: Tracked in `total_work_time` and `pomodoro_count`
4. **Task List**: Simple listbox with completion tracking

### Configuration

- **Default Settings**: 25-minute work, 5-minute short break, 15-minute long break
- **Auto-start**: Optional automatic transition between work/break
- **Sound Alerts**: System beep notification on completion
- **Theme**: Light/dark theme support (UI elements present but theme switching not fully implemented)

## File Structure

```
D:\AI\cursor\
├── pomodoro_clock.py      # Main application (530 lines)
├── statusline.py         # Status line script
└── pomodoro_settings.json # User settings (created at runtime)
```

## Important Implementation Notes

1. **Windows Compatibility**: Uses ASCII characters instead of emojis for proper display on Windows systems
2. **Unicode Encoding**: Explicit UTF-8 encoding for JSON files
3. **Memory Management**: Proper cleanup of event handlers and window instances
4. **Thread Safety**: UI updates use `root.after()` for thread-safe operations
5. **Auto-start Feature**: Optional automatic progression between work/break cycles

## Dependencies

- Standard library only: `tkinter`, `threading`, `time`, `json`, `os`, `pathlib`, `logging`
- No external package dependencies - pure Python implementation