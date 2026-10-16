[English](README.md) | [Italiano](README.it.md)

Demo online: [customer-repeat-purchase-analysis](https://gr1gorii.github.io/customer-repeat-purchase-analysis/)

# customer-repeat-purchase-analysis

Un'analisi in Python e SQL degli acquisti ripetuti, delle coorti di clienti, degli annullamenti e delle vendite nette registrate nel dataset pubblico UCI Online Retail. Il codice è pensato per essere facile da leggere e verificare. DuckDB conserva localmente i dati puliti, mentre una piccola dashboard statica permette di esplorare i risultati senza compilare un frontend né usare servizi esterni.

![customer-repeat-purchase-analysis: Panoramica della dashboard con vendite, finestre di riacquisto e andamento mensile](reports/dashboard-overview.png)

Il file registra **£9,75 milioni di vendite nette** e **4.338 clienti identificabili con almeno un acquisto**. Tra i clienti con una finestra di osservazione completa di 30 giorni, **907 su 4.070 (22,3%)** hanno effettuato un acquisto su un'altra fattura. Sono risultati storici, non utili né stime di un miglioramento del business.

![customer-repeat-purchase-analysis: Attività delle coorti di clienti per mese di calendario](reports/cohort-activity.png)

Ogni riga segue i clienti a partire dal mese del loro primo acquisto osservato. Le celle indicano la quota che ha acquistato in un mese successivo; le celle grigie corrispondono a periodi di osservazione incompleti. I filtri per paese e coorte permettono di esplorare singoli gruppi di clienti. [Apri la schermata desktop completa](reports/qa-desktop.png) oppure [guarda la versione mobile](reports/qa-mobile.png).

## Domande a cui risponde il progetto

- Quali coorti tornano ad acquistare e in quali mesi di calendario?
- Quanti clienti acquistano su un'altra fattura entro 30, 60 e 90 giorni, considerando soltanto finestre di osservazione complete?
- In che modo le registrazioni negative con prezzo positivo incidono sulle vendite nette, e quali elementi consentono di collegarle a precedenti righe di acquisto?
- Come cambiano i dati utilizzabili in presenza di identificativi mancanti, duplicati, prezzi non validi e mesi incompleti?

## Avviare la demo con i risultati inclusi

Clona il repository con il nome di cartella usato in queste istruzioni, oppure usa la cartella locale già esistente:

```bash
git clone https://github.com/Gr1gorii/customer-repeat-purchase-analysis.git retail-cohort-analytics
cd retail-cohort-analytics
python3 -m http.server 8764 --bind 127.0.0.1
```

Apri **http://127.0.0.1:8764/web/**. Mantieni il server sull'indirizzo di loopback. Non servono API esterne, account, servizi cloud o dipendenze a pagamento. Usa i filtri per paese e mese del primo acquisto osservato; il pulsante di ripristino torna alla vista iniziale. Il filtro per coorte si applica soltanto alle metriche dei clienti, come indicato nell'interfaccia. Le vendite sono attribuite al paese della transazione, mentre le metriche dei clienti usano il paese del primo acquisto osservato. Per arrestare il server, premi Ctrl+C.

## Riprodurre l'analisi dalla fonte originale

Il progetto è stato eseguito con Python 3.11. Le dipendenze necessarie all'analisi sono DuckDB, pandas e openpyxl; gli strumenti di sviluppo sono pytest, Ruff e, facoltativamente, Playwright. Le versioni dell'intero ambiente verificato sono fissate in `requirements.lock`.

Esegui questi comandi dalla directory del progetto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
PYTHONPATH=src .venv/bin/python -m retail.pipeline
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
```

Alla prima esecuzione, la pipeline scarica circa 23 MB da UCI, estrae il file Excel previsto dall'archivio, registra gli hash, pulisce 541.909 righe, ricrea `data/processed/retail.duckdb`, esporta i dati puliti in Parquet per consentire le verifiche e rigenera CSV, JSON e il riepilogo gestionale in inglese. Le esecuzioni successive riutilizzano lo ZIP locale e ricreano gli output senza accumulare duplicati. Su un portatile, la lettura del file Excel richiede indicativamente 20-45 secondi. Se il download non riesce, riprova quando la connessione è disponibile: il progetto non sostituisce i dati con un altro dataset o con dati inventati. I dati originali, il database, il file Parquet e `.venv` sono esclusi da Git tramite `.gitignore`; gli aggregati verificati e la demo sono invece inclusi.

Per la verifica facoltativa dell'interfaccia nel browser:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/retail-playwright .venv/bin/playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=/tmp/retail-playwright .venv/bin/python scripts/browser_qa.py
```

Lo script avvia un server temporaneo sull'indirizzo di loopback, verifica le viste desktop e mobile, i filtri, le selezioni vuote, le azioni ripetute e la gestione degli errori, salva gli screenshot e arresta il server. L'esecuzione del browser può richiedere un'autorizzazione nell'ambiente locale con sandbox. La demo normale non richiede Playwright.

## Risultati del file analizzato

| Misura | Risultato |
|---|---:|
| Righe conservate dopo la rimozione di 5.268 duplicati esatti | 536.641 |
| Clienti identificabili con acquisti / fatture di acquisto | 4.338 / 18.532 |
| Righe originali senza CustomerID | 135.080 (24,9%) |
| Valore delle righe con quantità e prezzo positivi | £10.642.110,804 |
| Valore assoluto delle righe con quantità negativa e prezzo positivo | £893.979,730 |
| Vendite nette registrate | £9.748.131,074 |
| Clienti con riacquisto entro 30 giorni / clienti con finestra completa | 907 / 4.070 (22,3%) |
| Clienti con riacquisto entro 60 giorni / clienti con finestra completa | 1.403 / 3.731 (37,6%) |
| Clienti con riacquisto entro 90 giorni / clienti con finestra completa | 1.605 / 3.370 (47,6%) |

Prima di aggiornare la demo locale, ogni cella SQL relativa a riacquisti, coorti e valori monetari per paese e mese viene confrontata con un calcolo indipendente in pandas. Le verifiche già registrate comprendono 12 test superati, i controlli di Ruff e i controlli in Chromium su filtri, selezioni vuote, azioni ripetute, layout mobile ed errori di caricamento dei dati. I documenti collegati descrivono le verifiche eseguite e i relativi limiti.

## Interpretazione e limiti

- I dati coprono il periodo dal 2010-12-01 al 2011-12-09. Dicembre 2011 è incompleto e non va confrontato con mesi di calendario interi.
- Le finestre di 30, 60 e 90 giorni hanno popolazioni diverse. Un cliente entra nel denominatore di una finestra soltanto se è osservabile per tutta la sua durata. Un esito non osservabile non viene considerato un mancato riacquisto.
- Il primo acquisto osservato non coincide necessariamente con l'acquisizione del cliente. Gli acquisti precedenti all'inizio del dataset sono sconosciuti. L'assenza di CustomerID impedisce l'analisi del comportamento del cliente per quelle righe, anche quando contribuiscono alle vendite.
- Le registrazioni negative non sono automaticamente resi confermati. I collegamenti candidati richiedono lo stesso cliente, prodotto e prezzo, una data precedente e una quantità sufficiente su una singola riga positiva. Non allocano le quantità e non identificano una fattura originale certa; anche un solo candidato non costituisce un abbinamento confermato.
- L'attività delle coorti conta le fatture di acquisto ammesse dalle regole di qualità, con prezzi e quantità positivi, anche se vengono successivamente stornate. Misura l'attività di acquisto, non il fatturato trattenuto. Le regole di qualità documentano la rimozione dei duplicati esatti e l'esclusione delle righe non valide o con prezzo zero.
- Le vendite non sono utili: mancano i dati sui costi. Le osservazioni non stimano effetti causali o miglioramenti futuri del business. La fonte descrive un singolo rivenditore in un periodo storico, con molti clienti all'ingrosso; non rappresenta un riferimento generale per l'intero settore.

Consulta il [riepilogo gestionale](reports/management_summary.md), il [dizionario delle metriche](docs/metrics.md), le [regole di qualità e l'analisi di sensibilità](docs/data_quality.md), il [resoconto delle verifiche](docs/verification.md), gli [hash della fonte](docs/source_manifest.json) e la [guida per presentare il progetto a un colloquio](docs/walkthrough.md). Questi documenti di approfondimento sono in inglese.

## Struttura del codice

| File | Funzione |
|---|---|
| `src/retail/download.py` | Download della fonte UCI, estrazione del file previsto dallo ZIP e hash |
| `src/retail/clean.py` | Normalizzazione delle righe originali, rimozione dei duplicati e indicatori di qualità |
| `sql/01_models.sql` | Registrazioni con DECIMAL, fatture di acquisto, cronologia con ROW_NUMBER/LEAD e JOIN dei candidati per le righe negative |
| `sql/02_repeat.sql` | CTE e CROSS JOIN delle finestre di osservazione, conteggi condizionali e gestione del denominatore |
| `sql/03_cohorts.sql` | Griglia dei mesi, JOIN dei clienti, zeri nei mesi completi senza attività e tassi non calcolati per i periodi incompleti |
| `sql/04_sales.sql`, `sql/05_candidates.sql` | Registrazioni per paese e mese e analisi dei collegamenti candidati |
| `src/retail/validate.py` | Confronto indipendente in pandas di tutte le celle principali dei risultati |
| `src/retail/pipeline.py` | Coordinamento della pipeline, esportazione e riepilogo |
| `tests/` | Casi limite sintetici e controlli di regressione sugli aggregati del file originale |
| `web/` | HTML, CSS e JavaScript semplici, JSON aggregato e nessuna CDN |
| `reports/` | CSV verificati, JSON, riepilogo e verifica visiva |

Per esplorare una query SQL senza una CLI dedicata:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import duckdb
with duckdb.connect('data/processed/retail.duckdb', read_only=True) as con:
    print(con.execute(Path('sql/02_repeat.sql').read_text()).df().head())
PY
```

## Attribuzione e ambito

Chen, D. (2015). **Online Retail [Dataset]**. UCI Machine Learning Repository. [DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33). [Pagina originale del dataset](https://archive.ics.uci.edu/dataset/352/online%2Bretail). Licenza dei dati: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). Il progetto modifica i dati originali mediante normalizzazione, rimozione dei duplicati e aggregazione. Se condividi dati derivati, conserva l'attribuzione e indica le modifiche effettuate. UCI descrive un rivenditore del Regno Unito con molti clienti all'ingrosso; i risultati non sono generalizzabili a tutto il settore.

Questo è un progetto locale autonomo. I comandi di installazione e analisi non eseguono push, deploy o pubblicazioni.
