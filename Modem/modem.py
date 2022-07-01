fe = 44100 #frecventa de esantionare
bitRate = 1000 #rata de biti
fp = 7000 #frecventa semnalului purtator
Tb = 1/bitRate #baud rate

import numpy as np
from scipy import signal
#import alte module necesare

def studenti():
    return "Bode Mateo"

def nrBitiTest():

    return 5000 # se va trece un numar corespunzator dar nu mai mic ca 256

def modulare(msg: list):

    A = 1 #amplitudine
    Te = 1/fe #perioada de eșantionare
    Nepb = int(Tb*fe) 
    niv = [-A, A] # niveluri pt amplitudine
    Nb = len(msg)  #numarul de biti

    #modulatia BPSK
    Ne =  Nb*Nepb
    t = np.arange(0,Tb*Nb,Te)[:Ne]
    sm = np.zeros(Ne)

    for k in range(Nb):
        sm[k*Nepb:(k+1)*Nepb]=niv[msg[k]] #NRZ bipolar
    
    sp = np.cos(2*np.pi*fp*t) #semnalul purtator
    sM = sm*sp #modulatia de produs

    #se returneaza semnalul modulat
    return sM


def demodulare(sR: np.ndarray):
    
    #inainte sa incep demodularea am incercat sa sterg timpul mort a semnalului receptionat (sR)
    #consider ca si cum este un "time lag" dintrun stimul dat unui raspuns si raspunsul rezultat
    #asadar stergerea timpului mort pe sR face sa se aproprie mai mult de semnalul trimis original

    index = np.where(np.abs(sR) > 0.5)
    index = int(index[0][0])
    
    if index < 100:
        sR = sR[index:]
    
    sR = sR[index:]

    Nepb = int(Tb*fe)
    Ne = len(sR)
    Te = 1/fe # perioada de esantionare
    T = len(sR)*Te # durata semnalului
    t = np.arange(0,T,Te) 
    t = t[0:len(sR)]
    phi=0 

    spr=2*np.cos(2*np.pi*fp*t+phi) # semnalul purtător de la recepție
    
    # demodularea de produs
    sx=sR*spr
    # acum trebuie FTJ
    NF = 599
    bFTJ = signal.remez(NF,[0, 0.005, 0.02, 0.5], [1, 0]) 
    Ne_prel = int(NF/2)
    sx_prel =np.append(sx,np.zeros(Ne_prel))

    y = signal.lfilter(bFTJ,1,sx_prel)
    y = y[Ne_prel:]
        
    #numărul de biți așteptat
    nb = int(Ne/Nepb)

    Nejb = int(Nepb/2) 
    yd = [y[Nejb+i*Nepb] for i in range(0,nb)]
    
    yb = [0]*nb
    
    prag = 0
    for i in range(0,nb):
        if (yd[i]>prag):
            yb[i]=1

    return yb
    