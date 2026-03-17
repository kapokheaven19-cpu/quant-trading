const http = require('http');
const { exec } = require('child_process');
const url = require('url');

const PORT = 3000;

const AGENT_MAP = {
  'echo': { id: 'echo', name: 'Echo' },
  'pm': { id: 'pm', name: 'PM Agent' },
  'genius-coder': { id: 'genius-coder', name: '天才Coder' },
  'calendar': { id: 'calendar', name: '日程助手' }
};

async function callAgent(agentId, message) {
  return new Promise((resolve, reject) => {
    const cmd = `openclaw agent --agent ${agentId} -m "${message.replace(/"/g, '\\"')}" --json`;
    
    exec(cmd, { timeout: 120000 }, (error, stdout, stderr) => {
      if (error) {
        reject(error);
        return;
      }
      
      try {
        // Try to parse JSON output
        const lines = stdout.trim().split('\n');
        const jsonLine = lines.find(line => {
          try {
            return JSON.parse(line);
          } catch {
            return false;
          }
        });
        
        if (jsonLine) {
          resolve(JSON.parse(jsonLine));
        } else {
          // Return raw output if no JSON
          resolve({ response: stdout || stderr });
        }
      } catch (e) {
        resolve({ response: stdout || stderr });
      }
    });
  });
}

// 提取 <text> 标签内容
function extractTextContent(response) {
  if (!response) return '';
  
  // 尝试匹配 <text>...</text> 标签内容
  const textMatch = response.match(/<text>([\s\S]*?)<\/text>/);
  if (textMatch) {
    return textMatch[1].trim();
  }
  
  // 如果没有 text 标签，返回原始内容
  return response;
}

const server = http.createServer(async (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  const parsedUrl = url.parse(req.url, true);
  
  // API: Get available agents
  if (parsedUrl.pathname === '/api/agents' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(AGENT_MAP));
    return;
  }
  
  // API: Send message to agent
  if (parsedUrl.pathname === '/api/chat' && req.method === 'POST') {
    let body = '';
    
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    req.on('end', async () => {
      try {
        const { agentId, message } = JSON.parse(body);
        
        if (!agentId || !message) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Missing agentId or message' }));
          return;
        }
        
        const result = await callAgent(agentId, message);
        
        // 提取 <text> 标签内容
        const textContent = extractTextContent(result.response);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, result: { response: textContent } }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
    
    return;
  }
  
  // Serve static files from parent directory
  if (parsedUrl.pathname === '/' || parsedUrl.pathname === '/dashboard') {
    const fs = require('fs');
    const path = require('path');
    const dashboardPath = path.join(__dirname, '..', 'docs', 'dashboard.html');
    
    fs.readFile(dashboardPath, (err, data) => {
      if (err) {
        res.writeHead(500);
        res.end('Error loading dashboard');
        return;
      }
      
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(data);
    });
    return;
  }
  
  res.writeHead(404);
  res.end('Not found');
});

server.listen(PORT, () => {
  console.log(`Agent Chat API Server running on http://localhost:${PORT}`);
  console.log(`Dashboard: http://localhost:${PORT}/dashboard`);
});
