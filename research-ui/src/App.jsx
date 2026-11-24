import { useState } from "react";
import { BookOpen, MessageCircle } from "lucide-react";
import { ResearchPipelineUI } from "./ResearchUI.jsx";
import DocumentChat from "./DocumentChat.jsx";

export default function App() {
  const [view, setView] = useState("research");

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <nav className="flex items-center justify-center gap-2 border-b border-zinc-800 px-4 py-3">
        <button
          type="button"
          onClick={() => setView("research")}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition ${
            view === "research" ? "bg-amber-500 text-zinc-950" : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
          }`}
        >
          <BookOpen className="h-4 w-4" />
          Research pipeline
        </button>
        <button
          type="button"
          onClick={() => setView("chat")}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition ${
            view === "chat" ? "bg-amber-500 text-zinc-950" : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
          }`}
        >
          <MessageCircle className="h-4 w-4" />
          Document chat
        </button>
      </nav>
      {view === "research" ? <ResearchPipelineUI /> : <DocumentChat />}
    </div>
  );
}
