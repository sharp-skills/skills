---
name: ansible
description: "Automate server provisioning, configuration, and deployments with Ansible. Use when asked to: write Ansible playbooks, create Ansible roles, manage server inventory, automate deployments with Ansible, configure servers with Ansible, use Ansible with AWS/GCP/Azure, or debug Ansible errors."
license: Apache-2.0
compatibility:
  - python >= 3.9
  - ansible >= 8.0
metadata:
  author: SharpSkills
  version: 1.1.0
  category: devops
  tags: [ansible, devops, automation, infrastructure, configuration-management, yaml, idempotent]
trace_id: 63429212093b
generated_at: '2026-02-28T22:43:15'
generator: sharpskill-v1.0 (legacy)
---

# Ansible

Ansible is an agentless IT automation tool — uses SSH to configure servers, deploy apps, and orchestrate infrastructure. No agents to install; just Python on the control node.

## Installation

```bash
pip install ansible
ansible --version  # verify
```

## Project Structure

```
ansible-project/
├── inventory/
│   ├── production.ini      # Production hosts
│   └── staging.ini         # Staging hosts
├── group_vars/
│   ├── all.yml             # Vars for all hosts
│   └── webservers.yml      # Vars for webservers group
├── roles/
│   └── nginx/
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       ├── templates/nginx.conf.j2
│       └── defaults/main.yml
├── site.yml                # Master playbook
└── ansible.cfg
```

## When to Use
- "Write an Ansible playbook to install nginx"
- "Automate server setup with Ansible"
- "Deploy app with Ansible"
- "Configure AWS EC2 instances with Ansible"
- "Create an Ansible role"
- "Fix Ansible SSH / become errors"

## Core Patterns

### Pattern 1: Basic Playbook — Install and Configure Nginx

```yaml
# site.yml
---
- name: Configure web servers
  hosts: webservers
  become: yes  # sudo
  vars:
    nginx_port: 80
    app_user: deploy

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Copy nginx config
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        owner: root
        group: root
        mode: '0644'
      notify: Restart nginx

    - name: Ensure nginx is started and enabled
      service:
        name: nginx
        state: started
        enabled: yes

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
```

### Pattern 2: Inventory File

```ini
# inventory/production.ini
[webservers]
web1.example.com ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_rsa
web2.example.com ansible_user=ubuntu

[dbservers]
db1.example.com ansible_user=ubuntu

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```

### Pattern 3: Role Structure — App Deployment

```yaml
# roles/app/tasks/main.yml
---
- name: Create app directory
  file:
    path: "{{ app_dir }}"
    state: directory
    owner: "{{ app_user }}"
    mode: '0755'

- name: Clone repository
  git:
    repo: "{{ app_repo }}"
    dest: "{{ app_dir }}"
    version: "{{ app_version | default('main') }}"
    force: yes
  notify: Restart app service

- name: Install Python dependencies
  pip:
    requirements: "{{ app_dir }}/requirements.txt"
    virtualenv: "{{ app_dir }}/venv"

- name: Copy environment file
  template:
    src: env.j2
    dest: "{{ app_dir }}/.env"
    owner: "{{ app_user }}"
    mode: '0600'
```

```yaml
# roles/app/defaults/main.yml
---
app_dir: /opt/myapp
app_user: deploy
app_repo: https://github.com/myorg/myapp.git
app_version: main
```

### Pattern 4: Run Ad-Hoc Commands and Check Mode

```bash
# Test connectivity
ansible all -i inventory/production.ini -m ping

# Run command on all webservers
ansible webservers -i inventory/production.ini -a "systemctl status nginx" --become

# Check what a playbook WOULD do (dry run)
ansible-playbook site.yml -i inventory/production.ini --check --diff

# Run only tasks with specific tag
ansible-playbook site.yml -i inventory/production.ini --tags "deploy"

# Limit to specific host
ansible-playbook site.yml -i inventory/production.ini --limit web1.example.com
```

### Pattern 5: Ansible Vault — Encrypt Secrets

```bash
# Encrypt a secrets file
ansible-vault encrypt group_vars/all/secrets.yml

# Edit encrypted file
ansible-vault edit group_vars/all/secrets.yml

# Run playbook with vault password
ansible-playbook site.yml --ask-vault-pass
# or use a password file
ansible-playbook site.yml --vault-password-file ~/.vault_pass
```

```yaml
# group_vars/all/secrets.yml (encrypted with ansible-vault)
---
db_password: "supersecret123"
api_key: "abc123xyz"
```

## Production Notes

1. **Always use `--check` before applying to production** — Ansible's check mode shows what would change without making changes. Critical for production deployments.
2. **`notify` + handlers for service restarts** — Only restarts service if a task actually changed something. Direct `state: restarted` always restarts even when config didn't change.
3. **`ansible_become_pass` vs `--ask-become-pass`** — In CI/CD, store sudo password in Vault; use `--ask-become-pass` only for interactive runs.
4. **Idempotency — state not commands** — Use `apt: state=present` not `command: apt-get install`. Ansible modules are idempotent; raw commands aren't.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `Permission denied (publickey)` | SSH key not loaded or wrong user | Check `ansible_user` and `ansible_ssh_private_key_file` in inventory |
| `sudo: a password is required` | Missing `become_pass` | Add `ansible_become_pass` in vault or pass `--ask-become-pass` |
| Task always shows `changed` | Using `command/shell` instead of idempotent module | Replace with proper Ansible module (apt, copy, template, etc.) |
| `[WARNING]: No inventory was parsed` | Wrong inventory path | Use `-i inventory/production.ini` explicitly |
| Template rendering fails | Undefined variable in Jinja2 | Set defaults in `defaults/main.yml` or use `| default('value')` filter |
| `fatal: [host]: UNREACHABLE` | Host down or firewall blocking port 22 | Test with `ssh -v user@host`; check security groups |

## Pre-Deploy Checklist
- [ ] Run `ansible-playbook --check --diff` on staging first
- [ ] Secrets encrypted with `ansible-vault` (never plaintext passwords in YAML)
- [ ] Inventory has correct `ansible_user` for each environment
- [ ] Handlers defined for all service restarts (not `state: restarted` in tasks)
- [ ] `ansible.cfg` sets `retry_files_enabled = False` (reduces noise)
- [ ] Tags applied to tasks for selective execution in CI/CD

## Resources
- Docs: https://docs.ansible.com/
- Galaxy (roles): https://galaxy.ansible.com/
- Best practices: https://docs.ansible.com/ansible/latest/tips_tricks/
