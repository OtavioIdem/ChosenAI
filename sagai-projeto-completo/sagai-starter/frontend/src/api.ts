import type { ChatResponse, FeedbackPayload, FeedbackResponse, KnowledgeStats } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function assertOk(response: Response, fallbackMessage: string) {
  if (response.ok) return;

  let detail = "";
  try {
    const body = await response.text();
    detail = body ? ` Detalhe: ${body.slice(0, 500)}` : "";
  } catch {
    detail = "";
  }

  throw new Error(`${fallbackMessage} Status: ${response.status}.${detail}`);
}

export async function askSagai(question: string, sessionId?: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      top_k: 5,
      allow_web_search: false,
      web_search_key: null
    })
  });

  await assertOk(response, "Falha ao consultar o SAGAI.");
  return response.json();
}

export async function sendFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  await assertOk(response, "Falha ao registrar feedback.");
  return response.json();
}

export async function fetchKnowledgeStats(): Promise<KnowledgeStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/knowledge/stats`);

  await assertOk(response, "Falha ao carregar estatísticas da base.");
  return response.json();
}
