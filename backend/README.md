# Visionary Career Assistance

A comprehensive application for analyzing children's career development based on various factors including educational background, behavioral patterns, role models, and family income.

## Project Structure

```
visionary-career-assistance/
├── frontend/               # React frontend application
│   ├── src/                # Source code
│   │   ├── pages/          # React components
│   │   ├── App.tsx         # Main application component
│   │   └── index.tsx       # Entry point
│   └── package.json        # Frontend dependencies
├── backend/                # Python backend application
│   ├── app.py              # Flask server
│   ├── requirements.txt    # Backend dependencies
│   └── *.py                # Analysis modules
└── README.md               # This file
```

## Setup and Installation

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the Flask server:
   ```
   python app.py
   ```

   The server will start on http://localhost:5000

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

   The application will open in your browser at http://localhost:3000

## Features

- **Background Analysis**: Analyze educational background and family income patterns
- **Behavioral Impact Analysis**: Understand behavioral patterns and their influence
- **Role Model Analysis**: Examine role model influence and traits
- **Career Insights**: Get personalized career recommendations

## API Endpoints

- `GET /api/health`: Check if the server is running
- `GET /api/analysis/background`: Get background analysis
- `GET /api/analysis/behavioral`: Get behavioral impact analysis
- `GET /api/analysis/rolemodel`: Get role model analysis
- `GET /api/analysis/income`: Get family income analysis
- `GET /api/analysis/complete`: Get all analyses at once

## Technologies Used

- **Frontend**: React, TypeScript, Material-UI, Axios
- **Backend**: Flask, Pandas, NumPy, Matplotlib, Seaborn, TextBlob 