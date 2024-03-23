from colorama import Fore, Style
from IPython.display import clear_output
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import time

from parametros import *
from python.hdf5Manager import *
from python.filesManager import *
from python.groundRemover import *

def obterClassesParametros(classesDicionario=parametros['classes'], alvo=parametros['geral']['classeAlvo'], seraoIgnorados=None):
    if seraoIgnorados is None: seraoIgnorados = []
    classes = list(classesDicionario.keys())
    seraoIgnorados.append(alvo)
    for elemento in seraoIgnorados: classes.remove(elemento)
    classes.insert(0, alvo)
    return classes #O alvo sempre aparece primeiro.

def obterProporcoesReais(qntFatiasIncluidas, casasDecimais=2):
    proporcoes, total = [], sum(qntFatiasIncluidas)
    for quantidade in qntFatiasIncluidas: proporcoes.append(round((quantidade / total) * 100, casasDecimais))
    return proporcoes

def gerarNomePastaDestino(proporcoes, tamanho,  classesAumentadas, classes=obterClassesParametros()):
    if 'null' in classes: classes.remove('null')
    prefixo, sufixo, separador = "CONSTRUTOR[", f"][{tamanho}]", '_'
    for c, p in zip(classes, proporcoes):
        if p!= 0: prefixo += f'{c.upper()}={p}' + separador
    for classe in classesAumentadas: sufixo = sufixo + f'[{classe}++]'
    return prefixo[:-len(separador)] + sufixo

def inverterNan(matriz, matrizNan): 
    return np.where(~np.isnan(matrizNan), np.nan, matriz) #Troca valores inteiros por Nan e os Nan por inteiros.

# Essa função tem o objetivo de verificar a equivalência de arquivos entre dois diretórios diferentes, sem considerar o formato do arquivo (extensão).
def verificaEquivalenciaEntreDiretorios(dir1, dir2):
    arquivos1 = removerFormatoLista(sorted(listdir(dir1)))
    arquivos2 = removerFormatoLista(sorted(listdir(dir2)))
    if set(arquivos1) == set(arquivos2): return True
    else: return False

def criarColormapCustom():
    cores_por_valor = [parametros['classes'][classe]['cor'] for classe in sorted(parametros['classes'], key=lambda x: parametros['classes'][x]['valor'])]
    customCmap = ListedColormap(cores_por_valor, name='custom_cmap')
    return customCmap

def plotLadoALado(figuras, titulos=['DADO', 'ROTULO']):
    valores = [classe['valor'] for classe in parametros['classes'].values()]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    im1 = axes[0].imshow(figuras[0], cmap='gray')
    axes[0].set_title(titulos[0])
    im2 = axes[1].imshow(figuras[1], cmap=criarColormapCustom(), vmin=min(valores), vmax=max(valores))
    axes[1].set_title(titulos[1])
    plt.show()
    
#Funções responsáveis por alterar a cor do print, trata-se apenas de um recurso estético.
def printColorido(mensagem, cor='g', end='\n', clear=False):
    cores_suportadas = {'g': Fore.GREEN, 'r': Fore.RED, 'y': Fore.YELLOW, 'b': Fore.BLUE, 'm': Fore.MAGENTA, 'c': Fore.CYAN}
    print(cores_suportadas.get(cor.lower(), Fore.RESET) + mensagem + Style.RESET_ALL, end=end)
    if clear: clear_output(wait=True)

def criarListaPontosIniciais(ptsIniciais): #Cria, usandos os ptsInicias, listas que indicam onde o fatiamento deve iniciar. 
    linha, coluna = [], []
    for ponto in ptsIniciais:
        if ponto==0:
            linha.append(0)
            coluna.append(0)
        else:
            linha.append(ponto) #O processo é feito nas linhas e colunas. Por isso fatiaremos duas vezes, saltando n linhas e depois n colunas.
            linha.append(0)
            coluna.append(0)  
            coluna.append(ponto)
    return linha, coluna

#Função responsável por exibir barra de progresso durante a execução dos blocos.
def imprimaBarraProgresso(iteration, total, etapa, limpar=False, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    clear_output(wait=True)
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    if iteration < total:
        printColorido(f'EFETUANDO {etapa.upper()}...', 'b')
        print(f'\r{prefix} ' + Fore.BLUE + f'|{bar}|' + Style.RESET_ALL + f'{percent}% {suffix}', end = printEnd) 
    if iteration == total:
        printColorido(f'ETAPA FINALIZADA COM SUCESSO! ')
        print(f'\r{prefix} ' + Fore.GREEN + f'|{bar}|{percent}% {suffix}' + Style.RESET_ALL, end = printEnd)
        print('')
        clear_output(wait=True)

def ocorrenciasAtendeLimiar(matriz, buscado, limiar=parametros['geral']['limiar']):
    if buscado == None: return None
    ocorrenciaPercentual = np.count_nonzero(matriz.flatten() == buscado)/(matriz.flatten().shape[0]) #Percentual de ocorrencias de buscado em toda matriz.
    return ocorrenciaPercentual > limiar

def aproximarLote(x, coef = [44355277.53563044, -2.0001758205102522]): return int(round(coef[0] * (x ** coef[1]), 0))

def obterQuantidadeDeLotes(comprimento, tamanhoLote):
    qntdLotes = comprimento // tamanhoLote
    if comprimento % tamanhoLote != 0: qntdLotes += 1
    return qntdLotes

def obterQntFatiasFiltradasHDF5(hdf5Filtrados, seraoIgnorados=None):
    if seraoIgnorados is None: seraoIgnorados = []
    classes, qntFatias = obterClassesParametros(), []
    for classe in classes:
        if classe not in seraoIgnorados: qntFatias.append(lenHDF5(hdf5Filtrados, grupo=classe))
        else: qntFatias.append(0) #É zerado para que na etapa de construção do conjunto de dados a classe não ser incluída.
    return qntFatias

def retirarSolo(netcdf, modo):
    if modo == 'glm': sigmaSemSolo = retirarSoloGlobalLandMaskGLOBE(netcdf)
    elif modo == 'glmWithNE': sigmaSemSolo = retirarSoloGLMNaturalEarth(netcdf)
    elif modo == 'snap': sigmaSemSolo = executarGrafoSobreNetcdf(netcdf, join(parametros['diretorios']['grafos'], "LandToNan.xml"))
    else:
        printColorido('MODO DE RETIRADA DE SOLO INVÁLIDO', 'r')
        return None
    return  sigmaSemSolo

def extrairProporcoes(dicionario=parametros['classes'], alvo=parametros['geral']['classeAlvo'], seraoIgnorados=None): 
    if seraoIgnorados is None: seraoIgnorados = []
    seraoIgnorados.append(alvo)
    proporcoes = []
    for classe in dicionario.items():
        if classe[0] not in seraoIgnorados: proporcoes.append(classe[1]['proporcao'])
    proporcoes.insert(0, dicionario[alvo]['proporcao']) #O alvo sempre aparece primeiro.
    return proporcoes
        