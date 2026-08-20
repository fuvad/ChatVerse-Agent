# ChatVerse 1.0

A modern, responsive AI chat interface with integrated web search functionality. ChatVerse 1.0 provides a clean UI similar to Perplexity.ai, combining conversational AI with real-time search capabilities

---

## 🌐 Live Demo

**Frontend:**
> https://chatverse-frontend-umber.vercel.app/

**Backend API:**
> https://chatverse-latest.onrender.com

> **Note:** The backend is hosted on Render's free tier, so the first request may take 30–60 seconds while the service wakes up.

---

## ✨ Features

- **Real-time AI Responses** - Stream AI responses as they're generated
- **Integrated Web Search** - AI can search the web for up-to-date information
- **Conversation Memory** - Maintains context throughout your conversation
- **Search Process Transparency** - Visual indicators show searching, reading, and writing stages
- **Responsive Design** - Clean, modern UI that works across devices

---

## 🏗️ Architecture

ChatVerse 1.0 follows a client-server architecture:

### Client (Next.js + React) - The Frontend
- Modern React application built with Next.js
- Real-time streaming updates using Server-Sent Events (SSE)
- Components for message display, search status, and input handling

### Server (FastAPI + LangGraph) - The Backend
- Python backend using FastAPI for API endpoints
- LangGraph implementation for conversation flow with LLM and tools
- Integration with Tavily Search API for web searching capabilities
- Server-Sent Events for real-time streaming of AI responses

---

## 🛠 Tech Stack

Frontend
- Next.js
- React
- Tailwind CSS
- TypeScript

Backend
- FastAPI
- LangGraph
- OpenAI
- Tavily

Deployment
- Docker
- Vercel
- Render

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- OpenAI API key
- Tavily API key

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fuvad/ChatVerse-Agent.git
   cd ChatVerse-Agent
   ```

2. **Set up the server**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**  
   Create a `.env` file in the server directory:
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   
4. **Set up the client**
```bash
cd ../frontend
npm install
```

### Running the Application

1. **Start the server**
   ```bash
   cd backend
   uvicorn app:app --reload
   ```

   - Can also use Docker for running backend

2. **Start the client**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser and navigate to http://localhost:3000**   

## 🔍 How It Works

1. **User sends a message** through the chat interface
2. **Server processes the message** using GPT-4o-mini (You can change it if you would like to use better models)
3. **AI decides** whether to use search or respond directly
4. If search is needed:
   - Search query is sent to Tavily API
   - Results are processed and provided back to the AI
   - AI uses this information to formulate a response
5. **Response is streamed** back to the client in real-time
6. **Search stages are displayed** to the user (searching, reading, writing)

---

## ☁️ Deployment
### Backend

The backend is deployed on **Render**.

Required environment variables

```text
OPENAI_API_KEY
TAVILY_API_KEY
```

---

### Frontend

The frontend is deployed on **Vercel**.

---

# 🚧 Roadmap

## ChatVerse 2.0

Planned improvements

- User authentication
- Persistent chat history
- Multiple conversations
- Markdown rendering
- Code syntax highlighting
- Copy code button
- File uploads
- PDF chat
- Image understanding
- Image generation
- Voice interaction
- Better search query generation
- Improved UI/UX
- Database-backed conversation storage

---
