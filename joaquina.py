import os
import argparse
import zipfile
import hashlib
import csv
from faster_whisper import WhisperModel

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Exibe mensagem de crédito
print("joaquina.py Script de fast-whisper para transcrição para diretórios, ZIPs e UFDR por Joaquim Ferreira.")

# Lista de extensões suportadas para áudio
audio_extensions = ['.mp3', '.wav', '.ogg', '.opus', '.aac']
# Lista de extensões suportadas para vídeo
video_extensions = ['.avi', '.mp4', '.mkv', '.mov']

def calcular_hash(file_path):
    hasher = hashlib.sha256()  # Usando SHA-256
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def transcrever_audio(audio_file, model, selected_language):
    try:
        if selected_language == "auto":
            segments, info = model.transcribe(audio_file, beam_size=5)
            print("Idioma detectado '%s' com probabilidade de %f" % (info.language, info.language_probability))
        else:
            segments, info = model.transcribe(audio_file, beam_size=5, language=selected_language)
            print(f"Transcrevendo utilizando o idioma selecionado: {selected_language}")

        texto_transcricao = " ".join(segment.text for segment in segments)
        return texto_transcricao.strip()
    except Exception as e:
        print(f"Erro ao transcrever {audio_file}: {e}")
        return None

def processar_arquivos_opus(arquivos, model, selected_language):
    # Criar ou abrir arquivos de transcrição com base no nome do arquivo de entrada
    nome_base = os.path.splitext(os.path.basename(entrada))[0]  # Obtém o nome do arquivo de entrada sem extensão
    output_txt_path = f"{nome_base}_joaquina.txt"
    output_csv_path = f"{nome_base}_joaquina.csv"

    # Tenta carregar hashes do CSV, se ele existir
    hashes_processados = set()
    if os.path.exists(output_csv_path):
        with open(output_csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Pula o cabeçalho
            for row in csv_reader:
                if len(row) > 2:  # Verifica se há informações suficientes
                    hash_value = row[2]  # Terceira coluna (hash)
                    hashes_processados.add(hash_value)

    with open(output_txt_path, "a", encoding="utf-8") as txt_file, \
         open(output_csv_path, "a", newline='', encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)

        # Adicionar cabeçalho ao CSV se estiver vazio
        if os.stat(output_csv_path).st_size == 0:
            csv_writer.writerow(["arquivo", "caminho", "hash", "texto"])  # Cabeçalho do CSV

        for arquivo_completo in arquivos:
            hash_value = calcular_hash(arquivo_completo)
            if hash_value in hashes_processados:  # Verificar se já foi processado
                print(f"Arquivo {arquivo_completo} já processado. Pulando...")
                continue
            
            print(f"Transcrevendo {arquivo_completo}...")
            transcricao = transcrever_audio(arquivo_completo, model, selected_language)
            if transcricao:
                nome_arquivo = os.path.basename(arquivo_completo)
                
                # Verifique se o caminho está na mesma unidade
                caminho_base = os.path.dirname(entrada)
                if os.path.splitdrive(arquivo_completo)[0] == os.path.splitdrive(caminho_base)[0]:
                    caminho_relativo = os.path.relpath(arquivo_completo, caminho_base)
                else:
                    caminho_relativo = arquivo_completo  # Se em outra unidade, utilize o caminho absoluto
            
                # Grava a transcrição no arquivo TXT
                txt_file.write(f"Nome do Arquivo: {nome_arquivo}\n"
                               f"Caminho: {caminho_relativo}\n"
                               f"HASH: {hash_value}\n"
                               f"{transcricao}\n\n"
                               "--------------------------------------------------------------\n")
                # Grava a transcrição no arquivo CSV
                csv_writer.writerow([nome_arquivo, caminho_relativo, hash_value, transcricao])
                
                # O hash do arquivo já é gravado no CSV, não precisa de outra função
                # adicionar_hash_processado(hash_value) - Removido
                

def localizar_opus(entrada, model, selected_language):
    arquivos_opus = []

    if os.path.isfile(entrada):  # Se for um arquivo
        if entrada.endswith(tuple(audio_extensions)) or entrada.endswith(tuple(video_extensions)):
            arquivos_opus.append(entrada)
        elif entrada.endswith('.zip') or entrada.endswith('.ufdr'):
            # Processar arquivo ZIP ou UFDR
            try:
                with zipfile.ZipFile(entrada, 'r') as zipf:
                    for arquivo in zipf.namelist():
                        if arquivo.endswith(tuple(audio_extensions)) or arquivo.endswith(tuple(video_extensions)):
                            # Extraímos o arquivo diretamente para a memória ou uma pasta temporária
                            with zipf.open(arquivo) as arquivo_media:
                                caminho_temporario = os.path.join("temp", arquivo)
                                os.makedirs(os.path.dirname(caminho_temporario), exist_ok=True)
                                with open(caminho_temporario, 'wb') as f:
                                    f.write(arquivo_media.read())
                                arquivos_opus.append(caminho_temporario)
            except zipfile.BadZipFile:
                print("O arquivo fornecido não é um arquivo zip válido.")
            except Exception as e:
                print(f"Ocorreu um erro ao processar o arquivo {entrada}: {e}")
    elif os.path.isdir(entrada):  # Se for um diretório
        for root, _, files in os.walk(entrada):
            for file in files:
                if file.endswith(tuple(audio_extensions)) or file.endswith(tuple(video_extensions)):
                    arquivos_opus.append(os.path.join(root, file))
    else:
        print("Entrada inválida: forneça um arquivo de áudio ou vídeo, um arquivo ZIP, um arquivo UFDR ou um diretório contendo arquivos de áudio ou vídeo.")

    return arquivos_opus

model_size = "large-v3"
model = WhisperModel(model_size, device="cuda", compute_type="float32")

# Argumentos de linha de comando
parser = argparse.ArgumentParser(description="Transcreva áudio de um arquivo ou diretório e gere arquivos TXT e CSV")
parser.add_argument("entrada", type=str, help="Um arquivo de áudio (MP3, WAV, OGG, OPUS), um arquivo de vídeo (AVI, MP4, MKV), um arquivo ZIP, um arquivo UFDR ou um diretório contendo arquivos de áudio ou vídeo para transcrição")
parser.add_argument("--language", type=str, default="pt", help="Idioma para transcrição (use 'auto' para detecção automática, padrão é 'pt' para português)")

args = parser.parse_args()
entrada = args.entrada
selected_language = args.language

# Localizar arquivos que precisam ser processados
arquivos_opus = localizar_opus(entrada, model, selected_language)

# Processar os arquivos encontrados
processar_arquivos_opus(arquivos_opus, model, selected_language)

# Limpeza dos arquivos temporários ao final (opcional)
import shutil
shutil.rmtree('temp', ignore_errors=True)  # Remove a pasta temporária
