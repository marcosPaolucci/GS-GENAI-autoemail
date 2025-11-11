# --- Criação do Nó ---
import json

def run_human_review_node(state: dict):
    """
    Nó "Human Review Node" (Revisão Humana).

    Este nó é um "pass-through". Ele não executa lógica de IA.
    Sua única função é atuar como um PONTO DE PARADA (breakpoint)
    no grafo.

    O 'graph_builder.py' (próximo arquivo) será configurado para 
    *interromper* a execução do grafo *após* este nó.
    
    A interface (Streamlit) irá:
    1. Executar o grafo até este ponto de interrupção.
    2. Pegar o 'draft_response' do estado.
    3. Mostrar ao usuário para aprovação/edição.
    4. Receber a 'final_response' (editada ou aprovada).
    5. Continuar a execução do grafo, injetando a 'final_response'.
    """
    print("--- 4. AGUARDANDO REVISÃO HUMANA ---")
    
    # O rascunho já está no estado, vindo do nó anterior
    draft = state.get("draft_response", {}).get("body", "Erro: Rascunho não encontrado.")
    
    print("Rascunho gerado. O grafo será pausado para aprovação do usuário.")
    print(f"Rascunho (prévia): \n{draft[:200]}...")
    
    # Não retorna nada de novo, apenas sinaliza a passagem.
    # O estado permanece o mesmo, pronto para a interrupção.
    return {}

# --- Bloco de Teste ---
if __name__ == "__main__":
    print("Testando o Nó de Revisão Humana (Human Review Node)...")
    
    # Simula o estado após o Agente 3
    mock_state_after_draft = {
         "email_data": {"id": "123"},
         "triage_result": {"categoria": "Suporte"},
         "extracted_data": {"nome": "Cliente"},
         "draft_response": {
            "body": "Olá Cliente,\n\nEste é um e-mail de teste...",
            "tom": "Amigável",
            "next_step": "Aguardar."
         }
    }
    print("\nEstado de entrada:")
    print(json.dumps(mock_state_after_draft, indent=2, ensure_ascii=False))
    
    # Executa a função do nó
    run_human_review_node(mock_state_after_draft)
    
    print("\nTeste concluído. O nó apenas imprimiu o status de espera.")