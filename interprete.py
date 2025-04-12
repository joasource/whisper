import re
import time
import argparse
from openai import OpenAI

# 🔐 Sua chave secreta da OpenAI
client = OpenAI(api_key="SUA CHAVE API")

def traduzir_texto(texto):
    role_prompt = f"""
Você é um tradutor profissional com profundo conhecimento em Jiu-Jitsu Brasileiro.
Traduza o seguinte texto do inglês para o português brasileiro, usando termos técnicos corretos do Jiu-Jitsu.
**Não adicione comentários, introduções, explicações ou qualquer texto extra.**
Responda apenas com a tradução fiel do conteúdo.

## Vocabulário técnico:
- half guard = meia guarda
- Belt = faixa
- sweep = raspar ou raspagem (depende do contexto)
- side control = cem quilo
- hip scape = fuga de quadril
- z-guard = meia escudo

Texto a ser traduzido:
{texto}
"""

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um tradutor técnico de inglês para português, com foco em Jiu-Jitsu Brasileiro. Use apenas a tradução como resposta."},
            {"role": "user", "content": role_prompt}
        ],
        temperature=0.2
    )
    return resposta.choices[0].message.content.strip()

def limpar_traducao(texto):
    """Remove qualquer introdução desnecessária que o modelo possa ter colocado."""
    return re.sub(
        r"^(claro,?\s*)?(aqui está a tradução.*?:|# legenda traduzida:)",
        "",
        texto,
        flags=re.IGNORECASE
    ).strip()

def ler_srt(arquivo):
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    blocos = re.findall(r'(\d+)\r?\n([\d:,]+ --> [\d:,]+)\r?\n(.*?)(?=\r?\n\r?\n|\Z)', conteudo, re.DOTALL)
    return blocos

def salvar_srt(blocos_traduzidos, arquivo_saida):
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        for idx, (num, tempo, texto) in enumerate(blocos_traduzidos, 1):
            f.write(f"{idx}\n{tempo}\n{texto.strip()}\n\n")

def traduzir_srt(arquivo_entrada, arquivo_saida):
    blocos = ler_srt(arquivo_entrada)
    print(f"🔍 {len(blocos)} blocos encontrados no SRT\n")

    blocos_traduzidos = []
    for numero, tempo, texto in blocos:
        texto_limpo = texto.replace('\n', ' ').replace('\r', ' ').strip()
        print(f"🔁 Bloco {numero}: {texto_limpo}")
        try:
            traducao_bruta = traduzir_texto(texto_limpo)
            traducao = limpar_traducao(traducao_bruta)
            print(f"✅ Tradução: {traducao}\n")
        except Exception as e:
            print(f"❌ Erro no bloco {numero}: {e}")
            traducao = texto_limpo
        blocos_traduzidos.append((numero, tempo, traducao))
        time.sleep(1.2)

    salvar_srt(blocos_traduzidos, arquivo_saida)
    print(f"\n✅ Tradução finalizada! Arquivo salvo como: {arquivo_saida}")

# 🖥️ CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traduz um arquivo .srt de inglês para português com termos técnicos de Jiu-Jitsu.")
    parser.add_argument("entrada", help="Arquivo .srt de entrada (em inglês)")
    parser.add_argument("saida", help="Arquivo .srt de saída traduzido (em pt-BR)")
    args = parser.parse_args()

    traduzir_srt(args.entrada, args.saida)
