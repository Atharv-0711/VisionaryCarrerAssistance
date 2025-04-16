// backend/submitSurvey.js (Express route example)
const express = require('express');
const router = express.Router();
const xl = require('excel4node');
const fs = require('fs');
const Sentiment = require('sentiment');
const sentiment = new Sentiment();

router.post('/submit-survey', async (req, res) => {
  try {
    const data = req.body;

    // Add sentiment score for "Behavioral Impact"
    const score = sentiment.analyze(data["Behavioral Impact"]).score;
    data["Score"] = score;

    // Read or create Excel file
    const filePath = './Childsurvey.xlsx';
    let wb, ws, row = 2;

    if (fs.existsSync(filePath)) {
      wb = new xl.Workbook();
      ws = wb.addWorksheet('Sheet 1');
      // Load existing data and find next row
      const existingData = require('xlsx').readFile(filePath);
      const sheet = existingData.Sheets[existingData.SheetNames[0]];
      row = Object.keys(sheet).filter(key => key.match(/^[A-Z]+1$/)).length + 1;
    } else {
      wb = new xl.Workbook();
      ws = wb.addWorksheet('Sheet 1');
      // Write headers
      const headers = [
        'Name of Child',
        'Age',
        'Class (बच्चे की कक्षा)',
        'Background of the Child',
        'Problems in Home',
        'Behavioral Impact',
        'Academic Performance',
        'Family Income',
        'Role models',
        'Reason for such role model',
        'Score'
      ];
      headers.forEach((header, index) => {
        ws.cell(1, index + 1).string(header);
      });
    }

    // Write new data
    const fields = [
      'Name of Child ',
      'Age',
      'Class (बच्चे की कक्षा)',
      'Background of the Child ',
      'Problems in Home ',
      'Behavioral Impact',
      'Academic Performance ',
      'Family Income ',
      'Role models',
      'Reason for such role model ',
      'Score'
    ];

    fields.forEach((field, index) => {
      if (field === 'Score') {
        ws.cell(row, index + 1).number(data[field]);
      } else {
        ws.cell(row, index + 1).string(data[field].toString());
      }
    });

    wb.write(filePath, (err) => {
      if (err) {
        console.error('Error writing to Excel:', err);
        return res.status(500).json({ error: 'Failed to save Excel' });
      }
      res.json({ success: true });
    });
  } catch (err) {
    console.error('Server error:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
