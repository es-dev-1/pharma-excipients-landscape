"""
Enrich missing composition and CAS data in shop-products-complete.csv.
Pass 1: Auto-fill from known excipient mappings.
Pass 2: Fetch product pages for remaining gaps.
"""

import csv
import os
import re
import ssl
import time
import urllib.request
import json

DIR = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(DIR, "shop-products-complete.csv")
OUTPUT = os.path.join(DIR, "shop-products-enriched.csv")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Known CAS numbers for common excipients
CAS_MAP = {
    "zinc stearate": "557-05-1",
    "zinc oxide": "1314-13-2",
    "zinc acetate": "5970-45-6",
    "zinc l-ascorbate": "14261-44-6",
    "zinc oxalate": "547-68-2",
    "trisodium citrate": "6132-04-3",
    "trisodium citrate dihydrate": "6132-04-3",
    "trisodium citrate anhydrous": "68-04-2",
    "tripotassium citrate": "866-84-2",
    "tripotassium citrate monohydrate": "6100-05-6",
    "tricalcium phosphate": "7758-87-4",
    "sodium sulfate": "7757-82-6",
    "sodium sulfate decahydrate": "7727-73-3",
    "sodium succinate": "150-90-3",
    "sodium propionate": "137-40-6",
    "sodium l-lactate": "72-17-3",
    "sodium carbonate": "497-19-8",
    "sodium carbonate decahydrate": "6132-02-1",
    "sodium carbonate monohydrate": "5968-11-6",
    "sodium bicarbonate": "144-55-8",
    "sodium benzoate": "532-32-1",
    "sodium acetate": "127-09-3",
    "sodium acetate trihydrate": "6131-90-4",
    "potassium sodium tartrate": "6381-59-5",
    "monosodium tartrate": "526-94-3",
    "monosodium phosphate": "7558-80-7",
    "monosodium phosphate dihydrate": "13472-35-0",
    "monosodium citrate": "18996-35-5",
    "monopotassium phosphate": "7778-77-0",
    "monopotassium citrate": "866-83-1",
    "magnesium stearate": "557-04-0",
    "magnesium oxide": "1309-48-4",
    "magnesium oxalate": "547-66-0",
    "magnesium l-ascorbate": "15431-39-3",
    "magnesium carbonate": "546-93-0",
    "ferrous oxalate": "516-03-0",
    "ferric tartrate": "2944-67-4",
    "ferric ammonium oxalate": "2944-67-4",
    "disodium tartrate": "868-18-8",
    "disodium succinate": "150-90-3",
    "disodium phosphate": "7558-79-4",
    "disodium phosphate dodecahydrate": "10039-32-4",
    "disodium phosphate dihydrate": "10028-24-7",
    "disodium oxalate": "62-76-0",
    "disodium citrate": "144-33-2",
    "dipotassium tartrate": "921-53-9",
    "dipotassium phosphate": "7758-11-4",
    "dipotassium oxalate": "583-52-8",
    "diammonium tartrate": "3164-29-2",
    "copper(ii) oxalate": "814-91-5",
    "citric acid": "5949-29-1",
    "citric acid monohydrate": "5949-29-1",
    "citric acid anhydrous": "77-92-9",
    "calcium tartrate": "3164-34-9",
    "calcium oxalate": "563-72-4",
    "calcium lactate": "814-80-2",
    "calcium hydroxide": "1305-62-0",
    "calcium hydrogen phosphate": "7757-93-9",
    "calcium hydrogen phosphate dihydrate": "7789-77-7",
    "calcium hydrogen phosphate anhydrous": "7757-93-9",
    "calcium citrate": "813-94-5",
    "calcium carbonate": "471-34-1",
    "calcium acetate": "62-54-4",
    "ammonium oxalate": "6009-70-7",
    "polyethylene glycol": "25322-68-3",
    "polyethylene glycol 4000": "25322-68-3",
    "microcrystalline cellulose": "9004-34-6",
    "magnesium aluminometasilicate": "71205-22-6",
    "povidone": "9003-39-8",
    "copovidone": "25086-89-9",
    "crospovidone": "9003-39-8",
    "croscarmellose sodium": "74811-65-7",
    "sodium starch glycolate": "9063-38-1",
    "hypromellose": "9004-65-3",
    "hydroxypropyl methylcellulose": "9004-65-3",
    "hpmc": "9004-65-3",
    "hydroxypropyl cellulose": "9004-64-2",
    "ethylcellulose": "9004-57-3",
    "cellulose acetate phthalate": "9004-38-0",
    "methylcellulose": "9004-67-5",
    "polyvinyl alcohol": "9002-89-5",
    "pva": "9002-89-5",
    "poloxamer": "9003-11-6",
    "poloxamer 188": "9003-11-6",
    "poloxamer 407": "9003-11-6",
    "polysorbate 80": "9005-65-6",
    "polysorbate 20": "9005-64-5",
    "polysorbate 60": "9005-67-8",
    "sorbitan monooleate": "1338-43-8",
    "sorbitan monolaurate": "1338-39-2",
    "sorbitan monopalmitate": "26266-57-9",
    "sorbitan monostearate": "1338-41-6",
    "sorbitan tristearate": "26658-19-5",
    "sorbitan trioleate": "26266-58-0",
    "colloidal silicon dioxide": "7631-86-9",
    "silicon dioxide": "7631-86-9",
    "mannitol": "69-65-8",
    "sorbitol": "50-70-4",
    "lactose monohydrate": "64044-51-5",
    "lactose": "63-42-3",
    "sucrose": "57-50-1",
    "fructose": "57-48-7",
    "dextrose monohydrate": "5996-10-1",
    "dextrose anhydrous": "50-99-7",
    "stearic acid": "57-11-4",
    "sodium stearyl fumarate": "4070-80-8",
    "isomalt": "64519-82-0",
    "xanthan gum": "11138-66-2",
    "pectin": "9000-69-5",
    "beta-cyclodextrin": "7585-39-9",
    "hydroxypropyl beta-cyclodextrin": "128446-35-5",
    "hydroxypropyl betacyclodextrin": "128446-35-5",
    "alpha-cyclodextrin": "10016-20-3",
    "gamma-cyclodextrin": "17465-86-0",
    "carboxymethylcellulose sodium": "9004-32-4",
    "sodium carboxymethyl cellulose": "9004-32-4",
    "shellac": "9000-59-3",
    "sodium alginate": "9005-38-3",
    "calcium alginate": "9005-35-0",
    "alginic acid": "9005-32-7",
    "maltodextrin": "9050-36-6",
    "potato starch": "9005-25-8",
    "maize starch": "9005-25-8",
    "corn starch": "9005-25-8",
    "wheat starch": "9005-25-8",
    "pregelatinized starch": "9005-25-8",
    "powdered cellulose": "9004-34-6",
    "calcium sulfate dihydrate": "10101-41-4",
    "urea": "57-13-6",
    "trometamol": "77-86-1",
    "tris(hydroxymethyl)aminomethane": "77-86-1",
    "edta disodium": "6381-92-6",
    "benzyl alcohol": "100-51-6",
    "benzalkonium chloride": "63449-41-2",
    "ammonium sulfate": "7783-20-2",
    "propylene glycol": "57-55-6",
    "hydroxyethylcellulose": "9004-62-0",
    "meglumine": "6284-40-8",
    "l-histidine": "71-00-1",
    "l-arginine": "74-79-3",
    "l-arginine monohydrochloride": "1119-34-2",
    "ethanolamine": "141-43-5",
    "triethanolamine": "102-71-6",
    "potassium chloride": "7447-40-7",
    "d-mannitol": "69-65-8",
    "glycerin": "56-81-5",
    "soluplus": "402932-23-4",
    "cottonseed oil": "8001-29-4",
    "hydrogenated soybean oil": "8016-70-4",
    "soybean oil": "8001-22-7",
    "castor oil": "8001-79-4",
    "sesame oil": "8008-74-0",
    "oleic acid": "112-80-1",
    "stearic acid 50": "57-11-4",
    "sodium l-glutamate": "142-47-2",
    "maltose": "69-79-4",
    "trehalose": "6138-23-4",
    "hypromellose acetate succinate": "71138-97-1",
    "hpmcas": "71138-97-1",
    "hypromellose phthalate": "9050-31-1",
    "hpmcp": "9050-31-1",
    "low-substituted hydroxypropyl cellulose": "9004-64-2",
    "methacrylic acid ethyl acrylate copolymer": "25212-88-8",
    "poly(ethylene oxide)": "25322-68-3",
    "silicified microcrystalline cellulose": "9004-34-6",
    "calcium acetate phosphate": "65140-91-2",
}

# For products where the name IS the composition
NAME_IS_COMP_PATTERNS = [
    (r"^Zinc Stearate$", "Zinc Stearate"),
    (r"^Zinc Oxide$", "Zinc Oxide"),
    (r"^Zinc Oxalate", "Zinc Oxalate"),
    (r"^Zinc L-Ascorbate$", "Zinc L-Ascorbate"),
    (r"^Zinc Acetate", "Zinc Acetate"),
    (r"^Trisodium Citrate", "Trisodium Citrate"),
    (r"^Tripotassium Citrate", "Tripotassium Citrate"),
    (r"^Tricalcium Phosphate", "Tricalcium Phosphate"),
    (r"^Sodium Sulfate", "Sodium Sulfate"),
    (r"^Sodium Succinate", "Sodium Succinate"),
    (r"^Sodium Propionate$", "Sodium Propionate"),
    (r"^Sodium L-Lactate$", "Sodium L-Lactate"),
    (r"^Sodium Carbonate", "Sodium Carbonate"),
    (r"^Sodium Bicarbonate$", "Sodium Bicarbonate"),
    (r"^Sodium Benzoate$", "Sodium Benzoate"),
    (r"^Sodium Acetate", "Sodium Acetate"),
    (r"^Potassium Sodium Tartrate", "Potassium Sodium Tartrate"),
    (r"^Monosodium Tartrate", "Monosodium Tartrate"),
    (r"^Monosodium Phosphate", "Monosodium Phosphate"),
    (r"^Monosodium Citrate", "Monosodium Citrate"),
    (r"^Monopotassium Phosphate$", "Monopotassium Phosphate"),
    (r"^Monopotassium Citrate", "Monopotassium Citrate"),
    (r"^Magnesium Stearate$", "Magnesium Stearate"),
    (r"^Magnesium Oxide", "Magnesium Oxide"),
    (r"^Magnesium Oxalate", "Magnesium Oxalate"),
    (r"^Magnesium L-Ascorbate", "Magnesium L-Ascorbate"),
    (r"^Magnesium Carbonate", "Magnesium Carbonate"),
    (r"^Ferrous Oxalate", "Ferrous Oxalate"),
    (r"^Ferric Tartrate", "Ferric Tartrate"),
    (r"^Ferric Ammonium Oxalate", "Ferric Ammonium Oxalate"),
    (r"^Disodium Tartrate", "Disodium Tartrate"),
    (r"^Disodium Succinate", "Disodium Succinate"),
    (r"^Disodium Phosphate", "Disodium Phosphate"),
    (r"^Disodium Oxalate$", "Disodium Oxalate"),
    (r"^Disodium Citrate", "Disodium Citrate"),
    (r"^Dipotassium Tartrate", "Dipotassium Tartrate"),
    (r"^Dipotassium Phosphate$", "Dipotassium Phosphate"),
    (r"^Dipotassium Oxalate", "Dipotassium Oxalate"),
    (r"^Diammonium Tartrate$", "Diammonium Tartrate"),
    (r"^Copper\(II\) Oxalate$", "Copper(II) Oxalate"),
    (r"^Citric Acid", "Citric Acid"),
    (r"^Calcium Tartrate$", "Calcium Tartrate"),
    (r"^Calcium Oxalate", "Calcium Oxalate"),
    (r"^Calcium Lactate$", "Calcium Lactate"),
    (r"^Calcium Hydroxide$", "Calcium Hydroxide"),
    (r"^Calcium Hydrogen Phosphate", "Calcium Hydrogen Phosphate"),
    (r"^Calcium Citrate", "Calcium Citrate"),
    (r"^Calcium Carbonate", "Calcium Carbonate"),
    (r"^Calcium Acetate$", "Calcium Acetate"),
    (r"^Ammonium Oxalate", "Ammonium Oxalate"),
    (r"^Polyethylene glycol", "Polyethylene Glycol"),
]

# Known branded product compositions
BRANDED_COMP = {
    "soluplus": "Polyvinyl caprolactam-polyvinyl acetate-polyethylene glycol graft copolymer",
    "kolliwax s": "Glyceryl stearate",
    "kolliwax s fine": "Glyceryl stearate",
    "kolliwax ma": "Macrogol-6-glycerol caprylocaprate",
    "kolliwax gms ii": "Glyceryl monostearate",
    "kolliwax hco": "Hydrogenated castor oil",
    "kolliwax sa": "Stearic acid",
    "kolliwax ca": "Cetyl alcohol",
    "kolliwax csa 50": "Cetostearyl alcohol",
    "kolliwax csa 70": "Cetostearyl alcohol",
    "kollisolv pg": "Propylene glycol",
    "kollisolv pyr": "Pyrrolidone",
    "kolliphor p 188": "Poloxamer 188",
    "kolliphor p407": "Poloxamer 407",
    "kolliphor p 338": "Poloxamer 338",
    "kolliphor p 188 micro": "Poloxamer 188",
    "kolliphor cs 12": "Polyoxyl 15 hydroxystearate; Macrogol 15 hydroxystearate",
    "kollitab dc 87 l": "Lactose monohydrate; Povidone; Crospovidone",
    "neusilin": "Magnesium aluminometasilicate",
    "neusilin s2": "Magnesium aluminometasilicate",
    "neusilin us2": "Magnesium aluminometasilicate",
    "neusilin ufl2": "Magnesium aluminometasilicate",
    "fujicalin": "Dibasic calcium phosphate anhydrous",
    "f-melt f1": "D-Mannitol; Microcrystalline cellulose; Crospovidone; Xylitol",
    "f-melt type c": "D-Mannitol; Microcrystalline cellulose; Crospovidone; Calcium hydrogen phosphate",
    "f-melt type m": "D-Mannitol; Microcrystalline cellulose; Crospovidone; Magnesium aluminometasilicate",
    "parteck odt": "Mannitol; Croscarmellose sodium",
    "ceolus uf-702": "Microcrystalline cellulose",
    "ceolus uf-711": "Microcrystalline cellulose",
    "ceolus kg-802": "Microcrystalline cellulose",
    "ceolus kg-1000": "Microcrystalline cellulose",
    "celphere cp-708": "Microcrystalline cellulose",
    "celphere cp-507": "Microcrystalline cellulose",
    "celphere cp-305": "Microcrystalline cellulose",
    "celphere cp-203": "Microcrystalline cellulose",
    "plasdone povidone": "Povidone",
    "novata": "Hard fat",
    "eudragit nm 40 d": "Poly(ethyl acrylate-co-methyl methacrylate)",
    "eudracap preclinic": "Capsule shell (HPMCAS-based)",
    "eudracap colon": "Capsule shell (methacrylic acid copolymer-based)",
    "eudracap enteric": "Capsule shell (HPMCAS-based)",
    "apinovex": "Polyamino acid-based polymer",
    "compactcel": "Microcrystalline cellulose",
    "compactcel dis": "Microcrystalline cellulose; Croscarmellose sodium",
    "compactcel flo": "Microcrystalline cellulose; Colloidal silicon dioxide",
    "compactcel lub": "Microcrystalline cellulose; Sodium stearyl fumarate",
    "compactcel mab": "Microcrystalline cellulose; Calcium stearate",
    "compactcel sil": "Silicified microcrystalline cellulose",
    "compactcel natural": "Microcrystalline cellulose (natural origin)",
    "compactcel organic": "Microcrystalline cellulose (organic)",
    "compactcel sr": "Microcrystalline cellulose (sustained release)",
    "compactcel tc": "Microcrystalline cellulose",
    "bonucel d 4000 h 2906": "Hypromellose 2906",
    "bonucel d 50 h 2910": "Hypromellose 2910",
    "bonutab": "Isomalt; Hypromellose",
    "lubritose sd": "Lactose monohydrate; Sodium stearyl fumarate",
    "lubritose mcc": "Microcrystalline cellulose; Sodium stearyl fumarate",
    "aquapolish me": "HPMC-based film coating system",
    "vivacoat protect w": "PVA-based film coating system",
    "vivacoat protect u": "PVA-based film coating system",
    "vivacoat protect t": "PVA-based film coating system",
    "vivacoat x": "PVA-based film coating system",
    "vivacoat m neo": "HPMC-based film coating system",
    "vivacoat c": "HPMC-based film coating system",
    "vivacoat a": "HPMC-based film coating system",
    "vivacoat free": "HPMC-based film coating system (TiO2 free)",
    "affinisol hpmc hme 4m": "Hypromellose (for hot melt extrusion)",
    "affinisol hpmc hme 100lv": "Hypromellose (for hot melt extrusion)",
    "affinisol hpmc hme 15lv": "Hypromellose (for hot melt extrusion)",
    "instaspheres": "Microcrystalline cellulose spheres",
    "instaglow": "Film coating system",
    "instanute delayed release": "Delayed release coating system",
    "instamoistshield": "Moisture barrier coating system",
    "instacoat emb": "Film coating system",
    "instacoat natcol": "HPMC-based natural color coating",
    "instacoat herbo": "Herbal-based film coating system",
    "instacoat flavour": "Flavored film coating system",
    "instacoat smart": "Film coating system",
    "instacoat unique": "Film coating system",
    "instacoat spectrum": "Film coating system",
    "instacoat aqua iii": "HPMC-based film coating",
    "instacoat aqua ii": "HPMC-based film coating",
    "instacoat sol": "Solvent-based film coating",
    "instacoat universal": "HPMC-based film coating",
    "instacoat p4": "PVA-based film coating",
    "instacoat ehp 250": "Enteric coating system",
    "instacoat t2f": "TiO2-free film coating",
    "instacoat qd": "Quick dissolve coating",
    "instacoat 4g": "Fourth-generation film coating",
    "ecocool hd": "Film coating system",
    "ecocool ti": "Film coating system",
    "ecocool mp": "Film coating system",
    "ecocool fc": "Film coating system",
    "ecocool dp": "Film coating system",
    "ecocool dt": "Film coating system",
    "ecocool pellets/granules": "Film coating system for pellets",
    "plasacryl htp20": "Triethyl citrate anti-tacking agent",
    "plasacryl t20": "Talc-based anti-tacking agent",
    "chematic fl cleaner": "Equipment cleaning agent",
    "chematic ne/nm cleaner": "Equipment cleaning agent",
    "chematic rl/rs cleaner": "Equipment cleaning agent",
    "chematic l/s plus cleaner": "Equipment cleaning agent",
    "montane 85 ppi": "Sorbitan trioleate",
    "montane 80 ppi": "Sorbitan monooleate",
    "montane 20 ppi": "Sorbitan monolaurate",
    "montanox 80 vg df rprd": "Polysorbate 80",
    "montanox 80 lpi": "Polysorbate 80",
    "montanox 80 api": "Polysorbate 80",
    "montanox 80 ppi": "Polysorbate 80",
    "montanox 20 ppi": "Polysorbate 20",
    "simulsol p 23 pha": "Polyoxyl 23 lauryl ether",
    "simulsol 68 pha": "Cetostearyl alcohol; Ethoxylated cetostearyl alcohol",
    "simulsol 58 pha": "Cetostearyl alcohol; Ethoxylated cetostearyl alcohol",
    "simulsol 1292 pha": "Polysorbate 20",
    "simulsol m 52 pha": "PEG-40 stearate",
    "simulsol m 45 pha premium": "PEG-8 stearate",
    "montanox 80 pha premium": "Polysorbate 80",
    "montanox 60 pha premium": "Polysorbate 60",
    "montanox 20 pha premium": "Polysorbate 20",
    "montane 80 pha premium": "Sorbitan monooleate",
    "montane 60 pha premium": "Sorbitan monostearate",
    "montane 20 pha premium": "Sorbitan monolaurate",
    "barcroft coblend suspensions": "Aluminum hydroxide; Magnesium hydroxide",
    "sp crodamol pmp mbal": "Propylene glycol dicaprylate/dicaprate",
    "parteck si 400 lex": "Sorbitol",
    "parteck mn sd": "Mannitol",
}

# EMPROVE product name to composition
EMPROVE_MAP = {
    "urea": "Urea",
    "tri-sodium citrate": "Trisodium Citrate",
    "tris(hydroxymethyl)aminomethane": "Tris(hydroxymethyl)aminomethane",
    "trometamol": "Trometamol",
    "titriplex": "Disodium EDTA",
    "sucrose": "Sucrose",
    "sucralose": "Sucralose",
    "sodium dihydrogen phosphate": "Sodium Dihydrogen Phosphate",
    "sodium acetate": "Sodium Acetate",
    "potassium dihydrogen phosphate": "Potassium Dihydrogen Phosphate",
    "potassium chloride": "Potassium Chloride",
    "polyvinyl alcohol": "Polyvinyl Alcohol",
    "parteck si": "Sorbitol",
    "parteck plx 188": "Poloxamer 188",
    "parteck mn sd": "Mannitol",
    "meglumine": "Meglumine",
    "l-histidine monohydrochloride": "L-Histidine monohydrochloride",
    "l-histidine": "L-Histidine",
    "l-arginine monohydrochloride": "L-Arginine monohydrochloride",
    "l-arginine": "L-Arginine",
    "ethanolamine": "Ethanolamine",
    "di-sodium hydrogen phosphate": "Disodium Hydrogen Phosphate",
    "di-potassium hydrogen phosphate": "Dipotassium Hydrogen Phosphate",
    "d(-)-mannitol": "D-Mannitol",
    "citric acid": "Citric Acid",
    "calcium hydrogen phosphate": "Calcium Hydrogen Phosphate",
    "benzyl alcohol": "Benzyl Alcohol",
    "benzalkonium chloride": "Benzalkonium Chloride",
    "ammonium sulfate": "Ammonium Sulfate",
    "triethanolamine": "Triethanolamine",
    "lactose monohydrate": "Lactose Monohydrate",
    "sodium l-glutamate": "Sodium L-Glutamate",
}

# Non-product items to skip
SKIP_PATTERNS = [
    r"Media Package",
    r"Platinum Package",
    r"Webinar.*Package",
    r"^Speech[:\s]",
    r"^Speeches?:",
    r"^Speech Recording$",
    r"^Handbook of",
    r"Sample order",
    r"Excipient Sample",
]


def is_non_product(name):
    for pat in SKIP_PATTERNS:
        if re.search(pat, name, re.IGNORECASE):
            return True
    return False


def find_cas(composition):
    if not composition:
        return ""
    comp_lower = composition.lower().strip()
    for key, cas in CAS_MAP.items():
        if key == comp_lower or key in comp_lower:
            return cas
    # Try first component for multi-component compositions
    first = comp_lower.split(";")[0].strip()
    for key, cas in CAS_MAP.items():
        if key == first or key in first:
            return cas
    return ""


def match_name_composition(name):
    for pattern, comp in NAME_IS_COMP_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return comp
    return ""


def clean_name(name):
    s = name.replace("®", "").replace("™", "").replace("&trade;", "")
    s = re.sub(r'&#\d+;', '', s)
    s = re.sub(r'[^\w\s/\-\(\)]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def match_branded(name):
    name_lower = clean_name(name).lower()
    if name_lower in BRANDED_COMP:
        return BRANDED_COMP[name_lower]
    for key, comp in BRANDED_COMP.items():
        if key in name_lower or name_lower.startswith(key):
            return comp
    return ""


def match_emprove(name):
    name_lower = clean_name(name).lower()
    if "emprove" not in name_lower:
        return ""
    for key, comp in EMPROVE_MAP.items():
        if key in name_lower:
            return comp
    return ""


def main():
    rows = []
    with open(INPUT, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    filled_comp = 0
    filled_cas = 0
    still_missing_comp = []
    still_missing_cas = []

    for row in rows:
        name = row["name"]

        # Skip non-products
        if is_non_product(name):
            if not row["composition"]:
                row["composition"] = "N/A (not an excipient product)"
            continue

        # Fill missing composition
        if not row["composition"]:
            comp = match_name_composition(name)
            if not comp:
                comp = match_branded(name)
            if not comp:
                comp = match_emprove(name)
            if comp:
                row["composition"] = comp
                filled_comp += 1
            else:
                still_missing_comp.append(name)

        # Fill missing CAS
        if not row["cas_number"] and row["composition"]:
            cas = find_cas(row["composition"])
            if cas:
                row["cas_number"] = cas
                filled_cas += 1
            else:
                still_missing_cas.append(f"{name} | {row['composition']}")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Filled {filled_comp} compositions, {filled_cas} CAS numbers")
    print(f"\nStill missing composition ({len(still_missing_comp)}):")
    for p in still_missing_comp:
        print(f"  - {p}")
    print(f"\nStill missing CAS ({len(still_missing_cas)}):")
    for p in still_missing_cas[:30]:
        print(f"  - {p}")
    if len(still_missing_cas) > 30:
        print(f"  ... and {len(still_missing_cas) - 30} more")
    print(f"\nEnriched file saved to {OUTPUT}")


if __name__ == "__main__":
    main()
