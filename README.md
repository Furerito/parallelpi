
# Parallel PI – Parallele Berechnung von Pi in Python

Dieses Projekt berechnet die Zahl π (Pi) parallelisiert mit Hilfe der Leibniz-Reihe. Die Implementierung unterstützt verschiedene Modi: klassische Python-Threads (mit GIL), parallele Threads (theoretisch ohne GIL, aber praktisch identisch), parallele Prozesse, Prozess-Pools und die simulierte Verteilung auf mehrere Hosts.

---

## **Leibniz-Formel**

[![leibnitz](https://raw.githubusercontent.com/Furerito/parallelpi/refs/heads/main/leibnitz.png)]
---

## **Nutzung**

Das Skript heisst `pi.py`.  
Starte es im Terminal wie folgt:

```bash
python pi.py -i ITERATIONEN [Modus-Flag] [-k ARBEITER]
````

### Beispiele:

* Mit Python-Threads (GIL):

  ```bash
  python pi.py -i 100000 --with-gil
  ```

* Mit parallelen Threads (identisch, aber anderer Parameter):

  ```bash
  python pi.py -i 100000 --with-thread
  ```

* Mit mehreren Prozessen:

  ```bash
  python pi.py -i 100000 --with-proces
  ```

* Mit mehreren Arbeitern (Threads/Prozesse):

  ```bash
  python pi.py -i 100000 --with-gil -k 8
  ```

* Mit Prozess-Pool:

  ```bash
  python pi.py -i 100000 --pool 8
  ```

  → Nutzt einen Pool mit 8 Prozessen für echte Parallelisierung.

* Mit "Hosts"-Simulation:

  ```bash
  python pi.py -i 100000 --hosts host1,host2,host3
  ```

  → Die Arbeit wird auf die angegebenen Hosts verteilt (simuliert, keine echte Netzwerkkommunikation).

* Mit Segmenten auf Hosts:

  ```bash
  python pi.py -s 2 --seg-size 10000 --hosts host1,host2
  ```

  → Berechnet nur das Segment Nr. 2 mit Grösse 10000 auf den Hosts host1 und host2.

---

## Kurzbeschreibung der Modi

* **--with-gil / --with-thread**
  → Nutzt Python-Threading (wegen des Global Interpreter Lock (GIL) laufen Threads nicht wirklich parallel, aber die Syntax ist vorbereitet).

* **--with-proces**
  → Nutzt das `multiprocessing`-Modul. Echte Parallelität, da jeder Prozess einen eigenen Python-Interpreter und Speicherraum hat.

* **--pool N**
  → Nutzt einen Prozess-Pool mit N Prozessen zur parallelen Berechnung (empfohlen für grosse Iterationszahlen).

* **--hosts h1,h2,...**
  → Simuliert die Verteilung der Arbeit auf verschiedene Hosts (keine echte Verteilung, sondern Anzeige, was auf welchem Host berechnet würde).

* **-s N --seg-size X --hosts ...**
  → Startet die Berechnung für ein einzelnes Segment (z.B. für einen Host, der im Cluster-Modus arbeitet). Segment N beginnt bei N\*X und geht bis (N+1)\*X.

* **Ohne Modus-Flag**
  → Fallback: Single-Thread (ohne Parallelisierung).

---

## Ablauf

1. Die Gesamtsumme wird auf die gewünschte Anzahl Threads/Prozesse/Hosts/Segmente aufgeteilt.
2. Jeder Thread/Prozess/Host berechnet einen Teil der Reihe.
3. Die Teilergebnisse werden zusammengeführt und ergeben die Annäherung an π.

---

## Voraussetzungen

* Python 3.6 oder neuer (Standard-Library, keine zusätzlichen Abhängigkeiten)
* Linux/Mac/Windows (empfohlen: Linux für multiprocessing)

---

## Visualisierung / Architektur-Skizze

[![diagramm](https://raw.githubusercontent.com/Furerito/parallelpi/refs/heads/main/diagram.png)]