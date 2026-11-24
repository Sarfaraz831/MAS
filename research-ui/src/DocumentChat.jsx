import { useRef, useState } from "react";
import { AlertTriangle, FileText, Link2, Loader2, Send, ShieldAlert, X } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function readResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "The request failed.");
  }
  return data;
}

export default function DocumentChat() {
  const [sourceUrl, setSourceUrl] = useState("");
  const [source, setSource] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const fileInput = useRef(null);

  const attachSource = (document) => {
    setSource(document);
    setMessages([]);
    setError("");
  };

  const loadUrl = async (event) => {
    event.preventDefault();
    const url = sourceUrl.trim();
    if (!url || busy) return;

    setBusy("source");
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/chat/source/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      attachSource(await readResponse(response));
    } catch (requestError) {
      setError(requestError.message || "Could not read that URL.");
    } finally {
      setBusy("");
    }
  };

  const loadPdf = async (event) => {
    const file = event.target.files?.[0];
    if (!file || busy) return;

    setBusy("source");
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE}/api/chat/source/pdf`, {
        method: "POST",
        body: formData,
      });
      attachSource(await readResponse(response));
    } catch (requestError) {
      setError(requestError.message || "Could not read that PDF.");
    } finally {
      setBusy("");
      event.target.value = "";
    }
  };

  const sendMessage = async (event, text = draft) => {
    event?.preventDefault();
    const content = text.trim();
    if (!content || busy) return;

    const nextMessages = [...messages, { role: "user", content }];
    setMessages(nextMessages);
    setDraft("");
    setBusy("chat");
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMessages.slice(-20).map(({ role, content: messageContent }) => ({
            role,
            content: messageContent,
          })),
          source: source
            ? { title: source.title, source_url: source.source_url, content: source.content }
            : null,
        }),
      });
      const data = await readResponse(response);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.answer, safetyWarnings: data.safetyWarnings || [] },
      ]);
    } catch (requestError) {
      setError(requestError.message || "Could not send your message.");
    } finally {
      setBusy("");
    }
  };

  return (
    <main className="mx-auto flex min-h-[calc(100vh-57px)] w-full max-w-4xl flex-col gap-6 px-4 py-8 sm:px-6">
      <header>
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-zinc-500">Document assistant</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Chat with a document or ask anything</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Add a web page or text-based PDF for questions and summaries, or use chat without a source.
        </p>
      </header>

      <section className="grid gap-3 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4 sm:grid-cols-[1fr_auto]">
        <form onSubmit={loadUrl} className="flex min-w-0 gap-2">
          <input
            type="url"
            value={sourceUrl}
            onChange={(event) => setSourceUrl(event.target.value)}
            placeholder="Paste a web page or PDF link"
            disabled={Boolean(busy)}
            className="min-w-0 flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-sm outline-none placeholder:text-zinc-600 focus:border-amber-500/60 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={Boolean(busy) || !sourceUrl.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-3 py-2 text-sm hover:bg-zinc-700 disabled:opacity-50"
          >
            {busy === "source" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />}
            Load link
          </button>
        </form>
        <div className="flex items-center">
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,application/pdf"
            onChange={loadPdf}
            disabled={Boolean(busy)}
            className="sr-only"
            aria-label="Upload a PDF"
          />
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            disabled={Boolean(busy)}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-zinc-700 px-3 py-2.5 text-sm hover:border-amber-500/50 disabled:opacity-50"
          >
            <FileText className="h-4 w-4" />
            Upload PDF
          </button>
        </div>
      </section>

      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {source && (
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="flex items-center gap-2 text-sm font-medium text-zinc-100">
                <FileText className="h-4 w-4 shrink-0 text-amber-400" />
                <span className="truncate">{source.title}</span>
              </p>
              {source.source_url && (
                <a href={source.source_url} target="_blank" rel="noreferrer" className="mt-1 block truncate text-xs text-amber-300 underline">
                  {source.source_url}
                </a>
              )}
            </div>
            <button
              type="button"
              onClick={() => attachSource(null)}
              className="rounded p-1 text-zinc-500 hover:text-zinc-100"
              aria-label="Remove document"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
              <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-amber-300">
                <FileText className="h-3.5 w-3.5" />
                Copyright and license indicators
              </p>
              <p className="mt-2 text-xs leading-relaxed text-zinc-300">
                {source.copyright?.status === "indicators_found"
                  ? `Potential notice(s): ${source.copyright.indicators.join(", ")}`
                  : "No known notice was detected."}
              </p>
              <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">{source.copyright?.notice}</p>
            </div>
            <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 p-3">
              <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-sky-300">
                <ShieldAlert className="h-3.5 w-3.5" />
                Automated safety scan
              </p>
              <p className="mt-2 text-xs leading-relaxed text-zinc-300">
                {source.safetyWarnings?.length
                  ? `Potential flags: ${source.safetyWarnings.join(", ")}`
                  : "No configured keyword flags were detected."}
              </p>
              <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
                Checks are advisory and limited; flagged content is not blocked.
              </p>
            </div>
          </div>
        </section>
      )}

      <section className="flex min-h-72 flex-1 flex-col rounded-2xl border border-zinc-800 bg-zinc-900/30">
        <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6" aria-live="polite">
          {messages.length === 0 ? (
            <div className="flex h-full min-h-60 flex-col items-center justify-center text-center">
              <div className="rounded-full bg-amber-500/10 p-3 text-amber-300">
                <FileText className="h-5 w-5" />
              </div>
              <p className="mt-4 text-sm text-zinc-300">
                {source ? "Ask a question or summarize the attached source." : "Load a source or start a normal conversation."}
              </p>
              {source && (
                <button
                  type="button"
                  onClick={() => sendMessage(null, "Summarize this document and list its key points.")}
                  disabled={Boolean(busy)}
                  className="mt-3 rounded-lg border border-zinc-700 px-3 py-2 text-xs text-zinc-300 hover:border-amber-500/50 disabled:opacity-50"
                >
                  Summarize document
                </button>
              )}
            </div>
          ) : (
            messages.map((message, index) => (
              <article
                key={`${message.role}-${index}`}
                className={`max-w-[90%] whitespace-pre-wrap rounded-xl px-4 py-3 text-sm leading-relaxed ${
                  message.role === "user"
                    ? "ml-auto bg-amber-500 text-zinc-950"
                    : "mr-auto border border-zinc-800 bg-zinc-900 text-zinc-100"
                }`}
              >
                {message.content}
                {message.safetyWarnings?.length > 0 && (
                  <p className="mt-3 flex items-start gap-2 border-t border-sky-500/20 pt-2 text-xs text-sky-300">
                    <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    Safety review flagged: {message.safetyWarnings.join(", ")}. This is advisory, not a blocking decision.
                  </p>
                )}
              </article>
            ))
          )}
          {busy === "chat" && (
            <div className="mr-auto flex items-center gap-2 text-xs text-zinc-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Thinking…
            </div>
          )}
        </div>
        <form onSubmit={sendMessage} className="flex gap-2 border-t border-zinc-800 p-3 sm:p-4">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask a question or just chat…"
            maxLength={4000}
            disabled={Boolean(busy)}
            className="min-w-0 flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm outline-none placeholder:text-zinc-600 focus:border-amber-500/60 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={Boolean(busy) || !draft.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-3 text-sm font-medium text-zinc-950 hover:bg-amber-400 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-600"
          >
            <Send className="h-4 w-4" />
            Send
          </button>
        </form>
      </section>
    </main>
  );
}
