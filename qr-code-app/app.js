const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bodyParser = require('body-parser');

const app = express();
const db = new sqlite3.Database('./qr-codes.db');

app.use(express.static('public'));
app.use(bodyParser.json());

app.post('/scan', (req, res) => {
  const qrData = req.body.data;

  db.run("INSERT INTO qr_codes (data) VALUES (?)", [qrData], (err) => {
    if (err) {
      return res.status(500).send('Error saving to database');
    }
    res.send('QR code data saved: ' + qrData);
  });
});

app.get('/data', (req, res) => {
  db.all("SELECT * FROM qr_codes", [], (err, rows) => {
    if (err) {
      return res.status(500).send('Error retrieving data');
    }
    res.json(rows);
  });
});

app.listen(3000, () => {
  console.log('Server started on http://localhost:3000');
});