# 对话结果显示优化设计方案

## 需求背景

Web页面对话功能目前已能正常响应，但显示结果存在问题：页面展示了所有返回内容，而实际只需要显示 agent 的回答。

**涉及文件：**
- `docs/dashboard.html` - 前端对话界面
- `server/index.js` - API 服务端

## 问题分析

当前数据流：
```
User Input → dashboard.html → /api/chat → server/index.js → openclaw agent → response
                                                                            ↓
User ← dashboard.html ← data.result?.response ← { response: 完整输出 }
```

**问题根源：**
`openclaw agent` 返回的完整输出包含：
- Agent 思考过程 (thinking)
- 工具调用信息 (tool_calls / tool_results)
- 调试信息
- 实际回答内容

当前前端直接显示 `data.result?.response`，导致所有技术信息都暴露给用户。

## 设计方案

### 方案概述

在前端对返回内容进行过滤，只显示 agent 的最终回答内容。

### 具体实现

修改 `docs/dashboard.html` 中的 `sendMessage` 函数（第454行附近）：

**修改前：**
```javascript
chatHistory.push({ role: 'agent', content: data.result?.response || data.error || '收到回复' });
```

**修改后：**
```javascript
const rawResponse = data.result?.response || data.error || '收到回复';
const filteredResponse = filterAgentResponse(rawResponse);
chatHistory.push({ role: 'agent', content: filteredResponse });
```

**新增过滤函数：**
```javascript
function filterAgentResponse(text) {
  if (!text) return '收到回复';
  
  // 移除工具调用块 (tool_calls, tool_results, function calls)
  let filtered = text
    // 移除 <tool_call>...</tool_call> 或类似标记
    .replace(/<tool_call>[\s\S]*?<\/tool_call>/gi, '')
    .replace(/<tool_calls>[\s\S]*?<\/tool_calls>/gi, '')
    .replace(/<function_calls>[\s\S]*?<\/function_calls>/gi, '')
    // 移除工具调用相关标记
    .replace(/\[(?:tool|call|function).*?:.*?\]/gi, '')
    .replace(/```tool[\s\S]*?```/g, '')
    .replace(/```function[\s\S]*?```/g, '');
  
  // 移除 thinking 块
  filtered = filtered
    .replace(/<thinking>[\s\S]*?<\/thinking>/gi, '')
    .replace(/\[think\] [\s\S]*? \[\/think\]/gi, '')
    .replace(/\*\*Thinking:\*\* [\s\S]*?(?=\n\n|\n[A-Z]|$)/gi, '');
  
  // 移除调试信息行
  filtered = filtered
    .split('\n')
    .filter(line => {
      const lower = line.toLowerCase();
      // 过滤掉纯调试/系统信息
      if (lower.startsWith('[debug]') || lower.startsWith('[system]') || 
          lower.startsWith('tool:') || lower.startsWith('calling:') ||
          lower.startsWith('executing:')) {
        return false;
      }
      return true;
    })
    .join('\n');
  
  // 清理多余空白
  filtered = filtered
    .replace(/\n{3,}/g, '\n\n')  // 多个换行合并为两个
    .replace(/^\s+|\s+$/g, '')    // 去除首尾空白
    .trim();
  
  return filtered || '收到回复';
}
```

## 接口定义

无需修改后端 API，仅前端处理。

## 验收标准

1. ✅ 对话界面只显示 agent 的文字回答
2. ✅ 不显示 thinking 过程
3. ✅ 不显示工具调用信息
4. ✅ 不显示调试信息
5. ✅ 正常的换行和格式保留
6. ✅ 空内容或仅过滤后无内容时显示默认提示

## 实施步骤

1. 在 `docs/dashboard.html` 中添加 `filterAgentResponse` 函数
2. 修改 `sendMessage` 函数中处理响应的逻辑
3. 测试验证过滤效果
