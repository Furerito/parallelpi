import argparse
import threading
import multiprocessing
import math
import sys
import time
import os
import paramiko  # Für SSH-Verbindungen
import json

# Berechnet einen Teil der Leibniz-Reihe: π/4 = 1 - 1/3 + 1/5 - 1/7 + ...
# Diese Funktion berechnet die Summe für einen bestimmten Bereich [start, end)
def leibniz(start, end):
    result = 0.0
    for k in range(start, end):
        result += ((-1) ** k) / (2 * k + 1)
    return result

# Thread/Prozess Worker-Funktion für die parallele Verarbeitung
# Berechnet einen Teil der Leibniz-Reihe und speichert das Ergebnis in einer geteilten Liste
def worker(start, end, result_list, idx):
    result_list[idx] = leibniz(start, end)

# Worker-Funktion für den Process Pool
# Erwartet ein Tupel mit Start- und Endwerten
def pool_worker(args):
    start, end = args
    return leibniz(start, end)

def read_hosts_file(file_path="hosts"):
    """
    Liest die Hosts-Datei mit IP, Benutzername und Passwort ein.
    Format: ip,username,password (eine Host-Konfiguration pro Zeile)
    """
    hosts = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) >= 3:
                        hosts.append({
                            'ip': parts[0].strip(),
                            'username': parts[1].strip(),
                            'password': parts[2].strip()
                        })
        return hosts
    except Exception as e:
        print(f"Fehler beim Lesen der Hosts-Datei: {e}")
        return []

def execute_on_remote_host(host_info, command):
    """
    Führt einen Befehl auf einem entfernten Host aus und gibt das Ergebnis zurück.
    """
    client = None
    try:
        # SSH-Verbindung aufbauen
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host_info['ip'],
            username=host_info['username'],
            password=host_info['password']
        )
        
        # Befehl ausführen
        stdin, stdout, stderr = client.exec_command(command)
        
        # Ergebnis lesen
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if error:
            print(f"Fehler auf Host {host_info['ip']}: {error}")
            return None
        
        return result
    except Exception as e:
        print(f"Fehler bei der Ausführung auf Host {host_info['ip']}: {e}")
        return None
    finally:
        if client:
            client.close()

# Simuliert die Verteilung der Berechnungen auf mehrere Hosts
# In dieser Implementierung wird alles lokal berechnet, aber die Verteilung simuliert
def simulate_hosts(hosts_param, segments):
    """
    Verteilt die Arbeit auf echte Remote-Hosts via SSH.
    
    Args:
        hosts_param: Liste der Hostnamen oder Pfad zur Hosts-Datei
        segments: Liste der zu berechnenden Segmente [(start1, end1), (start2, end2), ...]
    
    Returns:
        Liste der berechneten Teilergebnisse
    """
    # Hosts einlesen (entweder aus Datei oder direkt als Liste verwenden)
    if isinstance(hosts_param, str) and os.path.exists(hosts_param):
        hosts_info = read_hosts_file(hosts_param)
    elif isinstance(hosts_param, str) and hosts_param.endswith('.txt'):
        hosts_info = read_hosts_file("hosts")
    else:
        # Wenn hosts_param eine Liste von Hostnamen ist, verwende die Standard-Hosts-Datei
        hosts_info = read_hosts_file()
    
    if not hosts_info:
        print("Keine Hosts gefunden. Berechne lokal...")
        results = []
        for start, end in segments:
            results.append(leibniz(start, end))
        return results
    
    # Zuordnen der Segmente zu den Hosts (Round-Robin)
    host_count = len(hosts_info)
    host_work = {i: [] for i in range(host_count)}
    
    for idx, segment in enumerate(segments):
        host_idx = idx % host_count
        host_work[host_idx].append(segment)
    
    results = []
    
    # Aufgaben an jeden Host verteilen und Ergebnisse einsammeln
    for host_idx, segments_for_host in host_work.items():
        if not segments_for_host:
            continue
            
        host_info = hosts_info[host_idx]
        print(f"[Host: {host_info['ip']}] bearbeitet Segmente: {segments_for_host}")
        
        # Aufruf des Skripts auf dem entfernten Host mit den Segmenten
        commands = []
        for i, (start, end) in enumerate(segments_for_host):
            # Stelle sicher, dass das Skript auf dem Remote-Host vorhanden ist
            # und führe es mit den entsprechenden Parametern aus
            command = f"python3 {os.path.basename(sys.argv[0])} --segment {i} --seg-size {end-start} --iterations {end}"
            result_str = execute_on_remote_host(host_info, command)
            
            if result_str:
                try:
                    # Versuche, den Ergebniswert aus der Ausgabe zu extrahieren
                    # Annahme: Das Ergebnis wird im Format "PI (Segment X): [Wert]" ausgegeben
                    pi_value_line = [line for line in result_str.split("\n") if "PI (Segment" in line]
                    if pi_value_line:
                        pi_value_str = pi_value_line[0].split(": ")[1]
                        # Da wir den Pi-Wert speichern und nicht direkt den Leibniz-Summenwert,
                        # müssen wir durch 4 teilen, um den richtigen Wert zu erhalten
                        result = float(pi_value_str) / 4
                        results.append(result)
                    else:
                        print(f"Warnung: Konnte kein Ergebnis aus Host {host_info['ip']} für Segment {start}-{end} extrahieren")
                except Exception as e:
                    print(f"Fehler beim Parsen des Ergebnisses von Host {host_info['ip']}: {e}")
                    print(f"Rohe Ausgabe: {result_str}")
    
    return results

def main():
    # Kommandozeilenargumente definieren
    parser = argparse.ArgumentParser(description='Parallel Pi Calculator')
    parser.add_argument('-i', '--iterations', type=int, help='Anzahl Iterationen')
    parser.add_argument('-k', '--workers', type=int, default=4, help='Anzahl Threads/Prozesse')
    parser.add_argument('--with-gil', action='store_true', help='mit GIL Threads (threading)')
    parser.add_argument('--with-thread', action='store_true', help='mit parallelen Threads (threading)')
    parser.add_argument('--with-proces', action='store_true', help='mit Prozessen (multiprocessing)')
    parser.add_argument('--pool', type=int, help='mit Pool aus N Prozessen')
    parser.add_argument('--hosts', type=str, help='Verteile Arbeit auf Hosts (kommagetrennt)')
    parser.add_argument('-s', '--segment', type=int, help='Nummer des Segments (für Einzel-Host-Betrieb)')
    parser.add_argument('--seg-size', type=int, help='Grösse eines Segments (für Einzel-Host-Betrieb)')
    args = parser.parse_args()

    # --- Segment-Modus: Berechnung eines einzelnen Segments für verteilte Berechnung ---
    # Wird verwendet, wenn ein Host nur einen Teil der Gesamtberechnung durchführt
    if args.segment is not None and args.seg_size is not None and args.hosts:
        start = args.segment * args.seg_size
        end = start + args.seg_size
        print(f"Segment-Modus: Bearbeite Segment {args.segment} (k={start} bis {end}) auf Hosts {args.hosts}")
        
        start_time = time.time()
        result = leibniz(start, end)
        elapsed = (time.time() - start_time) * 1000
        
        pi = 4 * result
        print(f"PI (Segment {args.segment}): {pi}")
        print(f"Verstrichene Zeit (Segment {args.segment}): {elapsed:.2f} ms")
        sys.exit(0)

    # --- Host-Modus: Simulation der Verteilung auf mehrere Hosts ---
    if args.hosts:
        if args.iterations is None:
            print("Bitte --iterations angeben!")
            sys.exit(1)
            
        # Hosts aus der Kommandozeile parsen
        hosts = [h.strip() for h in args.hosts.split(",")]
        k_workers = args.workers
        
        # Arbeit in Segmente aufteilen
        segment_size = args.iterations // k_workers
        segments = [(i * segment_size, (i + 1) * segment_size) for i in range(k_workers)]
        # Letztes Segment ggf. bis zum Ende auffüllen
        segments[-1] = (segments[-1][0], args.iterations)
        
        start_time = time.time()
        results = simulate_hosts(hosts, segments)
        pi = 4 * sum(results)
        elapsed = (time.time() - start_time) * 1000
        
        print(f"PI (simulierte Hosts): {pi}")
        print(f"Verstrichene Zeit (simulierte Hosts): {elapsed:.2f} ms")
        sys.exit(0)

    # --- Pool-Modus: Nutzung eines Process Pools für die Parallelisierung ---
    if args.pool:
        if args.iterations is None:
            print("Bitte --iterations angeben!")
            sys.exit(1)
            
        poolsize = args.pool
        
        # Arbeit in Segmente aufteilen
        segment_size = args.iterations // poolsize
        segments = [(i * segment_size, (i + 1) * segment_size) for i in range(poolsize)]
        segments[-1] = (segments[-1][0], args.iterations)
        
        start_time = time.time()
        with multiprocessing.Pool(poolsize) as pool:
            results = pool.map(pool_worker, segments)
        pi = 4 * sum(results)
        elapsed = (time.time() - start_time) * 1000
        
        print(f'PI (Pool mit {poolsize} Prozessen): {pi}')
        print(f"Verstrichene Zeit (Pool): {elapsed:.2f} ms")
        sys.exit(0)

    # --- Klassische Modi: Single-Thread, Threading oder Multiprocessing ---
    if args.iterations is None:
        print("Bitte --iterations angeben!")
        sys.exit(1)
        
    iterations = args.iterations
    k_workers = args.workers
    
    # Arbeit in gleich große Segmente aufteilen
    segment_size = iterations // k_workers
    segments = [(i * segment_size, (i + 1) * segment_size) for i in range(k_workers)]
    segments[-1] = (segments[-1][0], iterations)  # Letztes Segment bis zum Ende

    if args.with_gil or args.with_thread:
        # Threading-Modus (mit Global Interpreter Lock)
        threads = []
        results = [0.0] * k_workers  # Geteilte Liste für die Ergebnisse
        
        start_time = time.time()
        
        # Threads erstellen und starten
        for idx, (start, end) in enumerate(segments):
            t = threading.Thread(target=worker, args=(start, end, results, idx))
            threads.append(t)
            t.start()
            
        # Auf alle Threads warten
        for t in threads:
            t.join()
            
        pi = 4 * sum(results)
        elapsed = (time.time() - start_time) * 1000
        
        print(f'PI (threading): {pi}')
        print(f"Verstrichene Zeit (threading): {elapsed:.2f} ms")
    elif args.with_proces:
        # Multiprocessing-Modus (umgeht das GIL durch separate Prozesse)
        manager = multiprocessing.Manager()
        results = manager.list([0.0] * k_workers)  # Prozesssichere geteilte Liste
        processes = []
        
        start_time = time.time()
        
        # Prozesse erstellen und starten
        for idx, (start, end) in enumerate(segments):
            p = multiprocessing.Process(target=worker, args=(start, end, results, idx))
            processes.append(p)
            p.start()
            
        # Auf alle Prozesse warten
        for p in processes:
            p.join()
            
        pi = 4 * sum(results)
        elapsed = (time.time() - start_time) * 1000
        
        print(f'PI (multiprocessing): {pi}')
        print(f"Verstrichene Zeit (multiprocessing): {elapsed:.2f} ms")
    else:
        # Single-Thread-Modus (sequentielle Berechnung)
        start_time = time.time()
        pi = 4 * leibniz(0, iterations)
        elapsed = (time.time() - start_time) * 1000
        
        print(f'PI (single thread): {pi}')
        print(f"Verstrichene Zeit (single thread): {elapsed:.2f} ms")

if __name__ == '__main__':
    main()
