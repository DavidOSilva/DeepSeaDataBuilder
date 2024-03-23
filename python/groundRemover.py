import numpy as np
from global_land_mask import globe # https://github.com/toddkarin/global-land-mask
import cartopy.feature as cfeature
from shapely.geometry import Polygon, MultiPolygon
from cv2 import fillPoly, flip

from python.netcdfManager import *

def geometriasParaPoligonos(geometrias):
    poligonos = []
    for geometria in geometrias:
        if isinstance(geometria, Polygon): geometries = [geometria]
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