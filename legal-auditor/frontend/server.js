const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from the current directory
app.use(express.static(__dirname));

// For SPA: send index.html for any request that doesn't match a file
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`
  🚀 LegalShield AI Frontend Server Running
  -----------------------------------------
  URL: http://localhost:${PORT}
  Mode: Production
  Directory: ${__dirname}
  -----------------------------------------
  `);
});
