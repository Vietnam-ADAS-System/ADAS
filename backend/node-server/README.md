# Node.js Backend Server

Express.js server that handles API requests from frontend and communicates with Python AI Service.

## Routes

- `POST /upload-video` - Upload video file
- `POST /detect` - Vehicle detection
- `POST /segment` - Lane segmentation  
- `POST /warning` - ADAS warning system

## Structure

- `routes/` - API endpoint definitions
- `controllers/` - Request handlers
- `services/` - Business logic and calls to Python AI Service
- `middleware/` - Authentication, file upload handling, etc.
- `uploads/` - User uploaded videos

## Installation

```bash
npm install
npm start
```
