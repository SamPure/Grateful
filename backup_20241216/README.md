# Daily Gratitude Tracker

## Overview
A web application for tracking daily gratitude with SMS reminders. This application helps users maintain a daily practice of gratitude by allowing them to log what they're grateful for and receiving daily SMS reminders.

## Features
- User Registration & Authentication
- Daily Gratitude Logging
- Chronological Display of Past Entries
- SMS Reminders (coming soon)
- Modern, Responsive UI with Tailwind CSS

## Tech Stack
- Backend: Python (Flask)
- Database: SQLite with SQLAlchemy
- Authentication: Flask-Login
- Frontend: HTML, Tailwind CSS
- SMS Integration: Twilio (planned)

## Setup Instructions
1. Clone the repository
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python3 app.py
   ```
4. Access the application at http://localhost:5011

## Project Structure
```
.
├── app.py              # Main Flask application
├── gratitude.db        # SQLite database
├── requirements.txt    # Python dependencies
└── templates/         
    ├── index.html     # Dashboard template
    ├── login.html     # Login page
    └── register.html  # Registration page
```

## Database Schema
### Users Table
- id (PRIMARY KEY)
- email (UNIQUE)
- password (hashed)
- phone_number

### Gratitude Entries Table
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- message
- timestamp

## Last Backup
- Date: 2024-12-16
- Time: 20:16:43 EST
