# Parallel PI – Parallele Berechnung von Pi in Python

Dieses Projekt berechnet die Zahl π (Pi) parallelisiert mit Hilfe der Leibniz-Reihe. Die Implementierung unterstützt verschiedene Modi: klassische Python-Threads (mit GIL), parallele Threads (theoretisch ohne GIL, aber praktisch identisch), und parallele Prozesse.

---

## **Leibniz-Formel**

\[
\frac{\pi}{4} = 1 - \frac{1}{3} + \frac{1}{5} - \frac{1}{7} + \frac{1}{9} - \cdots = \sum_{k=0}^\infty \frac{(-1)^k}{2k + 1}
\]

---

## **Nutzung**

Das Skript heisst `pi.py`.  
Starte es im Terminal wie folgt:

```bash
python pi.py -i ITERATIONEN [Modus-Flag] [-k ARBEITER]

python pi.py -i 100000 --with-gil
python pi.py -i 100000 --with-thread
python pi.py -i 100000 --with-proces
python pi.py -i 100000 --with-gil -k 8
 ```

 ## Kurzbeschreibung der Modi

- **--with-gil / --with-thread**  
  → Nutzt Python-Threading (wegen des Global Interpreter Lock (GIL) laufen Threads nicht wirklich parallel, aber die Syntax ist vorbereitet).

- **--with-proces**  
  → Nutzt das `multiprocessing`-Modul. Echte Parallelität, da jeder Prozess einen eigenen Python-Interpreter und Speicherraum hat.

- **Ohne Modus-Flag**  
  → Fallback: Single-Thread (ohne Parallelisierung).

---

## Ablauf

1. Die Gesamtsumme wird auf die gewünschte Anzahl Threads/Prozesse aufgeteilt.
2. Jeder Thread/Prozess berechnet einen Teil der Reihe.
3. Die Teilergebnisse werden zusammengeführt und ergeben die Annäherung an π.

---

## Voraussetzungen

- Python 3.6 oder neuer (Standard-Library, keine zusätzlichen Abhängigkeiten)
- Linux/Mac/Windows (empfohlen: Linux für multiprocessing)

---

## Visualisierung / Architektur-Skizze
@startuml
actor "User" as user

user -> "pi.py": Startet mit CLI-Parametern

rectangle "Argumente parsen" as parse
rectangle "Arbeiter-Manager" as manager
rectangle "Threads ODER Prozesse" as worker_pool
rectangle "Thread/Prozess" as worker
rectangle "Resultat zusammenfassen" as result

"pi.py" --> parse
parse --> manager
manager --> worker_pool
worker_pool --> worker
worker --> result
result -> user : Ausgabe Pi

note right of manager
  Teilt Iterationen auf Segmente auf
end note

note right of worker
  Berechnet Teil-Summe
  Gibt Ergebnis zurück
end note

@enduml
