# channels_registry.py

# Importa i tuoi plugin (sorgenti dei canali)
from plugins import guardaserietvpro,altadefinizione,calcioGA,SportZone,CalcioStreamingLat

# Lista di canali disponibili
CHANNELS = [
    guardaserietvpro,
    altadefinizione,
    calcioGA,
    SportZone,
    #CalcioStreamingLat, #non funzionante disattivato 
]
