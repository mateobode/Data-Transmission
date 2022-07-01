# -*- coding: utf-8 -*-
"""
Program pentru verificarea functionalitatii si performantelor functiilor
din fisierul modem.py
versiunea 0.1.
"""

import modem

import numpy as np
import random
import sounddevice as sd


#constante
sep1 = "-"*40
sep2 = "="*40
# #praguri de multiplicare pentru rata de biti folosita de metoda de modulatie
# praguri_multiplicare = [ [100, 1],     #      100bps+ x 1  
#                          [1000, 1.5],  #       1kbps+ x 1.5
#                          [10000, 2],   #      10kbps+ x 2
#                          [50000, 2.5], #      50kbps+ x 2.5
#                         ] 
 
# raportul maxim de biti eronati acceptat pentru a considera un test trecut
BERmax = 1 # [%]



def computeBER(sir1, sir2):
    '''! Functie care calculeaza raportul de biti eronati (Bit Error Ratio) si o returneaza in procente
        @param sir1, sir2 Sirurile de biti ce vor fi comparate
        @return BER in procente
    '''
    try:
        sir3 = [sir1[k]^sir2[k] for k in range(len(sir1))]
    except:
        print("Eroare BER: ceva nu a mers bine!")
        return 100
    return sum(sir3)/len(sir3)*100


def chIdeal(si: np.ndarray):
    '''! Simuleaza efectul canalului ideal
        @param si Semnalul de la intrarea in canal
        @return semnalul de la iesirea din canal (in cazul acesta identic)
    '''
    so = si.copy()
    
    return so

def chAudioSimulat(si: np.ndarray):
    '''Simuleaza efectul canalului audio la care se considera frecventa de esantionare 44100Hz si frecventa de taiere 20Hz
        @param si Semnalul de la intrarea in canal
        @return semnalul de la iesirea din canal
    '''
    dt = 1/44100 # perioada de esantionare in [s]
    fc = 20 # frecventa de esantionare in [s]
    # o implementare de FTS cu un singur pol care discretizeaza comportamentul unui FTS format
    # dintr-o capacitate C in seria si o rezistenta R in paralel si a carui constanta de timp este RC
    # Un astfeld e filtru are frecventa de taiere ft=1/(2piRC)
    a = 1/(2*np.pi*dt*fc + 1)    
    so = si.copy()
    for i in range(1, si.size):
        so[i] = a*(so[i-1] + si[i] - si[i-1]) 
    
    return so

def chAWGN(si: np.ndarray):
    '''! Simuleaza efectul zgomotului gausian alb aditiv, considerand normalizata intrarea in intervalul [-1;1].
        Functia foloseste o variabila globala SNRdB ce exprima raportul semnal zgomot (in dB) la iesirea din canal 
        @param si Semnalul de la intrarea in canal
        @return semnalul de la iesirea din canal
    '''
    SNR = 10**(SNRdB/10) # transformarea din dB
    SP =  1/np.sqrt(2) # se calculează conform A/sqrt(2) unde A este amplitudinea purtatoarei care va fi 1 conform normalizarii
    zgomot = (SP/SNR)*np.random.randn(len(si)) # se generează un zgomot cu o denistate de probabilitate normală standard 
                                               # (medie 0 și deviație standard 1)
                                               # dar cu amplitudine ce poate duce la SNR-ul dorit
    # se observa ca zgomotul generat va fi independent de semnalul emis in canal si va fi la fel pentru toate metodele de modulatie
    NP = np.sqrt(np.sum((zgomot*zgomot)/len(zgomot))) # se calculează puterea RMS a zgomotului astfel generat
    print("Puterea zgomotului: {:.2f}, puterea semnalului: {:.2f}, eroarea relativa fata de SNR-ul dorit este {:.2f} %"\
      .format(NP, SP, np.abs(SNR - SP/NP)*100/SNR)) # se verifică eroarea de estimare a zgomotului
    
    so = si + zgomot # ieșirea va fi intrarea plus zgomot
    
    return so

def normalizare(si: np.ndarray):
    '''! Functie pentru normarea unui semnal in intervalul [-1,1] 
        @param si Semnalul de la intrarea in canal
        @return semnalul normalizat
    '''
    maxabs=np.max(np.abs(si))
    so = si/maxabs
    return so


def chIntarziere(si: np.ndarray):
    '''! Simuleaza efectul de intarziere (cu un interval aleatoriu) introdus de un canal
        @param si Semnalul de la intrarea in canal
        @return semnalul de la iesirea din canal
    '''   
    DtMax = 0.3 # Intarzierea maxima in secunde a semnalului
    NeiMax = int(DtMax*44100) # numarul maxim de esantioane care alcatuiesc intarzierea
    Nei = random.randint(100,NeiMax) # intarzierea va fi arbitrara 
    timpMort = np.zeros(Nei)
    so = np.append(timpMort,si)
    #si nu e suficent sa adaugam zerouri, va trebui si perturbat
    so = chAWGN(so)    
    return so

def chMulticale(si: np.ndarray):
    '''! Simuleaza efectul de propagare multicale introdus de un canal radio
        @param si Semnalul de la intrarea in canal
        @return semnalul de la iesirea din canal
    '''  
    so = chIntarziere(si)
    soc = so.copy() # o imagine a semnalului
    # ce va fi intarziata si atenuata
    soc = 0.2*chIntarziere(soc)
    #trebuie sa pastram din imaginea mai mica un numar de esantioane egal cu semnalul transmis pe
    #calea cea mai scurta
    so = so + soc[:len(so)]    
    return so


def chAudio(si: np.ndarray):
    '''! Testeaza semnalul modulat prin transmisia lui audio
        @param si Semnalul redat prin placa de sunet
        @return semnalul achizitionat prin placa de sunet
    '''  
    Nec = 20000
    so = np.append(si, np.zeros(Nec))
    so = sd.playrec(so, samplerate=44100, channels=2)
    sd.wait()
    so = so[:,0]
    
    return so

def testModulatie(msg: list):
    '''! Testeaza modulatorul
        @param msg Lista (sirul) de biti ce urmeaza a fi modulati 
        @return sM un vector de tip np.ndarray ce contine esantioanele semnalului modulat
        @return Rb rata de biti calculata (si folosita de modulator)
    '''  
    Nb = len(msg)
    try:
        sM = modem.modulare(msg)
    except:
        print("Eroare la modulatie!!!")
        return ([],0)
    if not isinstance(sM, np.ndarray):
        print("Functia de modulatie nu returneaza un np.ndarray!")
        return ([],0)
    if sM.ndim != 1:
        print("Functia de modulatie un np.ndarray cu dimenisune necorespunzatora!")
        return ([],0)
    Tb = len(sM)/Nb/44100
    Rb = 1/Tb
    print("Metoda de modulatie foloseste o rata de biti de {:.1f} bps".format(Rb))
    return (sM,Rb)

def testTransmisie(sM, modelCh, msg):
    '''! Testeaza transmisia printr-un anumit tip de canal (inclusiv demodularea)
        @param sM un vector de tip np.ndarray ce contine esantioanele semnalului modulat
        @param modelCh o functie care modeleaza un canal
        @param msg Lista (sirul) de biti folositi la modulatie pentru a calcula BER  
        @return 1 daca a trecut testul si 0 daca l-a picat
    '''     
    try:
        sR = modelCh(sM)
    except:
        print("Eroare la trimiterea prin canala! ceva nu a mers bine...")
        return 0
    try:
        msgR = modem.demodulare(sR)
    except:
        print("Eroare la demodulatie!!!")
        return 0
    if not isinstance(msgR, list):
        print("Functia de demodulatie nu returneaza o lista!")
        return 0
    if (msgR.count(0) + msgR.count(1))!=len(msgR):
        print("Mesajul recuperat contine si altceva in afara de biti!")
        return 0
    BER = computeBER(msg,msgR)
    print("BER = {:.2f} %".format(BER))
    if BER<BERmax:
        return 1
    else:
        return 0



# modelele de canal [modelcanal, SNRdB, punctaj]
modeleCh = [ [chIdeal, 0, 2], # ch ideal ignora SNR
             [chAWGN, 10, 2],
             [chAWGN, 3, 1],
             [chAWGN, 0, 1],
             [chAWGN, -3, 1],
             [chAudioSimulat, 0, 1], #ignora SNR
             [chIntarziere, 10, 1],
             [chMulticale, 10, 1],
             [chAudio, 0, 1], #ignora SNR pentru ca va exista zgomot real
]

#incepe verificarea
print(sep2)
print("Start test...")
print(sep1)

#afisare membrii echipei
print("Componenta echipa: ", modem.studenti())
#verificarea numarului de biti dorit pentru test
try:
    Nb = int(modem.nrBitiTest())
    if  Nb < 256:
        Nb = 256
except:
    Nb = 256
print("\nPentru test se vor folosi {} biti si un prag pentru BER de {:.2f}%!".format(Nb,BERmax))
print(sep2)

#generare biti
msg = [random.randint(0,1) for k in range(Nb)]

punctaj = 0
#mai intai se testeaza metoda de modulatie
print("Testarea metodei de modulatie -> ", end="")
(sM, Rb) = testModulatie(msg)
#apoi se normeaza semnalul de la iesirea modulatorului pentru a nu se folosi puteri exagerate si 
#pentru a se putea transmite pe placa de sunet
sM = normalizare(sM)

if len(sM)==0:
    print("Modulatia nu functioneaza! Restul testelor nu isi mai au rostul!")
    print(sep2)
else:
    # K = 0
    # for [rb, k] in praguri_multiplicare:
    #     if Rb > rb:
    #         K = k
    K = np.log10(Rb)/2
    print("Factorul de multiplicare al punctajului este: {:.2f}".format(K) )

    nrTest = 0
    #efectuare teste
    for [modelCh, SNRdB, pt] in modeleCh:
        nrTest = nrTest + 1
        print(sep1)
        print("Test ", nrTest, " ... ")
        rez = testTransmisie(sM, modelCh, msg)
        if rez==1:
            print("PASS!")
        else:
            print("FAIL!")
        punctaj += rez*pt*K
        print("Punctaj intermediar: {:.2f}".format(punctaj) )
    
    print(sep2)
    print("Testele s-au finalizat")
    print("Punctajul obtinut: ", min([round(punctaj,1),30]))
    print(sep2)


