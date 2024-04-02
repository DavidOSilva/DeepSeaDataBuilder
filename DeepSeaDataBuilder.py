from python.steps import *
from python.filesManager import *
from parametros import * 

for tamanho in parametros['geral']['tamanhos']:
    npzConvertidos = converterEmNpz()
    hdf5Fatiados = recortarEmFatias(tamanho, npzConvertidos)
    hdf5Filtrados = separarFatiasPorClasses(hdf5Fatiados, tamanho)
    hdf5Embaralhados = embaralharFiltrados(hdf5Filtrados, tamanho)
    hdf5Aumentado, classesAumentadas = aumentoDeDadosHDF5(hdf5Embaralhados, tamanho)
    datasetHDF5 = criarConjuntoDeDados(hdf5Aumentado, tamanho, classesAumentadas)
    deletarPastas([parametros['diretorios']['temporarios']])
    break