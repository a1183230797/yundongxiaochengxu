# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a Python-based Pomodoro Clock application. The project consists of two main Python files:
- `pomodoro_clock.py` - The main application file with complete implementation
- `pomodoro_clock_注释版.py` - A version with Chinese comments for reference

The application implements the Pomodoro technique for time management with features including:
- Work sessions, short breaks, and long breaks
- Configurable timers and intervals
- Task management functionality
- Progress tracking and statistics
- Settings persistence in JSON format
- Auto-start capabilities for sessions

## Running the Application

To run the Pomodoro Clock application:

```bash
# Run the main application
python pomodoro_clock.py

# Or run the commented version
python pomodoro_clock_注释版.py
```

The application uses tkinter for the GUI and requires Python 3.x with tkinter support.

## Code Structure

### Main Class: `PomodoroClock`

The application is built around the `PomodoroClock` class which handles:

#### Core Functionality
- **Timer Management**: Start, pause, reset, and auto-start functionality
- **Mode Switching**: Automatic transitions between work, short break, and long break modes
- **Settings Management**: Load/save configuration from `pomodoro_settings.json`
- **Task Management**: Add and mark tasks as completed
- **Statistics Tracking**: Total work time and completed pomodoros

#### Key Methods
- `create_widgets()` - Builds the UI layout with time display, controls, progress bar, and task list
- `timer_thread()` - Background thread for timer counting
- `timer_finished()` - Handles session completion and mode transitions
- `open_settings()` - Opens settings modal with customizable parameters
- `save_settings()` - Persists settings to JSON file in background thread

#### UI Components
- Time display (MM:SS format)
- Control buttons (Start/Pause, Reset, Settings)
- Progress bar showing session progress
- Task list with add/complete functionality
- Quick timer buttons (25min work, 5min break, 15min break)
- Statistics display for daily tracking

### Configuration

Settings are stored in `pomodoro_settings.json` and include:
- Work duration (default: 25 minutes)
- Short break duration (default: 5 minutes)
- Long break duration (default: 15 minutes)
- Long break interval (default: 4 pomodoros)
- Auto-start break after work
- Auto-start work after break
- Sound notifications
- Theme preference

## Development Notes

- The application uses threading for non-blocking timer operations
- UI updates are scheduled with `root.after()` for thread safety
- Settings are saved asynchronously to prevent UI freezing
- Event handlers are tracked and cleaned up to prevent memory leaks
- The code includes Chinese language support for the interface

## Testing

Manual testing is the primary verification method. Key scenarios to test:
- Timer start/pause/reset functionality
- Mode transitions (work → break → work)
- Settings persistence across sessions
- Task management add/complete operations
- Progress bar accuracy
- Statistics tracking updates

## File Dependencies

- `pomodoro_settings.json` - Created automatically for user preferences
- No external Python packages required (uses standard library only)