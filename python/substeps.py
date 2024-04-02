from python.utils import *
from parametros import *
from python.netcdfManager import *
from os.path import join, isdir, exists
from cv2 import fillPoly
import re
import json

def converterNetcdfParaArray(netcdf, zerarNan=True, semSolo=parametros['geral']['retirarSolo'], modo=parametros['geral']['modoRetirarSolo']):
    sigma = obterBandaNetcdf(netcdf, 'Sigma0_VV_db')
    borda = sigma != sigma
    sigmaSemSolo = retirarSolo(netcdf, modo=modo)
    sigmaSemMar = inverterNan(sigma, sigmaSemSolo)
    if semSolo: sigma = sigmaSemSolo
    if zerarNan: sigma = np.nan_to_num(sigma, nan=0)
    return sigma, sigmaSemSolo , sigmaSemMar, borda

def converterJsonParaArray(jsonFile, sigmaSemSolo, sigmaSemMar, borda, aprimorarRotulos=parametros['geral']['aprimorarRotulo']):
    dadosJSON = json.load(open(jsonFile)) #Lendo cada arquivo JSON e convertendo em um dicionário.
    rotulo = np.full(sigmaSemSolo.shape, parametros['classes']['null']['valor'], dtype=np.int32) + borda.astype(np.int32) * parametros['classes']['edge']['valor']
    if aprimorarRotulos:
        apenasAgua = (sigmaSemSolo == sigmaSemSolo) * parametros['classes']['ocean']['valor']
        apenasSolo = (sigmaSemMar == sigmaSemMar) * parametros['classes']['land']['valor']
        rotulo = rotulo + apenasAgua.astype(np.int32) + apenasSolo.astype(np.int32)
    for poligono in dadosJSON['shapes']: #Analisando cada poligono de cada vez para extrair seu tipo.
        categoria = re.sub(r"[^a-zA-Z0-9]","",poligono['label'].lower()) #Extraindo rótulo e tratando string para minusculo sem especiais.
        if   categoria in parametros['classes']['oil']['indicadores']:         valor = parametros['classes']['oil']['valor']
        elif categoria in parametros['classes']['ocean']['indicadores']:       valor = parametros['classes']['ocean']['valor']
        elif categoria in parametros['classes']['land']['indicadores']:        valor = parametros['classes']['land']['valor'] 
        elif categoria in parametros['classes']['ship']['indicadores']:        valor = parametros['classes']['ship']['valor'] 
        elif categoria in parametros['classes']['biofilm']['indicadores']:     valor = parametros['classes']['biofilm']['valor']
        elif categoria in parametros['classes']['wind']['indicadores']:        valor = parametros['classes']['wind']['valor']    
        elif categoria in parametros['classes']['rain']['indicadores']:        valor = parametros['classes']['rain']['valor']
        elif categoria in parametros['classes']['lookalike']['indicadores']:   valor = parametros['classes']['lookalike']['valor']
        else:
            valor = parametros['classes']['null']['valor']
            printColorido(f'RÓTULO INVÁLIDO ENCONTRADO: {rotulo}', 'y')
        rotulo = fillPoly(rotulo, [np.array(poligono['points'], dtype=np.int32)], valor) #Criando cada um dos poligonos no array
    return rotulo

#Função responsável por recortar uma única imagem em pacotes menores de acordo com o tamanho definido.
def fatiar(dado, rotulo, tamanho, manterVazios=parametros['geral']['manterVazios'], linhaInicial=0, colunaInicial=0):
    dado, rotulo = dado[linhaInicial:, colunaInicial:], rotulo[linhaInicial:, colunaInicial:]
    limiteLinha, limiteColuna = (rotulo.shape[0]) // tamanho, (rotulo.shape[1]) // tamanho
    dado, rotulo = dado[:limiteLinha * tamanho, :limiteColuna * tamanho], rotulo[:limiteLinha * tamanho, :limiteColuna * tamanho]
    fatiaVazia, fatiaZerada = np.full([tamanho,tamanho], parametros['classes']['null']), np.full([tamanho,tamanho], 0)
    dadoFatiado, rotuloFatiado = [], []
    for i in range(0, dado.shape[0], tamanho):
        for j in range(0, dado.shape[1], tamanho):
            fatiaRotulo, fatiaDado = rotulo[i:i+tamanho, j:j+tamanho], dado[i:i+tamanho, j:j+tamanho]
            equivalencia = np.array_equal(fatiaRotulo, fatiaVazia) or np.array_equal(fatiaDado, fatiaZerada) 
            if not equivalencia or manterVazios:
                rotuloFatiado.append(fatiaRotulo)
                dadoFatiado.append(np.nan_to_num(fatiaDado, nan=0))
    if len(dadoFatiado) != len(rotuloFatiado): printColorido("O número de fatias dos dados e rótulos devem ser iguais!", 'r')
    return dadoFatiado, rotuloFatiado

def fatiarComDiferentesPtsIniciais(dado, rotulo, tamanho, ptsIniciais=[0]): #Fatia multiplas vezes cada arquivo, considerando diferentes entradas.
    todosDadosFatiados, todosRotulosFatiados = [], []
    largadasLinha, largadasColuna = criarListaPontosIniciais(ptsIniciais) #Todo pt de partida tomado na linha pode também ser tomado na coluna.
    for linha, coluna in list(zip(largadasLinha, largadasColuna)): 
        dadoFatiado, rotuloFatiado = fatiar(dado, rotulo, tamanho=tamanho, linhaInicial=linha, colunaInicial=coluna)
        todosDadosFatiados.extend(dadoFatiado)
        todosRotulosFatiados.extend(rotuloFatiado)
    return todosDadosFatiados, todosRotulosFatiados

def retirarExcessos(img, lbl, plot=parametros['visualizar']['plotarSemExcessos'], valoresVazios=['null', 'ocean']):
    nLinhas, nColunas = img.shape
    def estaVazio(array, valoresVazios=valoresVazios): return set(np.unique(array)).issubset({parametros['classes'][v]['valor'] for v in valoresVazios})
    linhaInicio, colunaInicio, linhaFim, colunaFim = 0, 0, (nLinhas - 1), (nColunas - 1)
    for li in range(nLinhas):
        if estaVazio(lbl[li:li + 1, 0:nColunas]): linhaInicio = li + 1
        else: break
    for ci in range(nColunas):
        if estaVazio(lbl[0:nLinhas, ci:ci + 1]): colunaInicio = ci + 1
        else: break
    for lf in range(nLinhas, 0, -1):
        if estaVazio(lbl[lf - 1:lf, 0:nColunas]): linhaFim = lf - 1
        else: break
    for cf in range(nColunas, 0, -1):
        if estaVazio(lbl[0:nLinhas, cf - 1:cf]): colunaFim = cf - 1
        else: break
    intervalo = (linhaInicio, linhaFim, colunaInicio, colunaFim)  # linhaFim e colunaFim não estão contidos no intervalo.
    imgSemExcessos, lblSemExcessos = img[intervalo[0]:intervalo[1], intervalo[2]:intervalo[3]], lbl[intervalo[0]:intervalo[1], intervalo[2]:intervalo[3]]
    if plot: plotLadoALado([imgSemExcessos, lblSemExcessos], titulos=['DADO', 'ROTULO'])
    return imgSemExcessos, lblSemExcessos

#Função responsável por filtrar uma lista de fatias. Dessa forma, serve para separar da lista original fatias com um valor sugerido.
def filtrar(dado, rotulo, classe, limiar=parametros['geral']['limiar'], detalhar=False):
    dadoFiltrado, dadoRestante, rotuloFiltrado, rotuloRestante = [], [], [], []
    for d, r in zip(dado, rotulo):
        if ocorrenciasAtendeLimiar(r, parametros['classes'][f'{classe}']['valor'], limiar):
            dadoFiltrado.append(d)
            rotuloFiltrado.append(r)
        else:
            dadoRestante.append(d)
            rotuloRestante.append(r)
    if detalhar: printColorido(f'{classe.upper()}: {len(dadoFiltrado)}   ', 'b', '')
    return (dadoFiltrado, rotuloFiltrado), (dadoRestante, rotuloRestante) #filtrados, restantes = ([array, ...],[array, ...]), ([array, ...],[array, ...])

#Função responsável por identificar quais classes precisam ser aumentadas para tentar satisfazer a proporção estabelecida para ela.
def encontrarClassesAumentadas(hdf5Filtrados, alvo=parametros['geral']['classeAlvo']):
    classes, qntdFatias, proporcoes = obterClassesParametros(), obterQntFatiasFiltradasHDF5(hdf5Filtrados), extrairProporcoes()
    if parametros['geral']['realizarAumento']: classesAumentadas = [classes[0]]
    else: classesAumentadas = []
    for idx, classe in enumerate(classes[1:]): #O alvo não é analisado.
        qntdMin = int(round((proporcoes[idx] * qntdFatias[0])/proporcoes[0]))
        if qntdFatias[idx] < qntdMin: classesAumentadas.append(classe)
    return classesAumentadas

def aumentoDeDados(dados, rotulos, probabilidade=1, incluirBase=False):
    dadosAumento, rotulosAumento = [], []
    conjuntoTreinamento, conjuntoAumentado = [dados, rotulos], [dadosAumento, rotulosAumento]
    for i in range(len(dados)):
        dadoBase, rotuloBase = conjuntoTreinamento[0][i], conjuntoTreinamento[1][i]
        if incluirBase: conjuntoAumentado[tipo].append(base) # Adicionando o array original na lista.
        if np.random.rand() < probabilidade:
            conjuntoAumentado[0].append(np.rot90(dadoBase, k=1))
            conjuntoAumentado[1].append(np.rot90(rotuloBase, k=1))
        if np.random.rand() < probabilidade:
            conjuntoAumentado[0].append(np.rot90(dadoBase, k=2))
            conjuntoAumentado[1].append(np.rot90(rotuloBase, k=2))
        if np.random.rand() < probabilidade:
            conjuntoAumentado[0].append(np.rot90(dadoBase, k=3))
            conjuntoAumentado[1].append(np.rot90(rotuloBase, k=3))
        if np.random.rand() < probabilidade:
            conjuntoAumentado[0].append(np.flip(dadoBase, 1))
            conjuntoAumentado[1].append(np.flip(rotuloBase, 1))
        if np.random.rand() < probabilidade:
            conjuntoAumentado[0].append(np.flip(dadoBase, 0))
            conjuntoAumentado[1].append(np.flip(rotuloBase, 0))
        if np.random.rand() < probabilidade:
            dadoBaseRotacionado90Graus, rotuloBaseRotacionado90Graus = np.rot90(dadoBase, k=1), np.rot90(rotuloBase, k=1)
            conjuntoAumentado[0].append(np.flip(dadoBaseRotacionado90Graus, 1))
            conjuntoAumentado[1].append(np.flip(rotuloBaseRotacionado90Graus, 1))
        if np.random.rand() < probabilidade:
            dadoBaseRotacionado90Graus, rotuloBaseRotacionado90Graus = np.rot90(dadoBase, k=1), np.rot90(rotuloBase, k=1)
            conjuntoAumentado[0].append(np.flip(dadoBaseRotacionado90Graus, 0))
            conjuntoAumentado[1].append(np.flip(rotuloBaseRotacionado90Graus, 0))
    return dadosAumento, rotulosAumento