import json
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# Importa nosso cliente LLM
try:
    from ..utils.openai_client import get_llm_client
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from langgraph_app.utils.openai_client import get_llm_client

# --- 1. Definição do Esquema de Saída (Opcional, mas recomendado) ---
# Mesmo para geração de texto, podemos estruturar a saída
# para garantir que o LLM pense passo a passo.

class DraftResponse(BaseModel):
    """Define a estrutura para o rascunho da resposta do e-mail."""
    corpo_email: str = Field(..., description="O texto completo do rascunho da resposta a ser enviado ao usuário.")
    tom_sugerido: str = Field("Empático e Resolutivo", description="O tom usado na redação da resposta.")
    proximo_passo: str = Field(..., description="A ação interna sugerida (ex: 'Encaminhar ao time de logística', 'Verificar pagamento').")


# --- 2. Criação do Agente (Nó) ---

def run_responder_agent(state: dict):
    """
    Executa o agente redator de resposta (Nó "Agent 3").
    
    Ele usa o contexto da triagem e dos dados extraídos para
    gerar um rascunho de resposta personalizado.
    """
    print("--- 3. Executando Agente Redator de Resposta ---")
    
    # Coleta todas as informações do estado
    triage_result = state.get("triage_result", {})
    extracted_data = state.get("extracted_data", {})
    email_data = state.get("email_data", {})

    # Prepara o "contexto" para o LLM
    contexto = f"""
    --- Contexto do E-mail Original ---
    De: {email_data.get('headers', {}).get('From')}
    Assunto: {email_data.get('headers', {}).get('Subject')}
    Corpo:
    {email_data.get('body')}

    --- Análise da Triagem (Agente 1) ---
    Categoria: {triage_result.get('categoria')}
    Prioridade: {triage_result.get('prioridade')}
    Motivo: {triage_result.get('motivo')}

    --- Dados Extraídos (Agente 2) ---
    {json.dumps(extracted_data, indent=2, ensure_ascii=False)}
    """
    
    # O redator deve ser mais "criativo" que os outros
    llm = get_llm_client(model_name="gpt-4o-mini", temperature=0.5)
    structured_llm = llm.with_structured_output(DraftResponse)

    # Prompt focado na persona de atendimento
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "Você é um assistente de atendimento ao cliente excepcional, "
         "especializado em redigir respostas de e-mail claras, empáticas e eficientes. "
         "Seu objetivo é resolver o problema do cliente ou encaminhá-lo corretamente "
         "com base no contexto fornecido. Assine o e-mail como 'Equipe Smart Inbox'.\n"
         "Gere a resposta em Português do Brasil."),
        ("human", 
         "Por favor, use o contexto abaixo para gerar um rascunho de resposta "
         "apropriado e definir o próximo passo interno.\n\n"
         "{contexto}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        response_draft = chain.invoke({"contexto": contexto})
        
        print(f"Rascunho da Resposta Gerado:\n{response_draft.corpo_email}")
        
        # Retorna o rascunho para mesclar ao estado
        return {
            "draft_response": {
                "body": response_draft.corpo_email,
                "tom": response_draft.tom_sugerido,
                "next_step": response_draft.proximo_passo
            }
        }
        
    except Exception as e:
        print(f"Erro no Agente Redator: {e}")
        return {
            "draft_response": {
                "body": "Falha ao gerar rascunho da resposta.",
                "erro": str(e)
            }
        }

# --- Bloco de Teste ---
if __name__ == "__main__":
    print("Testando o Agente Redator de Resposta (Responder Agent)...")
    
    # Simula o estado do grafo APÓS os Agentes 1 e 2
    mock_state_after_extraction = {
        "email_data": {
            "id": "12345",
            "thread_id": "thread-abc",
            "headers": {
                "From": "Cliente Irritado <cliente.irritado@exemplo.com>",
                "Subject": "URGENTE: Meu pedido não chegou!"
            },
            "body": """
            Olá,
            Eu fiz um pedido (#98765) há duas semanas e o rastreio diz que 
            foi entregue, mas eu não recebi nada!
            Isso é um absurdo! Onde está minha encomenda? Eu preciso disso para ontem!
            Resolvam isso ou quero meu dinheiro de volta.
            Atenciosamente,
            Cliente
            """
        },
        "triage_result": {
            "categoria": "Suporte Técnico",
            "prioridade": "Alta",
            "motivo": "O e-mail é de um cliente insatisfeito..."
        },
        "extracted_data": {
            "remetente_nome": "Cliente",
            "numero_pedido": "98765",
            "produto_afetado": None,
            "resumo_problema": "O pedido foi marcado como entregue, mas o cliente não recebeu nada.",
            "intencao": "Solicitar reembolso"
        }
    }
    
    # Executa a função do nó
    response_result_state = run_responder_agent(mock_state_after_extraction)
    
    print("\n--- Resultado do Teste ---")
    print(json.dumps(response_result_state, indent=2, ensure_ascii=False))  