from pydantic import BaseModel, Field
from typing import Optional, Literal

from langchain_core.prompts import ChatPromptTemplate

# Importa nosso cliente LLM
try:
    from ..utils.openai_client import get_llm_client
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from langgraph_app.utils.openai_client import get_llm_client

# --- 1. Definição dos Esquemas de Extração (Pydantic) ---

class SupportExtraction(BaseModel):
    """Esquema para extrair dados de e-mails de Suporte Técnico."""
    remetente_nome: str = Field(
        ..., 
        description="O nome do cliente ou remetente. **Priorize o nome na assinatura do corpo do e-mail, se houver.**"
    )
    numero_pedido: Optional[str] = Field(None, description="O número do pedido ou ID de referência, se mencionado.")
    produto_afetado: Optional[str] = Field(None, description="O nome do produto ou serviço com problema.")
    resumo_problema: str = Field(..., description="Um resumo conciso do problema relatado pelo cliente.")
    intencao: str = Field(..., description="A intenção principal (ex: 'Solicitar reembolso', 'Pedir ajuda', 'Relatar bug').")

class QuoteExtraction(BaseModel):
    """Esquema para extrair dados de e-mails de Orçamento/Vendas."""
    remetente_nome: str = Field(
        ..., 
        description="O nome do potencial cliente. **Priorize o nome na assinatura do corpo do e-mail.**"
    )
    nome_empresa: Optional[str] = Field(None, description="O nome da empresa do remetente, se mencionado.")
    produto_solicitado: str = Field(..., description="O produto ou serviço para o qual estão pedindo um orçamento.")
    quantidade: Optional[str] = Field(None, description="A quantidade desejada, se especificada.")
    intencao: Literal["Solicitar Orçamento"] = Field("Solicitar Orçamento", description="A intenção do e-mail.")

class RHExtraction(BaseModel):
    """Esquema para extrair dados de e-mails de RH."""
    remetente_nome: str = Field(
        ..., 
        description="O nome do candidato ou remetente. **Priorize o nome na assinatura do corpo do e-mail.**"
    )
    vaga_interesse: Optional[str] = Field(None, description="A vaga de emprego à qual o candidato está se aplicando.")
    assunto_rh: str = Field(..., description="O tópico principal (ex: 'Candidatura', 'Benefícios', 'Entrevista').")
    intencao: Literal["Candidatura", "Consulta RH", "Outro"] = Field(..., description="A intenção do remetente.")

class GeneralExtraction(BaseModel):
    """Esquema de fallback para e-mails de categoria 'Outros'."""
    remetente_nome: str = Field(
        ..., 
        description="O nome do remetente. **Priorize o nome na assinatura do corpo do e-mail.**"
    )
    intencao: str = Field(..., description="A intenção ou pergunta principal do remetente.")
    resumo_email: str = Field(..., description="Um resumo de 1-2 frases do conteúdo do e-mail.")


# --- 2. Criação do Agente (Nó) ---

def run_extractor_agent(state: dict):
    """
    Executa o agente extrator de dados (Nó "Agent 2").
    """
    print("--- 2. Executando Agente Extrator de Dados ---")
    
    email_data = state.get("email_data", {})
    triage_result = state.get("triage_result", {})
    categoria = triage_result.get("categoria", "Outros")
    
    email_content = f"""
    De: {email_data.get('headers', {}).get('From')}
    Assunto: {email_data.get('headers', {}).get('Subject')}
    Corpo:
    {email_data.get('body')}
    """

    schema_map = {
        "Suporte Técnico": SupportExtraction,
        "Orçamento": QuoteExtraction,
        "RH": RHExtraction,
        "Vendas": QuoteExtraction,
        "Outros": GeneralExtraction
    }
    
    ExtractionSchema = schema_map.get(categoria, GeneralExtraction)
    
    print(f"Categoria da Triagem: '{categoria}'. Usando esquema de extração: '{ExtractionSchema.__name__}'")
    
    llm = get_llm_client(temperature=0.0)
    structured_llm = llm.with_structured_output(ExtractionSchema)
    
    # --- 💡 AJUSTE NO PROMPT AQUI 💡 ---
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "Você é um especialista em extração de dados. "
         "Seu trabalho é analisar o e-mail a seguir e extrair as informações relevantes "
         "com base no esquema JSON fornecido. Seja preciso e extraia apenas os dados mencionados no texto. "
         "**IMPORTANTE para 'remetente_nome': Sempre priorize o nome encontrado na assinatura ou no final do corpo do e-mail. "
         "Use o nome do cabeçalho 'De:' (From) apenas como última opção se nenhum nome for encontrado no corpo.**"),
        ("human", 
         "Por favor, extraia os dados deste e-mail para uma solicitação de '{categoria}':\n\n"
         "{email_content}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        extraction_result = chain.invoke({
            "categoria": categoria,
            "email_content": email_content
        })
        
        extracted_data_dict = extraction_result.model_dump()
        
        print(f"Dados Extraídos: {extracted_data_dict}")
        
        return {"extracted_data": extracted_data_dict}
        
    except Exception as e:
        print(f"Erro no Agente Extrator: {e}")
        return {
            "extracted_data": {
                "erro": "Falha ao extrair dados",
                "detalhes": str(e)
            }
        }

# --- Bloco de Teste (Permanece o mesmo) ---
if __name__ == "__main__":
    # ... (o bloco de teste não precisa mudar) ...
    print("Testando o Agente Extrator de Dados (Extractor Agent)...")
    
    mock_state_after_triage = {
        "email_data": {
            "id": "12345",
            "headers": {
                "From": "marcos.salamondac@exemplo.com", # <- Nome "errado"
                "Subject": "URGENTE: Meu pedido não chegou!"
            },
            "body": """
            Olá,
            Eu fiz um pedido (#98765) ...
            Atenciosamente,
            João Silva 
            """ # <- Nome "certo"
        },
        "triage_result": {
            "categoria": "Suporte Técnico",
            "prioridade": "Alta",
            "motivo": "O e-mail é de um cliente insatisfeito..."
        }
    }
    
    extraction_result_state = run_extractor_agent(mock_state_after_triage)
    
    print("\n--- Resultado do Teste ---")
    import json
    print(json.dumps(extraction_result_state, indent=2, ensure_ascii=False))