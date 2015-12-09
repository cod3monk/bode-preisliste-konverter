#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import unicsv
import codecs
import re
from pprint import pprint
import argparse
import tempfile
from functools import reduce
import operator

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg  # return file name

def extract_csv(in_file, pages, temp_csv_path):
    os.system("/opt/local/share/java/jruby/lib/ruby/gems/shared/gems/tabula-extractor-0.7.6-java/"
              "bin/tabula --columns 10,45,287,308,354,383,421,458,493,522,552 "
              "'{}' -o '{}' -p {}".format(in_file, temp_csv_path, pages))

def convert_for_foodsoft(temp_csv, mwst_kategorien={}):
    # Status (x=ausgelistet) | Bestellnummer | Name | Notiz | Produzent | Herkunft | Einheit | Nettopreis | MwSt | Pfand | Gebindegröße | (geschützt) | (geschützt) | Kategorie
    data = []
    artnr = []
    kategorien = {"Other": {'count': 0, 'mwst': 0}}
    for k,v in mwst_kategorien.items():
        kategorien[k] = {'count': 0, 'mwst': int(v)}

    reader = unicsv.UnicodeReader(temp_csv, delimiter=',', quotechar='"')
    
    kategorie = "Other"
    for row in reader:
        # Zu ignorierende Zeilen:
        if row[1].startswith(u'B O D E   N A T U R K O S T'):
            continue
        elif row == [u'', u'', u'Gro\xdf', u'gebinde', u'', u'', u'', u'', u'', u'', u'']:
            continue
        elif row == [u'Art.-Nr.', u'Artikelbezeichnung', u'', u'Gebinde', u'Einzel', u'\u20ac', u'Gebinde', u' Art.-Nr.', u'Netto\u20ac', u'Brutto\u20ac', u'']:
            continue
        elif row == [u'Art.-Nr.', u'Artikelbezeichnung', u'', u'Gebinde', u'Einzel', u'\u20ac', u'Gebinde', u' Art.-Nr.', u'Netto\u20ac', u'Brutto\u20ac']:
            continue
    
        # Testen ob es sich um eine Kategorie handelt:
        set_kat = False
        if row[2:] == [u'Klein', u'gebinde', u'', u'', u'', u'Einzelpa', u'ckunge', u'n', u'']:
            set_kat = True
        elif row[2:] == [u'', u'', u'', u'', u'', u'Einzelpa', u'ckunge', u'n']:
            set_kat = True
        elif row[2:] == [u'Klein', u'-/Gro\xdfgebin', u'de', u'', u'', u'Einzelpa', u'ckunge', u'n', u'']:
            set_kat = True
        elif row[2:] == [u'Klein', u'gebinde', u'', u'', u'', u'Einzelpa', u'ckunge', u'n']:
            set_kat = True
        elif row[2:] == [u'Klein', u'gebinde', u'', u'', u'', u'', u'', u'', u'']:
            set_kat = True
        elif row[2:] == [u'Gro\xdf', u'gebinde', u'', u'', u'', u'', u'', u'', u'']:
            set_kat = True
        elif row[2:] == [u'Gro\xdf', u'gebinde', u'', u'', u'', u'', u'', u'']:
            set_kat = True
        elif row[2:] == [u'', u'', u'', u'', u'', u'Einzelpa', u'ckunge', u'n', u'']:
            set_kat = True
        elif row == [u'Verp', u'ackungsmaterial', u'', u'', u'', u'', u'', u'', u'', u'']:
            set_kat = True
        elif row[2:] == [u' Klein', u'gebinde', u'', u'', u'', u'Einzelpa', u'ckunge', u'n', u'']:
            set_kat = True
        elif row[2:] == [u'', u'', u'', u'', u'', u'', u'', u'', u'']:
            set_kat = True
        #elif row[2:] == [u'', u'', u'', u'', u'', u'', u'']:
        #    set_kat = True
        #elif row[1:] == [u'', u'', u'', u'', u'', u'', u'', u'']:
        #    set_kat = True
        #elif row[2:] == [u'', u'', u'', u'', u'', u'', u'', u'']:
        #    set_kat = True
        if set_kat:
            possible_kategorie = (row[0]+row[1]).split(u'\u2212')[0].strip()
            if possible_kategorie:
                kategorie = possible_kategorie
                kategorien.setdefault(kategorie, {'count': 0, 'mwst': 0})
            continue
    
        # Testen ob es sich um ein Produkt handelt:
        # Erste Spalte ist fünf stellige zahl
        if not re.match(r'^[0-9]{5}$', row[0]):
            print('\tIgnoriert (0):', row)
            continue
        bestellnummer = row[0]
        # Zweite Spalte ist ein string der länge >= 3
        if not len(row[1]) >= 3: 
            print('\tIgnoriert (1):', row)
            continue
        name = row[1]
        notiz = row[2]
        # Vierte Spalte is (menge /) gewicht einheit
        if not re.match(r'^(?:[0-9,]+/)?[0-9,]+.*?$', row[3]): 
            print('\tIgnoriert (3):', row)
            continue
        if '/' in row[3]:
            gebindegroesse, einheit = row[3].split('/', 1)
            
            # wenn eine gebindegroesse 3*10 lautet, dann ausmultiplizieren
            if re.match(r'^[0-9]+\*[0-9]+$', gebindegroesse):
                gebindegroesse = str(reduce(operator.mul, map(int, gebindegroesse.split('*')), 1))
        else:
            gebindegroesse = '1'
            einheit = row[3]
        try:
            int(einheit)
            einheit += ' Stk.'
        except:
            pass
        
        # Fünfte Spalte ist einzelpreis
        if not re.match(r'^[0-9]+,[0-9]{2}', row[4]): 
            print('\tIgnoriert (4):', row)
            continue
        # Fünfte Spalte ist gebindepreis
        if not re.match(r'^[0-9]+,[0-9]{2}', row[6]): 
            print('\tIgnoriert (6):', row)
            continue
        nettopreis = row[6]
    
        # Einzelpackungen auswerten und mwst extrahieren:
        if re.match(r'^[0-9]{5}$', row[7]) and \
           re.match(r'^[0-9]+,[0-9]{2}', row[8]) and \
           re.match(r'^[0-9]+,[0-9]{2}', row[9]):
            if float(row[9].replace(',', '.'))/float(row[8].replace(',', '.')) > 1.13:
                mwst = 19
            else:
                mwst = 7
            
            # Doppelte werden ignoriert
            if row[7] not in artnr:
                data.append(['', row[7], name[:24]+' {}'.format(row[7]), notiz, '', '', einheit, row[8].replace(',', '.'), str(mwst), '0', '1', '', '', kategorie])
                artnr.append(row[7])
                kategorien[kategorie]['count'] += 1
            kategorien[kategorie]['mwst'] = mwst
        else:
            mwst = 0
    
        # Doppelte ausfiltern:
        if bestellnummer in artnr:
            continue
    
        # Basisdaten sind okay
        data.append(['', bestellnummer, name[:24]+' {}'.format(bestellnummer), notiz, '', '', einheit, nettopreis.replace(',', '.'), str(mwst), '0', gebindegroesse, '', '', kategorie])
        artnr.append(bestellnummer)
        kategorien[kategorie]['count'] += 1

    # Kategorien mwst auf alle anderen Produkte in kategorie anwenden:
    for k,v in kategorien.items():
        if v['count'] != 0:
            for d in filter(lambda d: d[-1] == k, data):
                d[8] = str(v['mwst'])
    
    return data, kategorien


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("eingabepdf",
        help="PDF mit Preisliste",
        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("pages",
        help="Seitenbereich der zu analysieren ist (z.B. 5 oder 2-64)")
    parser.add_argument("ausgabecsv",
        help="CSV mit Datei für foodsoft",
        type=argparse.FileType('w'))
    parser.add_argument("kategorien_mwst", nargs='?',
        help="Textdatei mit Kategoriennamen und MwSt.",
        type=argparse.FileType('r'))
    args = parser.parse_args()
    
    temp_csv = tempfile.NamedTemporaryFile()
    
    print('Tabula aufrufen...')
    extract_csv(args.eingabepdf, args.pages, temp_csv.name)
    
    print('Extrahieren aus pdf mittels tabula ist beendet.')
    print()
    print('MwSt. Kategorien einlesen:')
    
    mwst_kategorien = {}
    if args.kategorien_mwst:
        for l in args.kategorien_mwst.readlines():
            k, mwst = l.strip().rsplit(" ", 1)
            try:
                mwst_kategorien[k] = int(mwst)
            except:
                print("Konnte MwSt. zu Kategorie", k, "nicht verstehen. \tIgnoriert.")
    print('Einlesen beendet.')
    print()
    print('Konvertieren nach foodsoft format:')
    data, kategorien = convert_for_foodsoft(temp_csv, mwst_kategorien)
    print('Konvertierung ist beendet.')
    print()
    print('Speichere foodsoft CSV in {}...'.format(args.ausgabecsv.name))
    unicsv.UnicodeWriter(args.ausgabecsv, delimiter=';').writerows(data)
    print('gespeichert.')
    print()
    
    # Output
    print("Anzulegende Kategorien:")
    for k in kategorien:
        if kategorien[k] > 0:
            print('\t'+k)

    print()
    print("Kategorien mit unbekannter MwSt.:")
    for k in kategorien:
        if kategorien[k]['mwst'] == 0:
            print('\t'+k)
    

if __name__ == '__main__':
    main()
