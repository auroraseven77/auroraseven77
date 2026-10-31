const PROJECTS = Object.freeze([
  'auroraseven77',
  'auroraseven77-test',
  'auroraseven77-v21-validation',
  'auroraseven77-b12-audit',
  'auroraseven77-b13-repro',
  'auroraseven77-b13-energy'
]);
const EXTENSIONS = new Set(['.md', '.txt', '.json', '.yaml', '.yml', '.py', '.toml', '.csv']);
const SENSITIVE = /(^|[._-])(env|pem|key|secret|credentials?|token|id_rsa|private)([._-]|$)/i;

const POLICY = Object.freeze({
  'aurora.list_projects': Object.freeze({
    name: 'aurora.list_projects',
    description: 'Lista os seis projetos autorizados sem revelar caminhos locais.',
    inputSchema: Object.freeze({ type: 'object', properties: {}, additionalProperties: false })
  }),
  'aurora.read_evidence': Object.freeze({
    name: 'aurora.read_evidence',
    description: 'Lê um arquivo de evidência autorizado de até 48 KiB e calcula SHA-256.',
    inputSchema: Object.freeze({
      type: 'object',
      properties: {
        project: { type: 'string', enum: PROJECTS },
        relative_path: { type: 'string', minLength: 1, maxLength: 1024 }
      },
      required: ['project', 'relative_path'],
      additionalProperties: false
    })
  })
});

function plainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
}

export function isToolAllowed(name, args) {
  if (!Object.hasOwn(POLICY, name) || !plainObject(args)) return false;
  const keys = Object.keys(args);
  if (name === 'aurora.list_projects') return keys.length === 0;
  if (name !== 'aurora.read_evidence') return false;
  if (keys.length !== 2 || !keys.includes('project') || !keys.includes('relative_path')) return false;
  if (!PROJECTS.includes(args.project) || typeof args.relative_path !== 'string') return false;
  const p = args.relative_path;
  if (!p || p.length > 1024 || p.includes('\0') || p.includes('\\') || p.startsWith('/')) return false;
  const segments = p.split('/');
  if (segments.some(s => !s || s === '.' || s === '..' || s.startsWith('.'))) return false;
  if (segments.some(s => SENSITIVE.test(s))) return false;
  const dot = p.lastIndexOf('.');
  const ext = dot >= 0 ? p.slice(dot).toLowerCase() : '';
  return EXTENSIONS.has(ext);
}

export function filterAllowedTools(advertisedTools) {
  if (!Array.isArray(advertisedTools)) return [];
  const announced = new Set(advertisedTools.filter(t => t && typeof t.name === 'string').map(t => t.name));
  return Object.values(POLICY).filter(p => announced.has(p.name)).map(p => ({
    name: p.name,
    description: p.description,
    inputSchema: structuredClone(p.inputSchema)
  }));
}

export function allowedToolNames() {
  return Object.keys(POLICY);
}
