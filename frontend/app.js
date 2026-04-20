const express = require('express');
const axios = require('axios');
const path = require('path');

const app = express();
const API_URL = process.env.API_URL || "http://api:8000";        
const PORT = parseInt(process.env.PORT || "3000", 10);           

app.use(express.json());


app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.use(express.static(path.join(__dirname, 'views')));

app.post('/submit', async (req, res) => {
  try {
    const response = await axios.post(`${API_URL}/jobs`);
    res.json(response.data);
  } catch (err) {
    
    const status = err.response?.status || 500;
    const message = err.response?.data?.detail || err.message || "Internal server error";
    res.status(status).json({ error: message });
  }
});

app.get('/status/:id', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/jobs/${req.params.id}`);
    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 500;
    const message = err.response?.data?.detail || err.message || "Internal server error";
    res.status(status).json({ error: message });
  }
});

app.listen(PORT, () => {                                          // ✅ FIX 12
  console.log(`Frontend running on port ${PORT}`);
});
