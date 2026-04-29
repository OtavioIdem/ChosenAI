import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { askSagai, fetchKnowledgeStats, sendFeedback } from "./api";
import type { ChatResponse, FeedbackPayload, KnowledgeStats } from "./types";

const appName = import.meta.env.VITE_APP_NAME ?? "SAGAI";

type FeedbackRating = FeedbackPayload["rating"];

type UiMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  response?: ChatResponse;
  createdAt: Date;
};

function formatPercent(value?: number) {
  if (typeof value !== "number") return "0%";
  return `${Math.round(value * 100)}%`;
}

function confidenceLabel(status?: ChatResponse["confidence_status"]) {
  switch (status) {
    case "high":
      return "Alta confiança";
    case "medium":
      return "Confiança média";
    case "low":
      return "Baixa confiança";
    default:
      return "Sem avaliação";
  }
}

function nowId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [filesModalOpen, setFilesModalOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const indexedFiles = stats?.indexed_files ?? [];
  const latestAssistantResponse = [...messages].reverse().find((message) => message.role === "assistant" && message.response)?.response;

  const canSubmit = useMemo(() => question.trim().length >= 3 && !loading, [question, loading]);

  useEffect(() => {
    const loadStats = async () => {
      setStatsLoading(true);
      try {
        const data = await fetchKnowledgeStats();
        setStats(data);
      } catch (err) {
        console.error(err);
      } finally {
        setStatsLoading(false);
      }
    };

    void loadStats();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
  }, [question]);

  const handleAsk = async () => {
    if (!canSubmit) return;

    const cleanQuestion = question.trim();
    const userMessage: UiMessage = {
      id: nowId("user"),
      role: "user",
      content: cleanQuestion,
      createdAt: new Date()
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setLoading(true);
    setError(null);

    try {
      const data = await askSagai(cleanQuestion, sessionId);
      setSessionId(data.session_id);

      const assistantMessage: UiMessage = {
        id: data.assistant_message_id ?? nowId("assistant"),
        role: "assistant",
        content: data.answer,
        response: data,
        createdAt: new Date()
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage = "Não foi possível consultar o SAGAI. Verifique se o backend e o Ollama estão ativos.";
      setError(errorMessage);
      setMessages((current) => [
        ...current,
        {
          id: nowId("system-error"),
          role: "system",
          content: errorMessage,
          createdAt: new Date()
        }
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void handleAsk();
  };

  const handleTextareaKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleAsk();
    }
  };

  const handleFeedback = async (response: ChatResponse, rating: FeedbackRating) => {
    try {
      const result = await sendFeedback({
        message_id: response.assistant_message_id,
        rating,
        create_training_candidate: true
      });

      setFeedbackSent((current) => ({
        ...current,
        [response.assistant_message_id]: result.training_candidate_id
          ? "Feedback registrado e candidato de treinamento criado."
          : "Feedback registrado."
      }));
    } catch (err) {
      console.error(err);
      setFeedbackSent((current) => ({
        ...current,
        [response.assistant_message_id]: "Não foi possível registrar o feedback."
      }));
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(undefined);
    setFeedbackSent({});
    setError(null);
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="brandCard">
          <span className="eyebrow">Projeto</span>
          <h1>{appName}</h1>
          <p>
            Assistente documental focado no MaxManager para suporte N1, treinamento e apoio interno.
          </p>
        </div>

        <button className="newChatButton" onClick={handleNewChat} type="button">
          + Nova conversa
        </button>

        <section className="sidebarCard">
          <span className="eyebrow">Base de conhecimento</span>

          {statsLoading ? (
            <p className="muted">Carregando estatísticas...</p>
          ) : (
            <>
              <div className="statsGrid">
                <div>
                  <strong>{stats?.sources_count ?? 0}</strong>
                  <span>Fontes</span>
                </div>
                <div>
                  <strong>{stats?.chunks_count ?? 0}</strong>
                  <span>Trechos</span>
                </div>
              </div>

              <button className="outlineButton full" type="button" onClick={() => setFilesModalOpen(true)}>
                Ver arquivos indexados
              </button>

              {indexedFiles.length === 0 ? (
                <p className="muted smallText">
                  Nenhum JSON indexado ainda. Adicione arquivos em <code>backend/knowledge/json</code> e rode a reindexação.
                </p>
              ) : (
                <p className="muted smallText">
                  {indexedFiles.length} arquivo(s) disponível(is) para consulta documental.
                </p>
              )}
            </>
          )}
        </section>

        <section className="sidebarCard">
          <span className="eyebrow">Aprendizado</span>
          <div className="infoBlock">
            <strong>Feedback supervisionado</strong>
            <p>Cada avaliação pode virar candidato de treinamento para auditoria.</p>
          </div>
          <div className="infoBlock">
            <strong>Lacunas</strong>
            <p>Baixa confiança gera oportunidade de evolução da base.</p>
          </div>
        </section>

        {latestAssistantResponse ? (
          <section className="sidebarCard compact">
            <span className="eyebrow">Última resposta</span>
            <div className={`statusDot ${latestAssistantResponse.confidence_status}`}>
              {confidenceLabel(latestAssistantResponse.confidence_status)} · {formatPercent(latestAssistantResponse.confidence_score)}
            </div>
          </section>
        ) : null}
      </aside>

      <main className="chatArea">
        <header className="chatHeader">
          <div>
            <span className="eyebrow">Consulta</span>
            <h2>Pergunte ao SAGAI</h2>
          </div>
          <div className="headerMeta">
            <span>{stats?.sources_count ?? 0} fontes</span>
            <span>{stats?.chunks_count ?? 0} trechos</span>
          </div>
        </header>

        <section className="messagesPanel">
          {messages.length === 0 ? (
            <div className="emptyState">
              <div className="emptyIcon">S</div>
              <h3>Como posso ajudar no MaxManager?</h3>
              <p>
                Faça perguntas sobre processos, rotinas, cadastros, fiscal, financeiro, NF-e, SPED e demais áreas documentadas.
              </p>
              <div className="suggestions">
                <button type="button" onClick={() => setQuestion("Como criar uma nota fiscal de entrada?")}>Como criar uma nota fiscal de entrada?</button>
                <button type="button" onClick={() => setQuestion("Como gerar SPED no MaxManager?")}>Como gerar SPED no MaxManager?</button>
                <button type="button" onClick={() => setQuestion("Como consultar contas a receber?")}>Como consultar contas a receber?</button>
              </div>
            </div>
          ) : (
            <div className="messagesList">
              {messages.map((message) => (
                <article key={message.id} className={`messageRow ${message.role}`}>
                  <div className="avatar">{message.role === "user" ? "Você" : message.role === "assistant" ? "S" : "!"}</div>
                  <div className="messageBubble">
                    <div className="messageHeader">
                      <strong>{message.role === "user" ? "Você" : message.role === "assistant" ? "SAGAI" : "Sistema"}</strong>
                      <span>{message.createdAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</span>
                    </div>

                    <div className="messageContent">{message.content}</div>

                    {message.response ? (
                      <ResponseDetails
                        response={message.response}
                        feedbackMessage={feedbackSent[message.response.assistant_message_id]}
                        onFeedback={handleFeedback}
                      />
                    ) : null}
                  </div>
                </article>
              ))}

              {loading ? (
                <article className="messageRow assistant">
                  <div className="avatar">S</div>
                  <div className="messageBubble loadingBubble">
                    <div className="typingDots" aria-label="Consultando SAGAI">
                      <span />
                      <span />
                      <span />
                    </div>
                    <p>Consultando SAGAI e analisando a base documental...</p>
                  </div>
                </article>
              ) : null}

              <div ref={messagesEndRef} />
            </div>
          )}
        </section>

        <form className="composer" onSubmit={handleSubmit}>
          {error ? <div className="composerError">{error}</div> : null}
          <div className="composerBox">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleTextareaKeyDown}
              placeholder="Pergunte ao SAGAI..."
              rows={1}
              disabled={loading}
            />
            <button className="sendButton" type="submit" disabled={!canSubmit}>
              {loading ? "..." : "Enviar"}
            </button>
          </div>
          <p className="composerHint">Enter para enviar · Shift + Enter para quebrar linha</p>
        </form>
      </main>

      <FilesModal
        open={filesModalOpen}
        files={indexedFiles}
        onClose={() => setFilesModalOpen(false)}
      />
    </div>
  );
}

type ResponseDetailsProps = {
  response: ChatResponse;
  feedbackMessage?: string;
  onFeedback: (response: ChatResponse, rating: FeedbackRating) => void;
};

function ResponseDetails({ response, feedbackMessage, onFeedback }: ResponseDetailsProps) {
  const [sourcesOpen, setSourcesOpen] = useState(false);

  return (
    <div className="responseMeta">
      <div className="metaChips">
        <span className={`chip ${response.confidence_status}`}>
          {confidenceLabel(response.confidence_status)} · {formatPercent(response.confidence_score)}
        </span>
        <span className="chip">Modo: {response.mode}</span>
        {response.knowledge_gap_id ? <span className="chip warning">Lacuna criada</span> : null}
      </div>

      {response.warnings.length > 0 ? (
        <div className="warningBox">
          {response.warnings.map((warning) => (
            <div key={warning}>{warning}</div>
          ))}
        </div>
      ) : null}

      <div className="messageActions">
        <button type="button" onClick={() => onFeedback(response, "useful")}>Útil</button>
        <button type="button" onClick={() => onFeedback(response, "incomplete")}>Incompleta</button>
        <button type="button" onClick={() => onFeedback(response, "incorrect")}>Incorreta</button>
        <button type="button" onClick={() => onFeedback(response, "bad_source")}>Fonte ruim</button>
        <button type="button" onClick={() => setSourcesOpen(true)}>
          Fontes ({response.sources.length})
        </button>
      </div>

      {feedbackMessage ? <div className="feedbackNotice">{feedbackMessage}</div> : null}

      <SourcesModal
        open={sourcesOpen}
        sources={response.sources}
        onClose={() => setSourcesOpen(false)}
      />
    </div>
  );
}

type FilesModalProps = {
  open: boolean;
  files: string[];
  onClose: () => void;
};

function FilesModal({ open, files, onClose }: FilesModalProps) {
  if (!open) return null;

  return (
    <div className="modalOverlay" role="dialog" aria-modal="true">
      <div className="modal largeModal">
        <div className="modalHeader">
          <div>
            <span className="eyebrow">Base documental</span>
            <h3>Arquivos indexados</h3>
          </div>
          <button className="iconButton" type="button" onClick={onClose}>×</button>
        </div>

        <div className="modalContent">
          {files.length === 0 ? (
            <p className="muted">Nenhum arquivo indexado ainda.</p>
          ) : (
            <div className="filesList">
              {files.map((file) => (
                <div key={file} className="fileItem">
                  <span>{file}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

type SourcesModalProps = {
  open: boolean;
  sources: ChatResponse["sources"];
  onClose: () => void;
};

function SourcesModal({ open, sources, onClose }: SourcesModalProps) {
  if (!open) return null;

  return (
    <div className="modalOverlay" role="dialog" aria-modal="true">
      <div className="modal largeModal">
        <div className="modalHeader">
          <div>
            <span className="eyebrow">Resposta</span>
            <h3>Fontes recuperadas</h3>
          </div>
          <button className="iconButton" type="button" onClick={onClose}>×</button>
        </div>

        <div className="modalContent">
          {sources.length === 0 ? (
            <p className="muted">Nenhuma fonte retornada para esta resposta.</p>
          ) : (
            <div className="sourceList">
              {sources.map((source) => (
                <article key={`${source.source_identifier}-${source.chunk_index}`} className="sourceCard">
                  <div className="sourceHeader">
                    <strong>{source.title}</strong>
                    <span>score {source.score.toFixed(2)}</span>
                  </div>
                  <div className="muted smallText">{source.source_identifier}</div>
                  <p>{source.excerpt}</p>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
