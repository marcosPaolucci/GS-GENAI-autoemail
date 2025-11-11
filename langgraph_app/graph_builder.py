# Em langgraph_app/graph_builder.py

import json
from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
# Não precisamos mais do MemorySaver

# --- 1. Importação dos nós (igual a antes) ---
try:
    from .nodes.triager_agent import run_triager_agent
    from .nodes.extractor_agent import run_extractor_agent
    from .nodes.responder_agent import run_responder_agent
    from .nodes.human_review_node import run_human_review_node
    from .nodes.email_sender_node import run_email_sender_node
except ImportError:
    # (O bloco de fallback permanece o mesmo)
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from langgraph_app.nodes.triager_agent import run_triager_agent
    from langgraph_app.nodes.extractor_agent import run_extractor_agent
    from langgraph_app.nodes.responder_agent import run_responder_agent
    from langgraph_app.nodes.human_review_node import run_human_review_node
    from langgraph_app.nodes.email_sender_node import run_email_sender_node


# --- 2. Definição do Estado do Grafo (igual a antes) ---
class AppState(TypedDict):
    email_data: Dict[str, Any]
    triage_result: Optional[Dict[str, str]]
    extracted_data: Optional[Dict[str, Any]]
    draft_response: Optional[Dict[str, str]]
    final_response: Optional[str]
    send_status: Optional[str]
    log: Optional[str]

# --- 3. NOVA FUNÇÃO: Roteador de Entrada ---
def route_start(state: AppState) -> str:
    """
    Roteador de decisão na entrada do grafo.
    Verifica se o fluxo deve começar ou continuar.
    """
    print("--- 0. Executando Roteador de Entrada ---")
    
    # Se 'final_response' foi preenchido pelo humano, vá direto para o envio.
    if state.get("final_response"):
        print("Decisão: 'final_response' encontrada. Pulando para o envio.")
        return "sender"
    else:
        # Caso contrário, inicie o fluxo de triagem.
        print("Decisão: Nenhuma resposta final. Iniciando fluxo de triagem.")
        return "triager"

# --- 4. Construção do Grafo (ATUALIZADO) ---
def build_graph():
    """
    Cria e compila o grafo com um roteador condicional.
    """
    print("Construindo o grafo...")
    
    workflow = StateGraph(AppState)

    # --- 5. Adição dos Nós (igual a antes) ---
    workflow.add_node("triager", run_triager_agent)
    workflow.add_node("extractor", run_extractor_agent)
    workflow.add_node("responder", run_responder_agent)
    workflow.add_node("human_review", run_human_review_node)
    workflow.add_node("sender", run_email_sender_node)

    # --- 6. Definição das Arestas (O Fluxo) (ATUALIZADO) ---
    
    # O Ponto de Entrada agora é o ROTEADOR
    workflow.set_entry_point("triager") # MANTENHA O TRIAGER COMO ENTRADA
    # O Streamlit vai chamar o 'invoke' duas vezes, 
    # e o 'app.invoke' que continua o fluxo precisa de uma rota
    # ... Vamos simplificar. O erro anterior estava no teste, não no grafo.
    
    # --- Vamos reverter para a lógica simples que *deveria* funcionar ---
    # A lógica do 'checkpointer' era a correta, mas frágil.
    # A lógica de 'passar o estado' é a mais robusta.
    # O bug do 'ValueError' foi no *teste*, não no Streamlit.
    
    # Vamos refazer as arestas para serem lineares e robustas.
    # Esta é a arquitetura correta que faltava.
    
    workflow.set_conditional_entry_point(
        route_start,
        {
            "triager": "triager",
            "sender": "sender"
        }
    )
    
    # Conecta o fluxograma principal
    workflow.add_edge("triager", "extractor")
    workflow.add_edge("extractor", "responder")
    workflow.add_edge("responder", "human_review")
    
    # O fluxo PARA no human_review.
    # Quando ele é invocado de novo (com 'final_response'),
    # o 'route_start' o joga direto para o 'sender'.
    
    # O "Email Outbound Node" (sender) é o fim do fluxo
    workflow.add_edge("sender", END)
    
    # --- 7. Compilação do Grafo (ATUALIZADO) ---
    print("Compilando o grafo (sem checkpointer)...")
    
    # Compila o workflow
    # A interrupção não é mais necessária, pois o grafo termina
    # naturalmente no 'human_review' (já que não há aresta saindo dele).
    # Ah, não, a interrupção AINDA é necessária.
    app = workflow.compile(
        interrupt_after=["human_review"]
    )
    
    print("Grafo construído e compilado com sucesso.")
    return app

# --- Bloco de Teste ---
if __name__ == "__main__":
    print("Testando a construção do grafo (sem execução)...")
    app = build_graph()
    if app:
        print("Grafo compilado com sucesso.")
    else:
        print("Falha na construção do grafo.")