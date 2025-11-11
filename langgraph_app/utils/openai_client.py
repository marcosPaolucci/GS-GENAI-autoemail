from langchain_openai import ChatOpenAI

try:
    # Importação relativa para quando o app estiver rodando
    from .config import OPENAI_API_KEY
except ImportError:
    # Fallback para testes diretos (se necessário)
    from config import OPENAI_API_KEY

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY não encontrada no arquivo .env. "
        "Por favor, defina a chave de API da OpenAI."
    )

def get_llm_client(model_name: str = "gpt-4o-mini", temperature: float = 0.0):
    """
    Inicializa e retorna uma instância do cliente LLM (ChatOpenAI).

    Esta função "fabrica" o cérebro que os agentes usarão.
    Usamos temperature=0.0 para tarefas de classificação e extração,
    pois queremos respostas consistentes e previsíveis.

    Args:
        model_name: O nome do modelo da OpenAI a ser usado (ex: "gpt-4o", "gpt-3.5-turbo").
        temperature: O nível de criatividade (0.0 = determinístico).

    Returns:
        Uma instância de ChatOpenAI.
    """
    client = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=OPENAI_API_KEY
    )
    return client


# --- Bloco para testar este módulo ---
if __name__ == "__main__":
    print("Testando o cliente OpenAI...")
    try:
        llm = get_llm_client()
        print("Instância do ChatOpenAI criada com sucesso.")
        
        print("Testando uma chamada simples (invoke)...")
        # Simula uma chamada simples
        response = llm.invoke("Qual é a capital do Brasil?")
        
        print(f"\nResposta do modelo: {response.content}")
        print("\nCliente OpenAI configurado e funcionando!")
        
    except Exception as e:
        print(f"\nOcorreu um erro ao testar o cliente OpenAI:")
        print(f"Erro: {e}")
        print("Verifique se sua OPENAI_API_KEY está correta no arquivo .env.")