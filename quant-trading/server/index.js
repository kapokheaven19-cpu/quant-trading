const http = require('http');
const { exec } = require('child_process');
const url = require('url');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const WORKFLOW_FILE = path.join(__dirname, '..', 'workflows.json');

const AGENT_MAP = {
  'echo': { id: 'echo', name: 'Echo' },
  'pm': { id: 'pm', name: 'PM Agent' },
  'genius-coder': { id: 'genius-coder', name: '天才Coder' },
  'calendar': { id: 'calendar', name: '日程助手' }
};

// 确保 workflows 文件存在
function ensureWorkflowFile() {
  if (!fs.existsSync(WORKFLOW_FILE)) {
    fs.writeFileSync(WORKFLOW_FILE, JSON.stringify({ workflows: [] }, null, 2));
  }
}

function loadWorkflows() {
  ensureWorkflowFile();
  return JSON.parse(fs.readFileSync(WORKFLOW_FILE, 'utf-8'));
}

function saveWorkflows(data) {
  fs.writeFileSync(WORKFLOW_FILE, JSON.stringify(data, null, 2));
}

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
  
  // API: Get all workflows
  if (parsedUrl.pathname === '/api/workflows' && req.method === 'GET') {
    const data = loadWorkflows();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data.workflows));
    return;
  }
  
  // API: Save workflow
  if (parsedUrl.pathname === '/api/workflows' && req.method === 'POST') {
    let body = '';
    
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    req.on('end', () => {
      try {
        const workflow = JSON.parse(body);
        
        if (!workflow.name || !workflow.nodes || !workflow.connections) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Missing required fields: name, nodes, connections' }));
          return;
        }
        
        const data = loadWorkflows();
        workflow.id = workflow.id || Date.now().toString();
        workflow.createdAt = workflow.createdAt || new Date().toISOString();
        workflow.updatedAt = new Date().toISOString();
        
        // Update or add
        const existingIndex = data.workflows.findIndex(w => w.id === workflow.id);
        if (existingIndex >= 0) {
          data.workflows[existingIndex] = workflow;
        } else {
          data.workflows.push(workflow);
        }
        
        saveWorkflows(data);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, workflow }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
    
    return;
  }
  
  // API: Delete workflow
  if (parsedUrl.pathname === '/api/workflows' && req.method === 'DELETE') {
    const workflowId = parsedUrl.query.id;
    
    if (!workflowId) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Missing workflow id' }));
      return;
    }
    
    const data = loadWorkflows();
    data.workflows = data.workflows.filter(w => w.id !== workflowId);
    saveWorkflows(data);
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: true }));
    return;
  }
  
  // API: Execute workflow
  if (parsedUrl.pathname === '/api/workflows/execute' && req.method === 'POST') {
    let body = '';
    
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    req.on('end', async () => {
      try {
        const { workflowId, input } = JSON.parse(body);
        
        if (!workflowId) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Missing workflowId' }));
          return;
        }
        
        const data = loadWorkflows();
        const workflow = data.workflows.find(w => w.id === workflowId);
        
        if (!workflow) {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Workflow not found' }));
          return;
        }
        
        // 执行工作流
        const results = [];
        const nodeResults = {};
        
        // 构建依赖图并执行
        const executeNode = async (nodeId) => {
          if (nodeResults[nodeId]) return nodeResults[nodeId];
          
          const node = workflow.nodes.find(n => n.id === nodeId);
          if (!node) return null;
          
          // 获取依赖节点的结果
          const dependencies = workflow.connections
            .filter(c => c.target === nodeId)
            .map(c => c.source);
          
          let message = input;
          if (dependencies.length > 0) {
            const depResults = await Promise.all(dependencies.map(d => executeNode(d)));
            message = `前序结果:\n${depResults.map(r => r ? r.response : '').join('\n---\n')}\n\n用户输入: ${input}`;
          } else {
            message = input;
          }
          
          const result = await callAgent(node.agentId, message);
          const textContent = extractTextContent(result.response);
          
          nodeResults[nodeId] = { nodeId, agentId: node.agentId, response: textContent };
          results.push(nodeResults[nodeId]);
          
          return nodeResults[nodeId];
        };
        
        // 从没有依赖的节点开始执行
        const rootNodes = workflow.nodes.filter(n => 
          !workflow.connections.some(c => c.target === n.id)
        );
        
        await Promise.all(rootNodes.map(n => executeNode(n.id)));
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, results }));
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
