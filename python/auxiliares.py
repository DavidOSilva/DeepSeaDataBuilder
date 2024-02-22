from colorama import Fore, Style
from os import listdir, makedirs, remove, rename
from os.path import join, splitext, exists, basename, dirname
from IPython.display import clear_output
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from global_land_mask import globe # https://github.com/toddkarin/global-land-mask
import cartopy.feature as cfeature
from shapely.geometry import Polygon
from cv2 import fillPoly, flip
import xarray as xr
import numpy as np
from subprocess import run, DEVNULL
from parametros import *
import xmltodict
import shutil
import re
import sys
import time
import h5py

def obterClassesParametros(classesDicionario=parametros['classes'], alvo=parametros['geral']['classeAlvo'], seraoIgnorados=None):
    if seraoIgnorados is None: seraoIgnorados = []
    classes = list(classesDicionario.keys())
    seraoIgnorados.append(alvo)
    for elemento in seraoIgnorados: classes.remove(elemento)
    classes.insert(0, alvo)
    return classes #O alvo sempre aparece primeiro.

def obterProporcoes(qntFatiasIncluidas, casasDecimais=2):
    proporcoes, total = [], qntFatiasIncluidas[0] * 2
    for quantidade in qntFatiasIncluidas: proporcoes.append(round((quantidade / total) * 100, casasDecimais))
    return proporcoes

def gerarNomePastaDestino(proporcoes, tamanho, classes=obterClassesParametros(), foiAumentado=parametros['geral']['realizarAumento'],
                          classesAumentadas=parametros['geral']['classesAumentadas'], foiRedimensionado=parametros['geral']['redimensionar']):
    if 'null' in classes: classes.remove('null')
    prefixo, sufixo, separador = "CONSTRUTOR[", f"][{tamanho}]", '_'
    for c, p in zip(classes, proporcoes):
        if p!= 0: prefixo += f'{c.upper()}={p}' + separador
    if foiAumentado:
        for classe in classesAumentadas: sufixo = sufixo + f'[{classe}++]'
    if foiRedimensionado: sufixo = sufixo + f'[REDIMENSIONADO]'
    return prefixo[:-len(separador)] + sufixo

def inverterNan(matriz, matrizNan): 
    return np.where(~np.isnan(matrizNan), np.nan, matriz) #Troca valores inteiros por Nan e os Nan por inteiros.

def deletarArquivo(caminho):
    try:
        if exists(caminho): remove(caminho)
        else: print(f"O arquivo {caminho} não existe.")
    except Exception as e: print(f"Erro ao deletar o arquivo {caminho}: {e}")

def deletarPastas(pastas):
    for pasta in pastas:
        try: shutil.rmtree(pasta)
        except Exception as e: printColorido(f"Erro ao excluir a pasta '{pasta}': {e}", 'r')

def editarXml(grafo, entrada, saida):
    with open(grafo) as arquivo: dados = xmltodict.parse(arquivo.read())
    dados['graph']['node'][0]['parameters']['file'] = entrada
    dados['graph']['node'][-1]['parameters']['file'] = saida
    with open(grafo, 'w') as arquivo: arquivo.write(xmltodict.unparse(dados, pretty=True))

def executarGrafoSobreNetcdf(netcdf, dirGrafo, dirTemp=parametros['diretorios']['temporarios'], deletar=True):
    dirTemp = criarPasta(dirTemp)
    editarXml(dirGrafo, netcdf, join(dirTemp, "netcdfGrafoExecutado.nc"))
    shell = run([parametros['diretorios']['gpt'], dirGrafo], stdout=DEVNULL, stderr=DEVNULL)
    sigmaGrafoExecutado = obterBandaNetcdf(join(dirTemp, "netcdfGrafoExecutado.nc"), 'Sigma0_VV_db')
    if deletar: deletarArquivo(join(dirTemp, "netcdfGrafoExecutado.nc"))
    return sigmaGrafoExecutado
        
def manterElementosComFinalDesejado(lista, finalDesejado):
    return [elemento for elemento in lista if elemento.endswith(finalDesejado)]

def removerFormato(arquivo):
    titulo, _ = splitext(arquivo)
    return titulo

def removerFormatoLista(lista): return [removerFormato(elemento) for elemento in lista]

# Essa função tem o objetivo de verificar a equivalência de arquivos entre dois diretórios diferentes, sem considerar o formato do arquivo (extensão).
def verificaEquivalenciaEntreDiretorios(dir1, dir2):
    arquivos1 = removerFormatoLista(sorted(listdir(dir1)))
    arquivos2 = removerFormatoLista(sorted(listdir(dir2)))
    if set(arquivos1) == set(arquivos2): return True
    else: return False

# def criarColormapCustomAntigo(hex_colors=['#FF00FF', '#7A6352', '#66CCFF', '#FFFF99', '#E2E2E2', '#05FF58', '#FF643F', '#0066FF', '#CEA24A']):
#     customCmap = ListedColormap(hex_colors, name='custom_cmap')
#     return customCmap

def criarColormapCustom():
    cores_por_valor = [parametros['classes'][classe]['cor'] for classe in sorted(parametros['classes'], key=lambda x: parametros['classes'][x]['valor'])]
    customCmap = ListedColormap(cores_por_valor, name='custom_cmap')
    return customCmap

def obterBandaNetcdf(netcdf, banda='Sigma0_VV_db'):
    dados = xr.open_dataset(netcdf)
    banda = np.asarray(dados[f'{banda}'])
    dados.close()
    return banda

def obterLatLon(netcdf, apenasExtremidades=False):
    dados_nc = xr.open_dataset(netcdf)
    lat, lon = dados_nc['latitude'].values, dados_nc['longitude'].values # Obtendo as coordenadas reais de lat e lon.
    dados_nc.close()
    if apenasExtremidades:
        lat, lon = [lat[0][0], lat[0][-1], lat[-1][0], lat[-1][-1]], [lon[0][0], lon[0][-1], lon[-1][0], lon[-1][-1]] #Retorna apenas os pontos das extremidades.
        lat, lon = np.asarray(lat), np.asarray(lon) 
    return lat, lon

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

#Função responsável por criar uma nova pasta em um diretorio definido.
def criarPasta(caminho):
    if not exists(caminho): makedirs(caminho)
    return caminho

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
        
def fatiarComDiferentesPtsIniciais(dado, rotulo, tamanho, ptsIniciais=[0]): #Fatia multiplas vezes cada arquivo, considerando diferentes entradas.
    todosDadosFatiados, todosRotulosFatiados = [], []
    largadasLinha, largadasColuna = criarListaPontosIniciais(ptsIniciais) #Todo pt de partida tomado na linha pode também ser tomado na coluna.
    for linha, coluna in list(zip(largadasLinha, largadasColuna)): 
        dadoFatiado, rotuloFatiado = fatiar(dado, rotulo, tamanho=tamanho, linhaInicial=linha, colunaInicial=coluna)
        todosDadosFatiados.extend(dadoFatiado)
        todosRotulosFatiados.extend(rotuloFatiado)
    return todosDadosFatiados, todosRotulosFatiados

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

def carregarNpzDadoERotulo(npz, dadoIndice='arr_0', rotuloIndice='arr_1'):
    with np.load(npz) as npzFile:
        dado = npzFile[dadoIndice]
        rotulo = npzFile[rotuloIndice]
    return dado, rotulo

def lenHDF5(hdf5File, dataset='dado', grupo='principal'):
    with h5py.File(hdf5File, 'r') as f:
        gp = f[grupo]
        data = gp[dataset]
        qnt = len(data)
    return qnt

def obterNivelCompressao(compressao=parametros['geral']['compressao']):
    saida = None
    if compressao=='gzip' : saida = 9
    return saida
    
def criarHDF5Vazio(hdf5File, tamanho, grupos=['principal'], datasets=['dado', 'rotulo'], compressao=parametros['geral']['compressao']):
    nvlComp = obterNivelCompressao() #É usado apenas para compressão do tipo gzip. Para mais detalhes: https://docs.h5py.org/en/stable/high/dataset.html
    with h5py.File(hdf5File, 'w') as f:
        for gp in grupos:
            grupo = f.create_group(gp)  # Cria um grupo com o nome especificado
            for ds in datasets:
                if isinstance(tamanho, int): tamanho = [tamanho]
                if nvlComp is None:
                    grupo.create_dataset(ds,shape=(0, tamanho[0], tamanho[-1]), maxshape=(None, tamanho[0], tamanho[-1]),
                                         compression=compressao)
                else:
                    grupo.create_dataset(ds,shape=(0, tamanho[0], tamanho[-1]), maxshape=(None, tamanho[0], tamanho[-1]),
                                         compression=compressao, compression_opts=nvlComp)
    return hdf5File

def carregarHDF5(hdf5File, indices=None, grupo='principal', datasets=['dado', 'rotulo']):
    saida = []
    with h5py.File(hdf5File, 'r') as f:
        gp = f[grupo]  # Acessa o grupo com o nome especificado
        for ds in datasets:
            if indices is None: info = gp[ds][:]  # Se os índices forem None, carrega todo o dataset
            else:
                data = gp[ds]
                tamanho = len(data)
                if isinstance(indices, int): indices = [indices] # Se o índice for um único número inteiro, converte para uma lista
                start = indices[0]
                end = min(tamanho, indices[-1])
                info = data[int(start):int(end)] # Carrega o dataset do índice inicial ao índice final
            saida.append(info)
    return saida
 
def incrementarHDF5(hdf5File, dadosNovos, grupo='principal', datasets=['dado', 'rotulo']): #Sendo dadosNovos uma lista de listas = [[],[], ...]
    with h5py.File(hdf5File, 'a') as f:
        gp = f[grupo]  # Acessa o grupo com o nome especificado
        for dadoNovo, ds in zip(dadosNovos, datasets):
            dados = gp[ds]
            dadosAntigosShape = dados.shape # Obtem o tamanho atual dos datasets
            dados.resize((dadosAntigosShape[0] + len(dadoNovo), *dadosAntigosShape[1:])) # Extende os datasets
            dados[dadosAntigosShape[0]:] = dadoNovo # Adiciona os novos dados

def aproximarLote(x, coef = [44355277.53563044, -2.0001758205102522]): return int(round(coef[0] * (x ** coef[1]), 0))

def obterQuantidadeDeLotes(comprimento, tamanhoLote):
    qntdLotes = comprimento // tamanhoLote
    if comprimento % tamanhoLote != 0: qntdLotes += 1
    return qntdLotes

def obterBasename(caminho): return removerFormato(basename(caminho)) #Extrai o nome de qualquer arquivo sem sua extensão.

def renomearArquivo(caminhoAtual, novoNome):
    novoCaminho = join(dirname(caminhoAtual), novoNome)
    rename(caminhoAtual, novoCaminho)
    return novoCaminho

def obterQntFatiasFiltradasHDF5(hdf5Filtrados, seraoIgnorados=None):
    if seraoIgnorados is None: seraoIgnorados = []
    classes, qntFatias = obterClassesParametros(), []
    for classe in classes:
        if classe not in seraoIgnorados: qntFatias.append(lenHDF5(hdf5Filtrados, grupo=classe))
        else: qntFatias.append(0) #É zerado para que na etapa de construção do conjunto de dados a classe não ser incluída.
    return qntFatias

# Função para converter geometrias em polígonos
def geometriasParaPoligonos(geometrias):
    poligonos = []
    for geometria in geometrias:
        if isinstance(geometria, Polygon): geometries = [geometria]  # Check if the geometry is a Polygon or a MultiPolygon
        else: geometries = list(geometria.geoms)
        for geom in geometries: poligonos.append(np.array(geom.exterior.coords))
    return poligonos

def lat_to_index(lat, _lat):
    lat = np.array(lat)
    if np.any(lat>90): raise ValueError('latitude must be <= 90')
    if np.any(lat<-90): raise ValueError('latitude must be >= -90')
    lat[lat > _lat.max()], lat[lat < _lat.min()] = _lat.max(), _lat.min()
    return ((lat - _lat[0])/(_lat[1]-_lat[0])).astype('int')
    
def lon_to_index(lon, _lon):
    lon = np.array(lon)
    if np.any(lon > 180): raise ValueError('longitude must be <= 180')
    if np.any(lon < -180): raise ValueError('longitude must be >= -180')
    lon[lon > _lon.max()],  lon[lon < _lon.min()] = _lon.max(), _lon.min()
    return ((lon - _lon[0]) / (_lon[1] - _lon[0])).astype('int')

def is_land(lat, lon, _mask, _lat, _lon):
    lat_i, lon_i = lat_to_index(lat, _lat), lon_to_index(lon, _lon)
    return np.logical_not(_mask[lat_i,lon_i])

def obterMascaraTerrenoNaturalEarth(escala='10m', resolucao=2e-3):
    land_10m = cfeature.NaturalEarthFeature('physical', 'land', escala) # Carregar os polígonos dos continentes
    poligonosTerreno = list(land_10m.geometries())
    extent = [-180, 180, -90, 90]
    nx, ny = round((extent[1] - extent[0]) // resolucao), round((extent[3] - extent[2]) // resolucao) # Criar grade de coordenadas
    lons = np.linspace(extent[0], extent[1], nx)  # Cria array de longitudes
    lats = np.linspace(extent[2], extent[3], ny)  # Cria array de latitudes
    lats = lats[::-1]  # Inverte as latitudes
    poligonosTerreno = geometriasParaPoligonos(poligonosTerreno) # Converter geometrias em polígonos
    continentes = np.zeros((ny, nx), dtype=np.uint8) # Criar array 2D numpy para armazenar os continentes
    for poligonoTerreno in poligonosTerreno: # Preencher continentes individualmente
        poligono = poligonoTerreno.reshape((-1, 2)) # Transformar polígono em formato aceitável pelo fillPoly
        poligono = np.array([[(x - extent[0]) / resolucao, (y - extent[2]) / resolucao] for x, y in poligono], dtype=np.int32)
        continentes = fillPoly(continentes, [poligono], color=1) # Preencher continentes com o polígono atual
    # lats, lons = np.repeat(lats[:, np.newaxis], nx, axis=1), np.repeat(lons[np.newaxis, :], ny, axis=0)
    return flip(continentes, 0), lats, lons

def retirarSoloGLMNaturalEarth(netcdf):
    sar = obterBandaNetcdf(netcdf, banda='Sigma0_VV_db')
    lat, lon = obterLatLon(netcdf)
    mask, lats, lons = obterMascaraTerrenoNaturalEarth(escala='10m')
    latFlatten, lonFlatten = lat.flatten(), lon.flatten()
    landMaskNE = is_land(latFlatten, lonFlatten, _mask=mask, _lat=lats, _lon=lons)
    landMaskNE = landMaskNE.reshape(lat.shape)
    sar[landMaskNE == False] = np.nan
    return sar

def retirarSoloGlobalLandMaskGLOBE(netcdf):
    sar = obterBandaNetcdf(netcdf, banda='Sigma0_VV_db')
    lat, lon = obterLatLon(netcdf)
    latFlatten, lonFlatten = lat.flatten(), lon.flatten()
    landMask = globe.is_land(latFlatten, lonFlatten)
    landMask = landMask.reshape(lat.shape)
    sar[landMask == True] = np.nan
    return sar

def retirarSolo(netcdf, modo):
    if modo == 'glm': sigmaSemSolo = retirarSoloGlobalLandMaskGLOBE(netcdf)
    elif modo == 'glmWithNE': sigmaSemSolo = retirarSoloGLMNaturalEarth(netcdf)
    elif modo == 'snap': sigmaSemSolo = executarGrafoSobreNetcdf(netcdf, join(parametros['diretorios']['grafos'], "LandToNan.xml"))
    else:
        printColorido('MODO DE RETIRADA DE SOLO INVÁLIDO', 'r')
        return None
    return  sigmaSemSolo

def redimensionar(dado, fator=2):
    novas_linhas, novas_colunas = dado.shape[0] // fator, dado.shape[1] // fator
    dado_reduzido = np.zeros((novas_linhas, novas_colunas))
    dado_reduzido = dado[:novas_linhas * fator, :novas_colunas * fator].reshape((novas_linhas, fator, novas_colunas, fator)).mean(axis=(1, 3))
    return dado_reduzido

def redimensionarLote(arrays, fator=2): return [redimensionar(array, fator=fator) for array in arrays]
        