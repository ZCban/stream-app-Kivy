# channels_registry.py

# Importa i tuoi plugin (sorgenti dei canali)
from plugins import guardaserietvpro,altadefinizione,calcioGA,SportZone,CalcioStreamingLat,StreamingCommunity,filmsenzalimiti

# Lista di canali disponibili
CHANNELS = [
    guardaserietvpro,
    altadefinizione,
    calcioGA,
    SportZone,
    StreamingCommunity,
    filmsenzalimiti,
    #CalcioStreamingLat, #non funzionante disattivato 
]
