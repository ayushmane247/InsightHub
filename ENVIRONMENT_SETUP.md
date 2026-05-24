# 🛠️ Environment Setup Guide – InsightHub

> This guide walks you through setting up InsightHub on your machine.  
> Two options are covered — pick whichever feels right for you.  
> **Not sure which to pick?** → Jump to [Which one should I use?](#-which-one-should-i-use)

---

## 📌 Table of Contents

- [Option A — Using venv (Simple & Lightweight)](#option-a--using-venv-simple--lightweight)
- [Option B — Using Anaconda (Recommended)](#option-b--using-anaconda-recommended)
- [Which one should I use?](#-which-one-should-i-use)
- [VS Code Auto-Activation (Anaconda only)](#-vs-code-auto-activation-anaconda-only)
- [Common Issues](#-common-issues)

---

## Option A — Using venv (Simple & Lightweight)

`venv` comes built into Python. No extra installs needed.

### Step 1 — Clone the repo

```bash
git clone https://github.com/ayushmane247/InsightHub.git
cd InsightHub
```

### Step 2 — Create the virtual environment

```bash
# On macOS/Linux
python3 -m venv venv

# On Windows
python -m venv venv
```

This creates a `venv/` folder inside your project. That's your isolated environment.

### Step 3 — Activate it

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

✅ You'll see `(venv)` appear at the start of your terminal line — that means it's active.

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Run the app

```bash
streamlit run App.py
```

### Done! To deactivate when finished:

```bash
deactivate
```

> ⚠️ **Note:** Every time you open a new terminal, you'll need to run the activate command again (Step 3).

---

## Option B — Using Anaconda (Recommended)

Anaconda manages your environment centrally and **VS Code activates it automatically** every time you open the project — no manual activation needed.

### Step 1 — Install Anaconda

Download and install from: https://www.anaconda.com/download

> If you already have Anaconda installed, skip this step.

### Step 2 — Clone the repo

```bash
git clone https://github.com/ayushmane247/InsightHub.git
cd InsightHub
```

### Step 3 — Create a conda environment

```bash
conda create -n insight_hub_env python=3.10
```

This creates a new isolated environment named `insight_hub_env` with Python 3.10.

### Step 4 — Activate the environment

```bash
conda activate insight_hub_env
```

✅ You'll see `(insight_hub_env)` appear at the start of your terminal line.

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 6 — Run the app

```bash
streamlit run App.py
```

### Done! To deactivate when finished:

```bash
conda deactivate
```

---

## 🤔 Which one should I use?

| | venv | Anaconda |
|---|---|---|
| Already have Python installed? | ✅ Ready to go | Needs Anaconda install |
| Auto-activates in VS Code | ❌ Manual every time | ✅ Automatic |
| Manages Python versions | ❌ No | ✅ Yes |
| Works well with ML packages (Prophet, scikit-learn) | ⚠️ Sometimes tricky | ✅ Handles them cleanly |
| Best for | Quick setup, simple projects | ML projects, long-term use |

**Our recommendation:** Use **Anaconda** if you're working on this project regularly. Use **venv** if you just want to try it out quickly.

---

## ⚡ VS Code Auto-Activation (Anaconda only)

This is the magic that makes Anaconda feel effortless in VS Code.

**How it works:**

When you open the InsightHub folder in VS Code for the first time:

1. Press `Ctrl + Shift + P` (or `Cmd + Shift + P` on Mac)
2. Type **"Python: Select Interpreter"** and hit Enter
3. You'll see a list — pick the one that says `insight_hub_env`

   It will look something like:
   ```
   Python 3.10.x ('insight_hub_env') - conda
   ```

4. VS Code saves this choice for the project inside `.vscode/settings.json`

**From now on**, every time you open this folder in VS Code and open a terminal, it will automatically activate `insight_hub_env` — no commands needed. You'll see it fire up like this:

```
(insight_hub_env) PS D:\InsightHub>
```

That's it. VS Code + Anaconda handles everything for you. 🎉

---

## 🐛 Common Issues

**`conda` is not recognized as a command**
> Anaconda wasn't added to your PATH during install. Re-run the Anaconda installer and check "Add to PATH", or use **Anaconda Prompt** instead of a regular terminal.

**`streamlit` not found after installing requirements**
> Make sure your environment is activated before running pip install. You should see `(venv)` or `(insight_hub_env)` in your terminal.

**VS Code not showing the conda environment in the interpreter list**
> Close and reopen VS Code after creating the conda environment. It should appear in the list then.

**`pip install -r requirements.txt` fails on Prophet or pystan**
> Try installing via conda instead:
> ```bash
> conda install -c conda-forge prophet
> ```
> Then re-run `pip install -r requirements.txt` for the rest.

---

> 💙 Still stuck? Open an [Issue](https://github.com/ayushmane247/InsightHub/issues) and we'll help you out!
