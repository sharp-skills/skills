#!/usr/bin/env node

const https = require('https');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://raw.githubusercontent.com/sharp-skills/skills/main/skills';
const API_URL = 'https://api.github.com/repos/sharp-skills/skills/contents/skills';

const TOOLS = {
  'claude':   { dir: '.claude/skills',   label: 'Claude Code' },
  'codex':    { dir: '.codex/skills',    label: 'OpenAI Codex' },
  'gemini':   { dir: '.gemini/skills',   label: 'Gemini CLI' },
  'cursor':   { dir: '.cursor/skills',   label: 'Cursor' },
  'windsurf': { dir: '.windsurf/skills', label: 'Windsurf' },
};

function detectTool() {
  for (const [key, cfg] of Object.entries(TOOLS)) {
    if (fs.existsSync(path.join(process.cwd(), cfg.dir.split('/')[0]))) return key;
  }
  return 'claude';
}

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const opts = new URL(url);
    https.get({ hostname: opts.hostname, path: opts.pathname + opts.search, headers: { 'User-Agent': 'sharp-skills-cli/1.0.0' } }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) return fetchUrl(res.headers.location).then(resolve).catch(reject);
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    }).on('error', reject);
  });
}

async function install(skillName, toolArg) {
  const tool = toolArg || detectTool();
  const cfg = TOOLS[tool];
  if (!cfg) { console.error('Unknown tool: ' + tool + '. Use: claude|codex|gemini|cursor|windsurf'); process.exit(1); }
  console.log('Installing: ' + skillName + ' -> ' + cfg.label);
  const res = await fetchUrl(BASE_URL + '/' + skillName + '/SKILL.md');
  if (res.status === 404) { console.error('Skill "' + skillName + '" not found.\nBrowse: https://github.com/sharp-skills/skills'); process.exit(1); }
  if (res.status !== 200) { console.error('HTTP ' + res.status); process.exit(1); }
  const destDir = path.join(process.cwd(), cfg.dir);
  fs.mkdirSync(destDir, { recursive: true });
  const destFile = path.join(destDir, skillName + '.md');
  fs.writeFileSync(destFile, res.body, 'utf8');
  console.log('Installed to: ' + destFile);
}

async function listSkills() {
  console.log('Fetching skills...\n');
  const res = await fetchUrl(API_URL);
  if (res.status !== 200) { console.error('Failed to fetch list'); process.exit(1); }
  const skills = JSON.parse(res.body);
  skills.forEach(s => console.log('  - ' + s.name));
  console.log('\nTotal: ' + skills.length + ' skills');
  console.log('Install: npx sharp-skills install <skill-name>');
}

async function main() {
  const [,, cmd, ...args] = process.argv;
  if (cmd === 'install') {
    const name = args[0];
    if (!name) { console.error('Usage: npx sharp-skills install <skill> [--tool=claude|cursor|gemini|codex|windsurf]'); process.exit(1); }
    const toolFlag = (args.find(a => a.startsWith('--tool=')) || '').split('=')[1] || null;
    await install(name, toolFlag);
  } else if (cmd === 'list') {
    await listSkills();
  } else {
    console.log([
      '',
      '  SharpSkills CLI v1.0',
      '',
      '  Commands:',
      '    npx sharp-skills install <skill>              Auto-detects your tool',
      '    npx sharp-skills install <skill> --tool=cursor',
      '    npx sharp-skills list                         Browse all skills',
      '',
      '  Examples:',
      '    npx sharp-skills install stripe',
      '    npx sharp-skills install docker --tool=cursor',
      '    npx sharp-skills install openai --tool=gemini',
      '',
      '  Supported tools: claude | codex | gemini | cursor | windsurf',
      '  Repo: https://github.com/sharp-skills/skills',
      '',
    ].join('\n'));
  }
}

main().catch(err => { console.error('Error:', err.message); process.exit(1); });
