# Organizador de Tarefas com IA

Este projeto é um organizador de tarefas que utiliza IA generativa para ajudar na organização e geração de tarefas.

## Tecnologias

- Python
- Streamlit
- Firebase
- Google Gemini API
- Genkit

## Instalação

1. Clone o repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`:

```
GOOGLE_GENAI_API_KEY=sua_chave_api_aqui
```

## Como Usar o @genkit no Projeto

# Start of Selection
Embora o projeto inicialmente visasse o uso do @genkit, após uma análise mais detalhada, percebemos que o @genkit não possui uma API Python oficial como suas versões em JavaScript e Go. No entanto, implementamos uma solução alternativa que simula a interface do Genkit, proporcionando uma experiência semelhante. Além disso, a interface do usuário do Genkit pode ser acessada no localhost:4000, o que torna o desenvolvimento e a interação ainda mais agradáveis.

### O que é o serviço implementado?

Criamos uma classe `GenerativeAIService` que oferece uma interface estruturada para trabalhar com a API Gemini do Google, permitindo:

1. Definição de fluxos de geração com modelos, prompts e configurações
2. Execução de fluxos com entrada de dados dinâmicos
3. Streaming de saída para atualização progressiva na interface Streamlit
4. Formatação e processamento dos resultados

### Configuração

Você precisa de:

1. Uma chave de API do Google AI (Gemini)
2. A biblioteca `google-generativeai` instalada

```bash
pip install google-generativeai
```

### Exemplos de Uso

#### Exemplo Básico:

```python
from genkit_service import GenerativeAIService

# Inicializar o serviço
service = GenerativeAIService(api_key="sua_chave_api")

# Criar um fluxo simples
flow = service.create_flow(
    name="meu_fluxo",
    prompt_template="Resuma o seguinte texto: {texto}",
    model="gemini-1.5-flash"
)

# Executar o fluxo
resultado = service.run_flow(flow, {"texto": "Um texto longo aqui..."})
print(resultado)
```

#### Usando com Streamlit:

O projeto inclui um exemplo completo em `genkit_example.py`. Para executá-lo:

```bash
streamlit run genkit_example.py
```

### Arquivos Principais

- `generative_ai_service.py`: Implementação do serviço GenerativeAI para uso com Streamlit
- `gemini_example.py`: Exemplo de aplicação Streamlit usando a API Gemini

## Executando o Projeto

```bash
streamlit run app.py
```

## Contribuições

Contribuições são bem-vindas! Abra um issue ou envie um pull request. 