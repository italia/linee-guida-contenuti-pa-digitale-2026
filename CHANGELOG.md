# Registro delle versioni

## 1.2 (bozza) – 18 novembre 2026

- Testo introduttivo della home (`.lead`) a 20 px, peso regolare, grigio scuro (#455b71).
- Barra laterale, card della home e menu mobile in Bootstrap Italia puro: tolti i numeri dei capitoli e tutti gli stili personalizzati dei titoli e delle voci (restano la barra fissa allo scorrimento e l’allineamento a sinistra con il breadcrumb, senza il rientro di 24 px).
- Scarica: i pulsanti di download degli MD e dello ZIP non rispondevano al clic perché li bloccava lo stile dei pulsanti d’esempio; ora lo stile vale solo per gli esempi.
- Audit di conformità a Bootstrap Italia: barra laterale con i titoli dei gruppi dentro `ul.link-list` e voci `medium`; skiplinks «Vai al contenuto principale» e «Vai al piede di pagina»; breadcrumb con separatori nascosti ai lettori di schermo e etichetta «Percorso di navigazione»; «Torna su» con `aria-label` e raggiungibile da tastiera. Corretto un difetto: il pulsante «Torna su» non scorreva in cima perché mancava l’animazione, ora lo script è la versione bundle di Bootstrap Italia.
- Sito basato su Bootstrap Italia 2.18.3, copiato in `assets/bootstrap-italia/` (nessuna risorsa esterna: i font Titillium Web e Roboto Mono, le icone e gli script si caricano dal sito stesso). Usa i componenti ufficiali: skiplinks, intestazione con fascia sottile, zona centrale e ricerca in finestra modale, menu dei capitoli a comparsa su mobile, barra laterale, breadcrumb, card, pulsanti, tabelle, footer e pulsante «Torna su». `assets/style.css` contiene solo le estensioni (tabelle Sì/No, schede impilate, impaginazione del testo).
- Revisione dai commenti sull’anteprima: principi più centrati sull’ente; Pec e comunicazioni all’ente con il “voi”, email al referente con il “tu” (sezioni 2.3 e 8.5); pagina Intelligenza artificiale senza nomi di prodotti; tooltip accessibili da tastiera; ordine dei pulsanti nella modale (Annulla prima, azione primaria dopo); campi dei menu a tendina; link alle linee guida di AGID sull’accessibilità nella checklist.
- Sezione 11.2 Governance spenta in attesa che il processo sia definito: il testo è in `content/da-riattivare/`. Il capitolo 11 si chiama «Checklist di revisione».
- Logo di PA digitale 2026, preso dal sito padigitale2026.gov.it, nell’intestazione e nel footer (`assets/logo-pa-digitale-2026.svg`).
- Tabelle su schermi stretti (fino a 600 px): le tabelle con tre o più colonne diventano schede impilate, con la semantica di tabella mantenuta tramite ruoli ARIA.
- Sito su mobile: intestazione fissa in alto con pulsanti Cerca e Capitoli, indice dei capitoli a pannello laterale (chiusura con Esc, focus gestito), ricerca comprimibile, tabelle scorrevoli con larghezza minima. Su tutti i dispositivi: pulsante «Torna su» fisso.
- Accessibilità del sito: indicatore di focus ad alto contrasto, gerarchia dei titoli corretta in «Principi» e «Fonti», tabelle scorrevoli raggiungibili da tastiera, ricerca con annuncio dei risultati e frecce direzionali, intestazioni di colonna con `scope`.
- Il testo passa su GitHub: un file per capitolo, revisione con pull request e issue.
- Tolto il capitolo "Decisioni sulle regole". La checklist e la governance diventano il capitolo 11.
- Capitolo 0.4: tra le fonti restano l’analisi del sito padigitale2026.gov.it e il confronto con le migliori pratiche internazionali, senza l’elenco di allegati e guide di stile. Nelle fonti le FAQ non citano più un tema specifico.
- Glossario: “verifiche di conformità tecnica” e “controlli formali” al posto di “Asseverazione tecnica” e “Asseverazione formale”.
- Fonti: il materiale revisionato per il Dipartimento è descritto in modo generico.
- Capitolo 8.5: nella riga "Pulsanti e link" restano solo i testi dei pulsanti.
- La pagina Pacchetto per Figma diventa Intelligenza artificiale: prima i file .md da scaricare e le istruzioni per assistenti come Claude, ChatGPT e Gemini, poi la sezione su Figma.
- I file .md si generano dal testo dei capitoli a ogni pubblicazione.
