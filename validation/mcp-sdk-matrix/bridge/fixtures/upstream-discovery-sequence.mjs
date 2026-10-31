import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';

let discoveryCount = 0;
const server = new Server({ name: 'aurora-discovery-fixture', version: '1.0.0' }, { capabilities: { tools: {} } });
const toolSet = [
  { name: 'aurora.list_projects', description: 'fixture project list', inputSchema: { type: 'object', properties: {}, additionalProperties: false } },
  { name: 'aurora.read_evidence', description: 'fixture evidence reader', inputSchema: { type: 'object', properties: { project: { type: 'string' }, relative_path: { type: 'string' } }, required: ['project', 'relative_path'], additionalProperties: false } }
];
server.setRequestHandler(ListToolsRequestSchema, async () => {
  discoveryCount++;
  return { tools: discoveryCount <= 2 ? toolSet : [toolSet[0]] };
});
server.setRequestHandler(CallToolRequestSchema, async request => {
  if (request.params?.name === 'aurora.list_projects' && Object.keys(request.params?.arguments || {}).length === 0) {
    return { content: [{ type: 'text', text: '[{"name":"fixture-project","exists":true}]' }], isError: false };
  }
  return { isError: true, content: [{ type: 'text', text: 'FIXTURE_ARGUMENTS_DENIED' }] };
});
await server.connect(new StdioServerTransport());
