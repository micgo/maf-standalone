# MAF Scripts

This directory contains utility scripts for the Multi-Agent Framework.

## Available Scripts

### install.sh
Quick installation script for setting up MAF from source.

```bash
./scripts/install.sh
```

### setup_venv.sh
Creates and configures a Python virtual environment for MAF development.

```bash
./scripts/setup_venv.sh
```

### launch_agents.sh
Legacy script for launching agents. **Deprecated** - use `maf launch` CLI command instead.

```bash
# Old way (deprecated)
./scripts/launch_agents.sh

# New way (recommended)
maf launch
```

### check_agents.sh
Legacy script for checking agent status. **Deprecated** - use `maf status` CLI command instead.

```bash
# Old way (deprecated)
./scripts/check_agents.sh

# New way (recommended)
maf status
```

## Note

Most functionality from these shell scripts has been integrated into the MAF CLI. It's recommended to use the `maf` command for all operations. These scripts are kept for backward compatibility.