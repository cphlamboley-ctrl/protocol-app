import re
from typing import List, Dict, Tuple

# Catégories valides (ligne de titre)
CAT_RE = re.compile(r"^(ADULTS|U21|U18|U16|U14|MASTER)\b", re.IGNORECASE)

# Ligne podium : 1/2/3 + au moins un espace + première lettre (nom qui suit)
RANK_START_RE = re.compile(r"^[123]\s+[A-Za-zÀ-ÖØ-öø-ÿ]")

# Variante "large" : rank + corps + (IOC optionnel)
LINE_CORE_RE = re.compile(r"^(?P<rank>[123])\s+(?P<body>.+?)(?:\s+(?P<ioc>[A-Z]{3}))?\s*$")

# Aide au nettoyage
MULTI_SPACE_RE = re.compile(r"\s{2,}")
SLASH_RE = re.compile(r"\s*/\s*")
IOC_AT_END_RE = re.compile(r"\b([A-Z]{3})\b$")


def _clean_name(text: str) -> str:
    """Nettoie le nom (espaces multiples, slashs) sans changer la casse."""
    text = MULTI_SPACE_RE.sub(" ", text.strip())
    text = SLASH_RE.sub(" / ", text)
    return " ".join(text.split())


def _parse_medalist_line(line: str):
    """
    Retourne (record_dict | {}, had_ioc: bool).
    record_dict = {"rank":int, "name":str, "nation":str}
    had_ioc = True si un IOC AAA était présent, False sinon.
    """
    m = LINE_CORE_RE.match(line)
    if m:
        try:
            rank = int(m.group("rank"))
        except Exception:
            return {}, False
        body = _clean_name(m.group("body") or "")
        if not body or not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ]", body):
            return {}, False
        ioc = (m.group("ioc") or "").strip()
        return {"rank": rank, "name": body, "nation": ioc}, bool(ioc)

    # Fallback (colonnes irrégulières)
    parts = re.split(r"\s{2,}|\t", line.strip())
    if not parts:
        return {}, False

    first = parts[0]
    if not first or first[0] not in "123":
        return {}, False

    # Tenter IOC à la toute fin (optionnel)
    ioc = ""
    m_ioc = IOC_AT_END_RE.search(line)
    if m_ioc:
        ioc = m_ioc.group(1)

    # Retirer l'IOC final du body si présent
    body = line.strip()
    if ioc:
        body = re.sub(rf"\s+{ioc}\s*$", "", body)

    # Retirer le rang initial
    body = re.sub(r"^[123]\s+", "", body).strip()
    body = _clean_name(body)

    if not body or not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ]", body):
        return {}, False

    try:
        rank = int(first.strip()[0])
    except Exception:
        return {}, False

    return {"rank": rank, "name": body, "nation": ioc}, bool(ioc)


def parse_results_txt_with_stats(content: str) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Parse un export JJIF et renvoie (categories, stats)
      categories: [{"title": "...", "medalists":[{"rank":1,"name":"...","nation":"FRA"}, ...]}, ...]
      stats: {
        "lines_rank_like": <nb de lignes qui commencent par 1/2/3>,
        "ignored_invalid_after_rank": <nb ignorées car pas de lettre après le rang>,
        "imported_medalists": <nb de médaillés ajoutés>,
        "no_ioc": <nb de médaillés importés sans IOC>
      }
    Règles :
      - Catégorie: ligne commençant par ADULTS/U21/U18/U16/U14/MASTER
      - Podium: ligne commençant par 1/2/3 puis une lettre (sinon ignorée et comptée)
      - IOC en fin de ligne optionnel (nation="" si absent)
      - On ENREGISTRE la catégorie même sans médaillés
    """
    categories: List[Dict] = []
    current_cat: Dict = None
    medalists: List[Dict] = []

    stats = {
        "lines_rank_like": 0,
        "ignored_invalid_after_rank": 0,
        "imported_medalists": 0,
        "no_ioc": 0,
    }

    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Nouvelle catégorie
        if CAT_RE.match(line):
            # Flush précédente
            if current_cat is not None:
                current_cat["medalists"] = medalists
                categories.append(current_cat)
            current_cat = {"title": line.strip(), "medalists": []}
            medalists = []
            continue

        # Lignes podium
        if line and line[0] in "123":
            stats["lines_rank_like"] += 1
            if not RANK_START_RE.match(line):
                # ex: "1 (2025-...)" ou "1 / 1" -> ignorer + compter
                stats["ignored_invalid_after_rank"] += 1
                continue
            rec, had_ioc = _parse_medalist_line(line)
            if rec:
                medalists.append(rec)
                stats["imported_medalists"] += 1
                if not had_ioc:
                    stats["no_ioc"] += 1
            else:
                # échec de parsing malgré le préfiltre
                stats["ignored_invalid_after_rank"] += 1
            continue

        # Autres -> ignorées

    # Dernière catégorie (même si 0 médaillés)
    if current_cat is not None:
        current_cat["medalists"] = medalists
        categories.append(current_cat)

    return categories, stats


# Compat: ancienne signature (sans stats)
def parse_results_txt(content: str) -> List[Dict]:
    cats, _ = parse_results_txt_with_stats(content)
    return cats
