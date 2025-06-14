# Quick Start Guide

Get up and running with the Multi-Agent Framework in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip package manager
- At least one API key from:
  - [Google Gemini](https://makersuite.google.com/app/apikey) (Recommended)
  - [Anthropic Claude](https://console.anthropic.com/)
  - [OpenAI](https://platform.openai.com/api-keys)

## Installation

1. **Clone and install MAF:**
```bash
git clone https://github.com/micgo/maf-standalone.git
cd maf-standalone
pip install -e .
```

2. **Verify installation:**
```bash
maf --version
# Output: Multi-Agent Framework, version 0.1.0
```

## Your First Project

### Step 1: Navigate to your project
```bash
cd ~/your-project-directory
```

### Step 2: Initialize MAF
```bash
maf init
```

This creates:
- `.maf-config.json` - Configuration file
- `.env.example` - Template for API keys
- `.maf_messages/` - Message queue directory
- `.maf_logs/` - Log directory

### Step 3: Add your API key
```bash
cp .env.example .env
```

Edit `.env` and add at least one API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
# ANTHROPIC_API_KEY=your_claude_key_here
# OPENAI_API_KEY=your_openai_key_here
```

### Step 4: Launch the agents
```bash
# For now, use polling mode (more stable)
maf launch --mode polling
```

You should see:
```
🚀 Launching Multi-Agent Framework
Starting agents: orchestrator, frontend_agent, backend_agent...
✅ Agents are running. Press Ctrl+C to stop...
```

### Step 5: Create your first feature
In a new terminal, trigger a development task:
```bash
cd ~/your-project-directory
maf trigger "Create a simple contact form component with name, email, and message fields"
```

Watch as the agents:
1. 📋 Break down the task into subtasks
2. 🎨 Create the UI component
3. 🔧 Add necessary backend logic
4. ✅ Complete the feature

## Example Tasks

### For React/Next.js Projects
```bash
# Create a component
maf trigger "Create a responsive navigation bar with logo and menu items"

# Add functionality
maf trigger "Add dark mode toggle to the app"

# Create a page
maf trigger "Create an about page with team member cards"
```

### For Backend Projects
```bash
# Create an API endpoint
maf trigger "Create a REST API endpoint for user registration"

# Add database model
maf trigger "Create a database model for blog posts with title, content, and author"

# Add authentication
maf trigger "Add JWT authentication to the API"
```

### Full-Stack Features
```bash
# Complete feature
maf trigger "Create a todo list feature with add, edit, delete functionality"

# Complex integration
maf trigger "Add user comments system to blog posts"
```

## Monitoring Progress

### Check status
```bash
maf status
```

### View logs
```bash
# All logs
maf logs

# Specific agent
maf logs frontend_agent

# Follow logs
maf logs --follow
```

## Tips for Best Results

1. **Be Specific**: Instead of "add authentication", say "add JWT-based authentication with login and signup endpoints"

2. **One Feature at a Time**: Let agents complete one feature before starting another

3. **Use Project Context**: MAF auto-detects your project type and uses appropriate patterns

4. **Check Generated Code**: Always review the code agents create before deploying

## Common Issues

### Agents not processing tasks?
Switch to polling mode:
```bash
maf launch --mode polling
```

### API rate limits?
Use a different provider or add delays in config:
```json
{
  "performance": {
    "request_delay": 2
  }
}
```

### Need specific agents only?
```bash
maf launch --agents orchestrator --agents frontend_agent
```

## Next Steps

- 📖 Read the [full documentation](https://github.com/micgo/maf-standalone/wiki)
- 🔧 Explore [configuration options](https://github.com/micgo/maf-standalone/wiki/Configuration)
- 🤝 Join [discussions](https://github.com/micgo/maf-standalone/discussions)
- 🐛 Report [issues](https://github.com/micgo/maf-standalone/issues)

## Example: Building a Blog

Here's a complete example of building a blog feature:

```bash
# 1. Initialize your Next.js project (if needed)
npx create-next-app@latest my-blog --typescript --tailwind
cd my-blog

# 2. Initialize MAF
maf init
# Add your API key to .env

# 3. Launch agents
maf launch --mode polling

# 4. Build features (in another terminal)
maf trigger "Create a blog post component that displays title, content, author, and date"
maf trigger "Create a blog post list page that shows all blog posts"
maf trigger "Add a create new blog post form with title and content fields"
maf trigger "Create API endpoints for creating and fetching blog posts"

# 5. Check results
maf status
```

Within minutes, you'll have a working blog with:
- 📝 Blog post components
- 📄 List and detail pages  
- ✏️ Create post functionality
- 🔌 API endpoints
- 🗄️ Database integration

## Happy Building! 🚀

MAF is here to accelerate your development. Start with simple tasks and work your way up to complex features. The agents learn your project structure and improve over time.