import xarray as xr
from subprocess import run, DEVNULL
import xmltodict
from parametros import * 
import numpy as np

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
        lat, lon = [lat[0][0], lat[0][-1], lat[-1][0], lat[-1][-1]], [lon[0][0], lon[0][-1], lon[-1][0], lon[-1][-1]]
        lat, lon = np.asarray(lat), np.asarray(lon) 
    return lat, lon

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