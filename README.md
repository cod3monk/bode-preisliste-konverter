# bode-preisliste-konverter
Konvertiert Preislisten von Bodenaturkost in das foodsoft csv Format.

## Installieren
1. MacPots installieren: https://distfiles.macports.org/MacPorts/MacPorts-2.3.3-10.10-Yosemite.pkg
2. In Terminal gehen und folgendes ausführen:
```
sudo ports install jruby
sudo jruby -S gem install tabula-extractor
```
## Anwendung
`./convert.py ../Bodenaturkost_Preisliste.pdf 3-45 ausgabe.csv`
