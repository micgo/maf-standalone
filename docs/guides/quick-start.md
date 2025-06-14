# Quick Start Guide

Get up and running with the Multi-Agent Framework in 5 minutes!

## 🎯 What You'll Build

In this guide, you'll use AI agents to automatically build a working feature in your project. No manual coding required!

## Prerequisites

Before you start, make sure you have:

✅ **Python 3.10+** installed ([Download Python](https://www.python.org/downloads/))  
✅ **Git** installed ([Download Git](https://git-scm.com/downloads))  
✅ **An API key** from one of these providers:
  - [Google Gemini](https://makersuite.google.com/app/apikey) (Recommended - Free tier available)
  - [Anthropic Claude](https://console.anthropic.com/) (Powerful but requires payment)
  - [OpenAI](https://platform.openai.com/api-keys) (GPT-4 recommended)

## ⚡ Quick Installation (2 minutes)

Open your terminal and run these commands:

```bash
# 1. Clone the repository
git clone https://github.com/micgo/maf-standalone.git
cd maf-standalone

# 2. Install MAF (creates 'maf' command)
pip install -e .

# 3. Verify it works
maf --version
```

You should see: `Multi-Agent Framework, version 0.1.2`

## 🚀 Your First AI-Generated Feature (3 minutes)

Let's create a real feature in a project. Choose one:

<details>
<summary><b>Option A: I have an existing project</b></summary>

```bash
# Navigate to your project
cd ~/path/to/your/project

# Initialize MAF
maf init
```
</details>

<details>
<summary><b>Option B: I want to try with a new project</b></summary>

```bash
# Create a simple React project
npx create-react-app my-ai-app
cd my-ai-app

# Or a Next.js project
npx create-next-app@latest my-ai-app --typescript --tailwind --app
cd my-ai-app

# Initialize MAF
maf init
```
</details>

### 1️⃣ Set Up Your API Key (30 seconds)

```bash
# Copy the template
cp .env.example .env

# Open .env in your editor
# Add your API key (no quotes needed):
# GEMINI_API_KEY=AIzaSyDCvp5MTJLUdtaYrQDg...
```

**Quick edit option:**
```bash
echo "GEMINI_API_KEY=your_actual_key_here" > .env
```

### 2️⃣ Launch the AI Agents (30 seconds)

```bash
maf launch
```

You'll see:
```
🚀 Launching Multi-Agent Framework
✅ Event bus: Started
✅ Orchestrator: Ready
✅ Frontend Agent: Ready
✅ Backend Agent: Ready
✅ Database Agent: Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agents are running! Press Ctrl+C to stop.
```

### 3️⃣ Create Your Feature (2 minutes)

Open a **new terminal** window and run:

```bash
# Navigate back to your project
cd ~/path/to/your/project

# Create a feature with one command
maf trigger "Create a contact form with name, email, and message fields that saves to a database"
```

**What happens next:**
- 🤖 Orchestrator breaks down the task
- 🎨 Frontend agent creates the UI component
- ⚙️ Backend agent creates the API endpoint
- 💾 Database agent sets up data storage
- ✅ All code is integrated into your project

**Watch the magic happen!** Check your project files - you'll see new components, APIs, and database models created automatically.

## 🎬 See It In Action

Here's what the output looks like:

```
📋 Orchestrator: Analyzing task...
├─ Creating subtasks:
│  ├─ Frontend: Build contact form UI
│  ├─ Backend: Create submission endpoint
│  └─ Database: Design contact schema

🎨 Frontend Agent: Creating ContactForm.jsx...
✓ Created: src/components/ContactForm.jsx

⚙️ Backend Agent: Setting up API...
✓ Created: src/api/contact.js

💾 Database Agent: Creating schema...
✓ Created: src/models/Contact.js

✅ Feature complete! Files created:
   - src/components/ContactForm.jsx
   - src/api/contact.js  
   - src/models/Contact.js
```

## ⚠️ Common Gotchas & Quick Fixes

<details>
<summary><b>❌ "No API keys configured"</b></summary>

Make sure your `.env` file:
- Is in your project root (where you ran `maf init`)
- Has NO quotes around the API key
- Has NO spaces around the `=`

✅ Correct: `GEMINI_API_KEY=AIzaSyDCvp5MTJLUdtaYrQDg...`  
❌ Wrong: `GEMINI_API_KEY="AIzaSyDCvp5MTJLUdtaYrQDg..."`  
❌ Wrong: `GEMINI_API_KEY = AIzaSyDCvp5MTJLUdtaYrQDg...`
</details>

<details>
<summary><b>❌ "Agents not processing tasks"</b></summary>

The event-driven mode can sometimes have issues. Use polling mode instead:
```bash
maf launch --mode polling
```
</details>

<details>
<summary><b>❌ "Rate limit exceeded"</b></summary>

You're making too many API calls. Either:
1. Wait a minute and try again
2. Use a different API provider
3. Add delays in your config
</details>

## 🎯 Try These First!

Start with these simple tasks that work great:

### 1. **Hero Section** (Frontend)
```bash
maf trigger "Create a hero section with a title, subtitle, and call-to-action button"
```

### 2. **Navigation Bar** (Frontend)
```bash
maf trigger "Create a responsive navigation bar with logo and menu items"
```

### 3. **Contact Form** (Full-Stack)
```bash
maf trigger "Create a contact form that sends emails"
```

### 4. **Blog Post Component** (Frontend)
```bash
maf trigger "Create a blog post card component with title, excerpt, author, and date"
```

### 5. **User API** (Backend)
```bash
maf trigger "Create REST API endpoints for user CRUD operations"
```

## 📚 More Example Tasks

<details>
<summary><b>Frontend Components</b></summary>

```bash
# UI Components
maf trigger "Create a testimonial card component with avatar, quote, and name"
maf trigger "Create a pricing table with three tiers"
maf trigger "Create a footer with social media links"

# Interactive Features
maf trigger "Add dark mode toggle to the app"
maf trigger "Create an image carousel component"
maf trigger "Add search functionality to the navbar"
```
</details>

<details>
<summary><b>Backend Features</b></summary>

```bash
# API Development
maf trigger "Create a REST API for todo items with CRUD operations"
maf trigger "Add pagination to the blog posts API"
maf trigger "Create webhook endpoint for payment processing"

# Database & Auth
maf trigger "Set up user authentication with JWT"
maf trigger "Create database schema for an e-commerce product catalog"
maf trigger "Add role-based access control to the API"
```
</details>

<details>
<summary><b>Full-Stack Features</b></summary>

```bash
# Complete Features
maf trigger "Create a comment system for blog posts"
maf trigger "Build a user dashboard with profile editing"
maf trigger "Create a file upload feature with progress indicator"

# Complex Apps
maf trigger "Create a task management system with drag-and-drop"
maf trigger "Build a real-time chat feature"
maf trigger "Create a shopping cart with checkout flow"
```
</details>

## 📊 Monitoring Your AI Agents

While agents are working, you can:

```bash
# Check what they're doing
maf status

# Watch live logs
maf logs --follow

# See specific agent activity
maf logs frontend_agent
```

## 💡 Pro Tips for Better Results

### 1. **Be Specific**
❌ Vague: "Add authentication"  
✅ Better: "Add email/password authentication with login and signup pages"

### 2. **One at a Time**
Let agents finish one task before starting the next. They work better when focused!

### 3. **Review the Code**
Always check what the agents created. They're good, but not perfect!

### 4. **Project Context Matters**
MAF automatically detects if you're using React, Next.js, Django, etc. and generates appropriate code.

## 🚨 Need Help?

<details>
<summary><b>Something not working?</b></summary>

1. Check our [Troubleshooting Guide](https://github.com/micgo/maf-standalone/wiki/Troubleshooting)
2. Search [existing issues](https://github.com/micgo/maf-standalone/issues)
3. Ask in [Discussions](https://github.com/micgo/maf-standalone/discussions)
4. Report a [bug](https://github.com/micgo/maf-standalone/issues/new)
</details>

## 🎓 What's Next?

Now that you've created your first AI-generated feature:

### **Level Up Your Skills**
1. **Try a Complex Feature**: `maf trigger "Create a real-time notification system"`
2. **Build a Full App**: Follow our [Blog Tutorial](#complete-example-blog-in-10-minutes) below
3. **Customize Agents**: Learn about [agent configuration](https://github.com/micgo/maf-standalone/wiki/Configuration)

### **Join the Community**
- ⭐ [Star the repo](https://github.com/micgo/maf-standalone) to support the project
- 💬 [Join discussions](https://github.com/micgo/maf-standalone/discussions) to share ideas
- 🤝 [Contribute](https://github.com/micgo/maf-standalone/blob/main/CONTRIBUTING.md) to make MAF better

## 📝 Complete Example: Blog in 10 Minutes

Want to see the full power of MAF? Let's build a complete blog:

<details>
<summary><b>Click to see the full blog tutorial</b></summary>

```bash
# 1. Create a new Next.js project
npx create-next-app@latest ai-blog --typescript --tailwind --app
cd ai-blog

# 2. Initialize MAF
maf init
echo "GEMINI_API_KEY=your_key_here" > .env

# 3. Launch agents
maf launch

# 4. Build the blog (in new terminal)
cd ai-blog

# Create the data model
maf trigger "Create a blog post model with title, slug, content, excerpt, author, tags, and timestamps"

# Create the UI components
maf trigger "Create a blog post card component that shows title, excerpt, author, date, and tags"
maf trigger "Create a full blog post view component with markdown rendering"
maf trigger "Create a blog post editor with title, content, excerpt, and tags fields"

# Create the pages
maf trigger "Create a blog homepage that lists all posts with pagination"
maf trigger "Create individual blog post pages using dynamic routing"
maf trigger "Create an admin page for creating and editing blog posts"

# Add features
maf trigger "Add search functionality to filter blog posts"
maf trigger "Add tag filtering to the blog"
maf trigger "Add related posts section to blog post pages"

# 5. Check your creation!
npm run dev
# Open http://localhost:3000
```

**You just built a full-featured blog with:**
- 📝 Rich text editor
- 🏷️ Tag system
- 🔍 Search functionality
- 📱 Responsive design
- 📄 Dynamic routing
- 👤 Admin interface

All in under 10 minutes! 🎉
</details>

## 🚀 Start Building Amazing Things!

You're now ready to use AI agents to accelerate your development. Remember:
- Start simple, build up complexity
- Be specific in your requests
- Review and refine the generated code
- Have fun and experiment!

**Happy coding with your new AI team! 🤖**