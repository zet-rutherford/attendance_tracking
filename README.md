# Facial Attendance Tracking System

A comprehensive attendance tracking system featuring facial recognition with anti-spoofing capabilities, built with Flutter, Flask, PostgreSQL, and Redis.
## Features

### Face Recognition & Security
- Secure check-in using facial recognition technology
- Advanced face anti-spoofing detection to prevent fraud
- Location-based verification ensuring employees are at company premises
- Secure face registration with anti-spoofing validation

### Attendance Management
- Track daily attendance records
- Manage working days and schedules
- Generate attendance reports
- Monitor check-in/check-out times

## System Architecture

### Mobile Application (Flutter)
- User-friendly Android interface
- Real-time face capture and verification
- Location services integration
- Attendance status dashboard

### Backend Service (Flask + PostgreSQL)
- RESTful API for attendance management
- Secure user authentication
- Data persistence with PostgreSQL
- Attendance records management

### Facial Recognition Service (Flask)
- Face matching algorithms
- Anti-spoofing detection
- Real-time face verification
- Secure face template storage

## Prerequisites

- Python 3.8 or higher
- Flutter SDK
- PostgreSQL 12 or higher
- Android Studio
- Required Python packages (specified in requirements.txt)

## Installation

1. Clone the repository
```bash
[git clone https://github.com/yourusername/attendance-tracking-system.git](https://github.com/zet-rutherford/attendance_tracking.git)
cd attendance-tracking-system
```

2. Start the Facial Recognition Service
```bash
cd facial-service
sh run.sh
```

3. Start the Backend Service
```bash
cd backend-flask
sh run.sh
```

4. Set up the Flutter application
```bash
cd frontend-flutter
flutter pub get
flutter run
```

## Configuration

### Backend Configuration
Create a `.env` file in the `backend-flask` directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=attendance_db
DB_USER=your_username
DB_PASSWORD=your_password
```

## Screenshots
<div align="center">
<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/01343fd6-ca5d-4c99-b61f-7525ce0ed061" width="180"/></td>
    <td><img src="https://github.com/user-attachments/assets/f8eda4bb-9ca2-4fcb-bea5-206a315501a1" width="180"/></td>
    <td><img src="https://github.com/user-attachments/assets/4dccc398-8ff8-4ed7-b7eb-9d5784b66374" width="180"/></td>
    <td><img src="https://github.com/user-attachments/assets/c788a128-3b9c-4cd4-9fec-645e249b5a69" width="180"/></td>
    <td><img src="https://github.com/user-attachments/assets/e3dceee3-a917-43d6-a509-d48ca63ede06" width="180"/></td>
    <td><img src="https://github.com/user-attachments/assets/a8e85230-ca93-4e20-af7b-c934272eb714" width="180"/></td>
  </tr>
</table>
</div>

## Support

For support, please email quangming.vision@gmail.com or open an issue in the GitHub repository.
