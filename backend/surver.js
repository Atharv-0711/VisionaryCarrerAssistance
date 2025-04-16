// backend/server.js
const express = require('express');
const cors = require('cors');
const XLSX = require('xlsx');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

// Direct path to existing Excel file
const FILE_PATH = path.join(__dirname, 'childsurvey.xlsx');

// Helper function to ensure file exists
const checkFile = () => {
  if (!fs.existsSync(FILE_PATH)) {
    throw new Error('childsurvey.xlsx not found in backend directory');
  }
};

app.post('/api/submit-survey', async (req, res) => {
  try {
    checkFile();
    
    // Load existing workbook
    const workbook = XLSX.readFile(FILE_PATH);
    
    // Get first worksheet (modify if using specific sheet name)
    const worksheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[worksheetName];
    
    // Convert worksheet to JSON
    const existingData = XLSX.utils.sheet_to_json(worksheet);
    
    // Add new entry with timestamp
    const newEntry = {
      Timestamp: new Date().toISOString(),
      ...req.body
    };
    
    // Append new data
    const updatedData = [...existingData, newEntry];
    const newWorksheet = XLSX.utils.json_to_sheet(updatedData);
    
    // Update workbook and save
    workbook.Sheets[worksheetName] = newWorksheet;
    XLSX.writeFile(workbook, FILE_PATH);
    
    res.status(200).json({ message: 'Survey saved successfully' });
  } catch (error) {
    console.error('Error saving survey:', error);
    res.status(500).json({ 
      error: error.message || 'Failed to save survey',
      note: 'Ensure the Excel file is closed during submissions'
    });
  }
});

app.listen(5000, () => console.log('Server running on port 5000'));