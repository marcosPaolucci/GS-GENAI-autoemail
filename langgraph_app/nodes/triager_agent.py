# --- 1. CORREÇÃO DO PYDANTIC ---
# Trocamos as importações obsoletas do 'langchain_core.pydantic_v1'
from pydantic import BaseModel, Field
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
# Não precisamos mais do 'langchain_core.pydantic_v1'

# Importa nosso cliente LLM
try:
    from ..utils.openai_client import get_llm_client
except ImportError:
    # O fallback agora está correto para o caso de
    # ser executado de formas inesperadas, mas o -m é o ideal.
    import sys
    import os
    # Adiciona o diretório raiz ao path para encontrar 'langgraph_app'
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from langgraph_app.utils.openai_client import get_llm_client

# --- 2. CORREÇÃO DO PYDANTIC ---
# Mudamos de 'V1BaseModel' para 'BaseModel' (do Pydantic v2)
class TriageOutput(BaseModel):
    """
    Define a estrutura de saída para o agente de triagem de e-mails.
    O modelo de IA será forçado a preencher estes campos.
    """
    categoria: Literal[
        "Suporte Técnico", 
        "Orçamento", 
        "RH", 
        "Vendas", 
        "Outros"
    ] = Field(..., description="A categoria principal do e-mail.")
    
    prioridade: Literal["Alta", "Média", "Baixa"] = Field(
        ..., description="A prioridade da solicitação, baseada na urgência."
    )
    
    motivo_triagem: str = Field(
        ..., 
        description="Uma breve explicação (1 frase) sobre o porquê desta categoria e prioridade."
    )

# --- O restante do código permanece igual ---

def run_triager_agent(state: dict):
    """
    Executa o agente de triagem (Nó "Agent 1").
    """
    print("--- 1. Executando Agente Triador ---")
    
    email_data = state.get("email_data")
    if not email_data:
        raise ValueError("Dados do e-mail não encontrados no estado.")
    
    email_body = email_data.get("body", "")
    email_subject = email_data.get("headers", {}).get("Subject", "")
    email_from = email_data.get("headers", {}).get("From", "")
    
    email_content = f"""
    De: {email_from}
    Assunto: {email_subject}
    Corpo:
    {email_body}
    """
    
    llm = get_llm_client(temperature=0.0)
    structured_llm = llm.with_structured_output(TriageOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "Você é um assistente de triagem de e-mails altamente eficiente. "
         "Seu trabalho é analisar o e-mail a seguir, classificá-lo em uma das "
         "categorias predefinidas e definir seu nível de prioridade. "
         "Responda *apenas* com a estrutura de dados JSON solicitada."),
        ("human", "Por favor, analise o seguinte e-mail:\n\n{email_content}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        triage_result = chain.invoke({"email_content": email_content})
        
        print(f"Resultado da Triagem: Categoria={triage_result.categoria}, Prioridade={triage_result.prioridade}")
        
        return {
            "triage_result": {
                "categoria": triage_result.categoria,
                "prioridade": triage_result.prioridade,
                "motivo": triage_result.motivo_triagem
            }
        }
        
    except Exception as e:
        print(f"Erro no Agente Triador: {e}")
        return {
            "triage_result": {
                "categoria": "Falha na Triagem",
                "prioridade": "N/A",
                "motivo": str(e)
            }
        }

# --- Bloco de Teste ---
if __name__ == "__main__":
    print("Testando o Agente Triador (Triager Agent)...")
    
    mock_state = {
        "email_data": {
            "id": "12345",
            "headers": {
                "From": "cliente.irritado@exemplo.com",
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
        }
    }
    
    triage_result_state = run_triager_agent(mock_state)
    
    print("\n--- Resultado do Teste ---")
    import json
    # Usando .model_dump_json() que é o padrão do Pydantic v2
    # E garantindo que a saída seja formatada
    if "triage_result" in triage_result_state:
        # Se for um dict, apenas dumpar
        print(json.dumps(triage_result_state, indent=2, ensure_ascii=False))