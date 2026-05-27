# 🧠 SmartNotes AI

SmartNotes AI is an AI-powered study notes generator built using Flask and Google Gemini API.

Users can generate detailed study notes, summaries, and key points for any topic instantly using AI. The application also supports PDF export and notes management.

---

# 🚀 Features

- ⚡ AI-generated study notes
- 📋 Smart summaries
- 🎯 Key revision points
- 📄 PDF export functionality
- 💾 Save notes history
- 🔍 Search saved notes
- 🌙 Dark mode support
- 📱 Fully responsive UI
- 🔐 Authentication system

---

# 🛠 Tech Stack

| Technology | Usage |
|---|---|
| Python | Backend |
| Flask | Web Framework |
| Gemini API | AI Content Generation |
| SQLite | Database |
| HTML/CSS/JS | Frontend |
| ReportLab | PDF Generation |

---

# 📂 Project Structure

```bash
smart_notes/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── static/
│   ├── css/
│   └── js/
│
├── templates/
│
└── instance/
```

---

# ⚙️ Setup & Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/smartnotes-ai.git
cd smartnotes-ai
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

---

## 3. Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure Gemini API Key

Create a `.env` file in the project root directory.

Add the following:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_random_secret_key
```

---

# 🔗 Get Gemini API Key

Generate your API key from:

https://aistudio.google.com/app/apikey

---

# ▶️ Run the Project

```bash
python app.py
```

Open in browser:

```text
http://127.0.0.1:5000
```

---

# 🐍 Python Version

Tested on:

```text
Python 3.14
```

---

# ⚠️ Important

- Do NOT upload your `.env` file to GitHub
- Keep your Gemini API key private
- Users must generate and add their own Gemini API key

Add this to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
```

---

# 📸 Screenshots

_Add your project screenshots here_

---

# 🔮 Future Improvements

- AI chatbot integration
- Cloud deployment
- Better PDF templates
- Multi-language support
- Notes sharing system

---

# 👨‍💻 Author

Nitin Saini
