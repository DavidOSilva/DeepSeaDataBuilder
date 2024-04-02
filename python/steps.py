from python.substeps import *
from parametros import *
from os import listdir, getcwd
from os.path import join, isdir, exists
from pathlib import Path
import datetime

def converterEmNpz(dirNpz=Path(parametros['diretorios']['npzs']), dirNetcdf=Path(parametros['diretorios']['netcdfs']),
                    dirJson=Path(parametros['diretorios']['jsons']), forcarConversao=parametros['geral']['converter']):
    if not verificaEquivalenciaEntreDiretorios(dirNetcdf, dirJson):
        printColorido('TODOS OS NETCDFS DEVEM POSSUIR UM JSON ASSOCIADO E VICE-VERSA!', 'r')
        return None
    if parametros['geral']['modoRetirarSolo'] == 'snap': printColorido('VAMOS UTILIZAR O SNAP PARA PROCESSAR CADA NETCDF, ISSO PODE LEVAR UM TEMPINHO...                                      ','b', '\r')
    dirPasta, jsons = criarPasta(dirNpz/f"{parametros['geral']['modoRetirarSolo'].upper()}"), sorted(list(dirJson.glob('*.json')))
    for i, stem in enumerate(map(lambda json: json.stem, jsons)): #Itera sobre cada um dos stems considerando os jsons.
        #Se o arquivo já foi convertido(stem.h5 existe) mas o netcdf (stem.nc) é mais antigo que o arquivo convertido (stem.h5), então não convertemos.
        if (dirPasta/f'{stem}.npz').exists() and not (dirNetcdf/f'{stem}.nc').stat().st_mtime > (dirPasta/f'{stem}.npz').stat().st_mtime and not forcarConversao: continue 
        else:
            sigma, sigmaSemSolo, sigmaSemMar, borda = converterNetcdfParaArray(dirNetcdf/f'{stem}.nc')
            rotulo = converterJsonParaArray(dirJson/f'{stem}.json', sigmaSemSolo, sigmaSemMar, borda)
            np.savez_compressed(dirPasta/f'{stem}.npz', dado=sigma, rotulo=rotulo)
            imprimaBarraProgresso(i+1, len(jsons), etapa='CONVERSÃO PARA NPZ')
    return dirPasta

def recortarEmFatias(tamanho, npzConvertidos, dirHDF5=parametros['diretorios']['temporarios'], valoresVazios=['null'], detalhes=parametros['visualizar']['exibirQuantidadeFatias']):
    if parametros['geral']['aprimorarRotulo']: valoresVazios=['null', 'ocean'] #Com os rotulos aprimorados teremos muitos pixels de ocean.
    dirFatiados = criarPasta(join(dirHDF5, 'FATIADOS'))
    hdf5File = criarHDF5Vazio(join(dirFatiados, f'[{tamanho}].h5'), tamanho=tamanho)
    npzs = sorted(npzConvertidos.glob('*.npz'))
    for indice, npz in enumerate(npzs):
        sigma, rotulo = carregarNpzArrays(npzConvertidos/f'{npz}')
        if parametros['geral']['retirarExcessos']: sigma, rotulo = retirarExcessos(sigma, rotulo, valoresVazios=valoresVazios)
        dadosFatiados, rotulosFatiados = fatiarComDiferentesPtsIniciais(sigma, rotulo, tamanho=tamanho, ptsIniciais=[0]) #[0, tamanho//2]
        incrementarHDF5(hdf5File, dadosNovos=[dadosFatiados, rotulosFatiados]) # Adiciona os dados fatiados ao arquivo HDF5
        if not parametros['visualizar']['plotarSemExcessos']: imprimaBarraProgresso(indice+1, len(npzs), etapa='RECORTE EM FATIAS')
    if detalhes: printColorido(f"QUANTIDADE TOTAL DE FATIAS OBTIDAS: {lenHDF5(hdf5File, dataset='dado')}                                        ",'g','\r') 
    return hdf5File

def separarFatiasPorClasses(hdf5Fatiados, tamanho, dirHDF5=parametros['diretorios']['temporarios'], alvo=parametros['geral']['classeAlvo'], classes=obterClassesParametros()):
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
            if classe == alvo: filtrados, restante = filtrar(restante[0], restante[1], classe) #Usa limiar de parametros.
            else: filtrados, restante = filtrar(restante[0], restante[1], classe, limiar=0)
            if len(filtrados[0])>0: incrementarHDF5(hdf5Filtrados, dadosNovos=[filtrados[0], filtrados[1]], grupo=classe)
        if not parametros['visualizar']['detalharFiltragem']: imprimaBarraProgresso(i+1, qntdLotes, etapa='FILTRAGEM ENTRE AS CLASSES')
        else: 
            mensagem = '' #Exibe a quantidade de fatias para cada classe toda vez que um dos lotes é filtrado.
            for classe in classes: mensagem += f'{classe.upper()}: {lenHDF5(hdf5Filtrados, grupo=classe)}   '
            mensagem += f'LOTE: {i+1}/{qntdLotes}'
            printColorido(mensagem,'b', '\r')      
    return hdf5Filtrados

def embaralharFiltrados(hdf5, tamanho):
    tamanhoLote, classes = aproximarLote(tamanho), obterClassesParametros(seraoIgnorados=['null'])
    for classeIdx, classe in enumerate(classes):
        qntdLotes = obterQuantidadeDeLotes(comprimento=lenHDF5(hdf5, grupo=classe), tamanhoLote=tamanhoLote)
        if qntdLotes == 0: continue
        for i in range(qntdLotes):
            inicioLote, fimLote = i*(tamanhoLote//2), i*(tamanhoLote//2) + tamanhoLote
            dados, rotulos = carregarHDF5(hdf5, indices=[inicioLote, fimLote], grupo=classe)
            indices = list(range(len(dados)))
            random.shuffle(indices)
            dadosEmbaralhados, rotulosEmbaralhados = [dados[i] for i in indices], [rotulos[i] for i in indices]
            sobrescreverHDF5(hdf5, dadosNovos=[dadosEmbaralhados, rotulosEmbaralhados], grupo=classe)
        imprimaBarraProgresso(classeIdx+1, len(classes), etapa='EMBARALHAMENTO DAS CLASSES')
    return hdf5

def aumentoDeDadosHDF5(hdf5Filtrados, tamanho, probabilidade=parametros['geral']['probabilidade']):
    tamanhoLote = aproximarLote(tamanho)
    sufixo, classesAumentadas = '', encontrarClassesAumentadas(hdf5Filtrados, alvo=parametros['geral']['classeAlvo'])
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
    return hdf5Filtrados, classesAumentadas

def criarConjuntoDeDados(hdf5Filtrados, tamanho, classesAumentadas, dirDataset=parametros['diretorios']['dataset'], detalhar=parametros['visualizar']['detalharConstrucao']):
    classes, qntFatias, tamanhoLote, proporcoes = obterClassesParametros(), obterQntFatiasFiltradasHDF5(hdf5Filtrados), aproximarLote(tamanho), extrairProporcoes()
    datasetPasta = criarPasta(join(dirDataset, f'{tamanho}'))
    datasetHDF5 = criarHDF5Vazio(join(datasetPasta, f'[EM ANDAMENTO...][{tamanho}].h5'), tamanho)
    etapaBarraProgresso, fatiasAdicionadasDasClasses, totalDataset, faltouNaClassePassada = 0, [], qntFatias[0]/proporcoes[0], 0
    for classeIndex, classe in enumerate(classes):
        qntdLotes = obterQuantidadeDeLotes(comprimento=qntFatias[classeIndex], tamanhoLote=tamanhoLote)
        faltaAdicionarNestaClasse, adicionados =  int(round(totalDataset*proporcoes[classeIndex])) + faltouNaClassePassada, 0
        if detalhar: printColorido(f'\nclasse: {classe}   disponivel: {lenHDF5(hdf5Filtrados, grupo=classe)}   faltaAdicionarNestaClasse: {faltaAdicionarNestaClasse}  faltouNaClassePassada: {faltouNaClassePassada}')
        for loteIndex in range(qntdLotes):
            if faltaAdicionarNestaClasse <= 0: break
            inicioLote = loteIndex*tamanhoLote
            fimLote =  min(inicioLote + tamanhoLote, inicioLote + faltaAdicionarNestaClasse)
            dado, rotulo = carregarHDF5(hdf5Filtrados, indices=[inicioLote, fimLote], grupo=classe)
            incrementarHDF5(datasetHDF5, dadosNovos=[dado, rotulo])
            adicionados += len(dado)
            etapaBarraProgresso += len(dado)
            faltaAdicionarNestaClasse -= len(dado)
            faltouNaClassePassada = faltaAdicionarNestaClasse
            if detalhar: printColorido(f'\t  adicionados: {adicionados}  faltaAdicionarNestaClasse: {faltaAdicionarNestaClasse}  faltouNaClassePassada: {faltouNaClassePassada}', 'c')
            else: imprimaBarraProgresso(etapaBarraProgresso, int(round(totalDataset)), etapa='CONSTRUÇÃO DO CONJUNTO DE DADOS, ESTAMOS QUASE LÁ')
        fatiasAdicionadasDasClasses.append(adicionados) #Captura o número de fatias incluidas da classe que estamos iterando.
    fatiasAdicionadasDasClasses.append(adicionados) #Captura o número de fatias incluidas da ultima classe vista.
    if detalhar: printColorido(f'\nfatiasAdicionadasDasClasses: {fatiasAdicionadasDasClasses}   totalDataset: {sum(fatiasAdicionadasDasClasses)}')
    novoNome = gerarNomePastaDestino(proporcoes=obterProporcoesReais(fatiasAdicionadasDasClasses), tamanho=tamanho, classesAumentadas=classesAumentadas) + '.h5'
    datasetHDF5 = renomearArquivo(datasetHDF5, novoNome)
    printColorido(f'CONJUNTO DE DADOS SALVO: {datasetHDF5}                                                                                ', 'g', '\r')
    return datasetHDF5
    