import shutil
from os import remove, listdir, rename, makedirs
from os.path import join, splitext, exists, basename, dirname

def deletarPasta(pasta):
    try: shutil.rmtree(pasta)
    except OSError as e: print(f'Erro ao deletar a pasta "{pasta}": {e}')

def deletarPastas(pastas):
    for pasta in pastas:
        try: shutil.rmtree(pasta)
        except Exception as e: printColorido(f"Erro ao excluir a pasta '{pasta}': {e}", 'r')

def deletarArquivo(caminho):
    try: remove(caminho)
    except OSError as e: print(f'Erro ao deletar o arquivo "{caminho}": {e}')

def removerFormato(arquivo):
    titulo, _ = splitext(arquivo)
    return titulo

def removerFormatoLista(lista): return [removerFormato(elemento) for elemento in lista]

def criarPasta(caminho):
    if not exists(caminho): makedirs(caminho)
    return caminho

def renomearArquivo(caminhoAtual, novoNome):
    novoCaminho = join(dirname(caminhoAtual), novoNome)
    rename(caminhoAtual, novoCaminho)
    return novoCaminho

def obterBasename(caminho): return removerFormato(basename(caminho))

def manterElementosComFinalDesejado(lista, finalDesejado):
    return [elemento for elemento in lista if elemento.endswith(finalDesejado)]