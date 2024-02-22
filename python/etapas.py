from python.auxiliares import *
from parametros import *
from cv2 import fillPoly #Versão utilizada: 4.6.0.66
from os import listdir, getcwd
from os.path import join, isdir, exists
import matplotlib.pyplot as plt
import json

def converterNetcdfParaArray(netcdf, zerarNan=True, semSolo=parametros['geral']['retirarSolo'], modo=parametros['geral']['modoRetirarSolo']):
        sigma = obterBandaNetcdf(netcdf, 'Sigma0_VV_db')
        sigmaSemSolo = retirarSolo(netcdf, modo=modo)
        sigmaSemMar = inverterNan(sigma, sigmaSemSolo)
        if semSolo: sigma = sigmaSemSolo
        if zerarNan: sigma = np.nan_to_num(sigma, nan=0)
        return sigma, sigmaSemSolo , sigmaSemMar

def converterJsonParaArray(jsonFile, sigmaSemSolo, sigmaSemMar, aprimorarRotulos=parametros['geral']['aprimorarRotulo']):
    dadosJSON = json.load(open(jsonFile)) #Lendo cada arquivo JSON e convertendo em um dicionário.
    rotulo = np.full(sigmaSemSolo.shape, parametros['classes']['null']['valor'], dtype=np.int32)
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

def recortarEmFatias(tamanho, dirNetcdf=parametros['diretorios']['netcdfs'], dirJson=parametros['diretorios']['jsons'],
                     dirHDF5=parametros['diretorios']['temporarios'], valoresVazios=['null', 'ocean'],
                     detalhes=parametros['visualizar']['exibirQuantidadeFatias']):
    if not verificaEquivalenciaEntreDiretorios(dirNetcdf, dirJson):
        printColorido('TODOS OS NETCDFS DEVEM POSSUIR UM JSON ASSOCIADO E VICE-VERSA!', 'r')
        return None
    if not parametros['geral']['aprimorarRotulo']: valoresVazios=['null'] #Assim os poligonos de oceano feitos a mão são mantidos.
    dirFatiados = criarPasta(join(dirHDF5, 'FATIADOS'))
    hdf5File = criarHDF5Vazio(join(dirFatiados, f'[{tamanho}].h5'), tamanho=tamanho)
    if parametros['geral']['modoRetirarSolo'] == 'snap':
        printColorido('VAMOS UTILIZAR O SNAP PARA PROCESSAR CADA NETCDF, ISSO PODE LEVAR UM TEMPINHO...                                      ','b', '\r')
    for indice, arquivoSemFormato in enumerate(sorted(removerFormatoLista(manterElementosComFinalDesejado(listdir(dirNetcdf), '.nc')))):
        sigma, sigmaSemSolo, sigmaSemMar = converterNetcdfParaArray(join(dirNetcdf, arquivoSemFormato + '.nc'))
        rotulo = converterJsonParaArray(join(dirJson, arquivoSemFormato + '.json'), sigmaSemSolo, sigmaSemMar)
        if parametros['geral']['retirarExcessos']: sigma, rotulo = retirarExcessos(sigma, rotulo, valoresVazios=valoresVazios)
        dadosFatiados, rotulosFatiados = fatiarComDiferentesPtsIniciais(sigma, rotulo, tamanho=tamanho, ptsIniciais=[0]) #[0, tamanho//2]
        incrementarHDF5(hdf5File, dadosNovos=[dadosFatiados, rotulosFatiados]) # Adiciona os dados fatiados ao arquivo HDF5
        if not parametros['visualizar']['plotarSemExcessos']: imprimaBarraProgresso(indice+1, len(listdir(dirNetcdf)), etapa='RECORTE EM FATIAS')
    if detalhes: printColorido(f"QUANTIDADE TOTAL DE FATIAS OBTIDAS: {lenHDF5(hdf5File, dataset='dado')}                                        ",'g','\r') 
    return hdf5File

def separarFatiasPorClasses(hdf5Fatiados, tamanho, dirHDF5=parametros['diretorios']['temporarios'],
                            alvo=parametros['geral']['classeAlvo'], classes=obterClassesParametros()):
    tamanhoLote, comprimento = aproximarLote(tamanho), lenHDF5(hdf5Fatiados, dataset='dado')
    qntdLotes, fim = obterQuantidadeDeLotes(comprimento, tamanhoLote), tamanhoLote
    dirFiltrados = criarPasta(join(dirHDF5, 'FILTRADOS'))
    hdf5Filtrados = criarHDF5Vazio(join(dirFiltrados, f'[{tamanho}].h5'), tamanho=tamanho, grupos=classes)
    for i in range(qntdLotes):
        inicioLote = i*tamanhoLote
        fimLote = inicioLote + tamanhoLote
        dadosLote, rotulosLote = carregarHDF5(hdf5Fatiados, indices=[inicioLote, fimLote]) #Carrega lote de fatias.
        restante = (dadosLote, rotulosLote)
        for classe in classes:
            if classe == alvo: filtrados, restante = filtrar(restante[0], restante[1], classe) #Usa limiar pde parametros.
            else: filtrados, restante = filtrar(restante[0], restante[1], classe, limiar=0)
            if len(filtrados[0])>0: incrementarHDF5(hdf5Filtrados, dadosNovos=[filtrados[0], filtrados[1]], grupo=classe)
        if not parametros['visualizar']['detalharFiltragem']: imprimaBarraProgresso(i+1, qntdLotes, etapa='FILTRAGEM ENTRE AS CLASSES')
        else: 
            mensagem = '' #Exibe a quantidade de fatias para cada classe toda vez que um dos lotes é filtrado.
            for classe in classes: mensagem += f'{classe.upper()}: {lenHDF5(hdf5Filtrados, grupo=classe)}   '
            mensagem += f'LOTE: {i+1}/{qntdLotes}'
            printColorido(mensagem,'b', '\r')      
    return hdf5Filtrados

def aumentoDeDadosHDF5(hdf5Filtrados, tamanho, classesAumentadas=parametros['geral']['classesAumentadas'], probabilidade=parametros['geral']['probabilidade']):
    tamanhoLote = aproximarLote(tamanho)
    fim, sufixo = tamanhoLote, ''
    for i, classeAumentada in enumerate(classesAumentadas):
        qntdLotes = obterQuantidadeDeLotes(comprimento=lenHDF5(hdf5Filtrados, grupo=classeAumentada), tamanhoLote=tamanhoLote)
        for i in range(qntdLotes):
            inicioLote = i*tamanhoLote
            fimLote = inicioLote + tamanhoLote
            dados, rotulos = carregarHDF5(hdf5Filtrados, indices=[inicioLote, fimLote], grupo=classeAumentada)
            dadosAumentados, rotulosAumentados = aumentoDeDados(dados, rotulos, probabilidade=probabilidade, incluirBase=False)
            incrementarHDF5(hdf5Filtrados, dadosNovos=[dadosAumentados, rotulosAumentados], grupo=classeAumentada)
        sufixo += f'[{classeAumentada}++]'
        imprimaBarraProgresso(i, len(classesAumentadas), etapa='AUMENTO DO CONJUNTO DE DADOS')
    hdf5Filtrados = renomearArquivo(hdf5Filtrados, novoNome=obterBasename(hdf5Filtrados) + sufixo + '.h5')
    return hdf5Filtrados

def criarConjuntoDeDados(hdf5Filtrados, tamanho, dirDataset=parametros['diretorios']['dataset']):
    classes, qntFatias = obterClassesParametros(), obterQntFatiasFiltradasHDF5(hdf5Filtrados, seraoIgnorados=['land', 'null'])
    datasetPasta = criarPasta(join(dirDataset, f'{tamanho}'))
    tamanhoLote = aproximarLote(tamanho)
    if parametros['geral']['redimensionar']: datasetHDF5 = criarHDF5Vazio(join(datasetPasta, f'[EM ANDAMENTO...][{tamanho}].h5'), parametros['geral']['limiteResolucao']) 
    else: datasetHDF5 = criarHDF5Vazio(join(datasetPasta, f'[EM ANDAMENTO...][{tamanho}].h5'), tamanho)
    totalAdicionado, qntFatiasIncluidas = 0, []
    for classeIndex, classe in enumerate(classes):
        qntdLotes, foramIncluidas = obterQuantidadeDeLotes(comprimento=qntFatias[classeIndex], tamanhoLote=tamanhoLote), 0
        for loteIndex in range(qntdLotes):
            faltaAdicionar = qntFatias[0]*2 - totalAdicionado
            inicioLote = loteIndex*tamanhoLote
            fimLote =  min(inicioLote + tamanhoLote, inicioLote + faltaAdicionar)
            dado, rotulo = carregarHDF5(hdf5Filtrados, indices=[inicioLote, fimLote], grupo=classe)
            if parametros['geral']['redimensionar'] and tamanho > parametros['geral']['limiteResolucao']:
                fator = tamanho//parametros['geral']['limiteResolucao']
                dado, rotulo = redimensionarLote(dado, fator=fator), redimensionarLote(rotulo, fator=fator)
            incrementarHDF5(datasetHDF5, dadosNovos=[dado, rotulo])
            totalAdicionado += len(dado)
            foramIncluidas += len(dado)
            imprimaBarraProgresso(totalAdicionado, qntFatias[0]*2, etapa='CONSTRUÇÃO DO CONJUNTO DE DADOS, ESTAMOS QUASE LÁ')
            if totalAdicionado == qntFatias[0]*2: break #Se o número de fatias já atingiu o dobro do numero de fatias do alvo, não incluimos mais.
        qntFatiasIncluidas.append(foramIncluidas) #Captura número de fatias incluidas da classe que estamos iterando.
        if totalAdicionado == qntFatias[0]*2: break #Se o número de fatias já atingiu o dobro do numero de fatias do alvo, não incluimos mais.    
    qntClassesNaoIncluidas = len(classes) - len(qntFatiasIncluidas)
    qntFatiasIncluidas.extend([0] * qntClassesNaoIncluidas) # Preenchendo com zeros para as classes que não foram incluídas
    datasetHDF5 = renomearArquivo(datasetHDF5, gerarNomePastaDestino(proporcoes=obterProporcoes(qntFatiasIncluidas), tamanho=tamanho) + '.h5')
    printColorido(f'CONJUNTO DE DADOS SALVO: {datasetHDF5}                                                                                ', 'g', '\r')
    return datasetHDF5
    