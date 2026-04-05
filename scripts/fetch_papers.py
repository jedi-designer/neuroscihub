#!/usr/bin/env python3
"""
NeuroSciHub — 週次論文自動収集スクリプト (本番版)
==================================================
毎週土曜 09:00 JST に GitHub Actions から自動実行。

使用API（すべて無料）:
  1. PubMed E-utilities  ─ メイン論文収集
  2. CrossRef API        ─ 被引用数
  3. Semantic Scholar    ─ 注目度スコア
  4. Altmetric API       ─ ニュース話題度

出力: data/papers.json
"""

import os, json, time, datetime, hashlib, requests
from pathlib import Path
from xml.etree import ElementTree as ET

# ─────────────────────────────────────────────────────
# 設定
# ─────────────────────────────────────────────────────
PUBMED_API_KEY = os.environ.get("PUBMED_API_KEY", "")
S2_API_KEY     = os.environ.get("S2_API_KEY", "")
CONTACT_EMAIL  = os.environ.get("CONTACT_EMAIL", "contact@neuroscihub.jp")

OUTPUT_PATH    = Path(__file__).parent.parent / "data" / "papers.json"
DAYS_BACK      = 8          # 過去8日分を新着として取得（土→土で確実にカバー）
MAX_PER_QUERY  = 12         # 1クエリあたり最大取得数
POPULAR_MIN_CITATIONS = 10  # popular判定の引用数閾値
POPULAR_MIN_ALTMETRIC = 30  # popular判定のAltmetricスコア閾値
ARCHIVE_KEEP   = 40         # アーカイブ保持数（分野ごと）
NEW_KEEP       = 8          # new列の最大表示数
POPULAR_KEEP   = 8          # popular列の最大表示数

BASE_PUBMED    = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
BASE_CROSSREF  = "https://api.crossref.org/works"
BASE_S2        = "https://api.semanticscholar.org/graph/v1/paper"
BASE_ALTMETRIC = "https://api.altmetric.com/v1"

EV_ORDER = {"1a": 0, "1b": 1, "2": 2, "3": 3}

# ─────────────────────────────────────────────────────
# 検索クエリ定義
# ─────────────────────────────────────────────────────
SEARCH_QUERIES = {
    "ns": {
        "label": "脳神経外科",
        "subcats": {
            "stroke": (
                '("stroke"[MeSH] OR "cerebral infarction"[MeSH] OR '
                '"intracranial hemorrhage"[MeSH]) AND '
                '("surgery"[TW] OR "surgical"[TW] OR "thrombectomy"[TW]) AND '
                '("Randomized Controlled Trial"[PT] OR "systematic review"[PT] OR '
                '"meta-analysis"[PT] OR "cohort"[TW] OR "prospective"[TW])'
            ),
            "endo": (
                '("endovascular"[TW] OR "thrombectomy"[TW] OR "coil embolization"[TW] OR '
                '"flow diverter"[TW] OR "stent retriever"[TW]) AND '
                '("intracranial"[TW] OR "cerebral"[TW] OR "aneurysm"[MeSH] OR '
                '"arteriovenous malformation"[MeSH])'
            ),
            "tumor": (
                '("brain neoplasms"[MeSH] OR "glioma"[MeSH] OR "glioblastoma"[MeSH] OR '
                '"meningioma"[MeSH] OR "IDH"[TW]) AND '
                '("surgery"[TW] OR "resection"[TW] OR "temozolomide"[TW] OR '
                '"immunotherapy"[TW] OR "targeted therapy"[TW])'
            ),
            "skull": (
                '("skull base"[MeSH] OR "acoustic neuroma"[MeSH] OR '
                '"vestibular schwannoma"[TW] OR "cranial base"[TW] OR '
                '"pituitary"[MeSH]) AND '
                '("surgery"[TW] OR "radiosurgery"[TW] OR "gamma knife"[TW])'
            ),
            "functional": (
                '("deep brain stimulation"[MeSH] OR "DBS"[TW] OR '
                '"functional neurosurgery"[TW] OR "epilepsy surgery"[TW] OR '
                '"neuromodulation"[TW] OR "stereotactic"[TW]) AND '
                '("Parkinson"[MeSH] OR "epilepsy"[MeSH] OR "tremor"[MeSH] OR '
                '"dystonia"[MeSH])'
            ),
            "spine": (
                '("spinal stenosis"[MeSH] OR "disc herniation"[TW] OR '
                '"spine surgery"[TW] OR "vertebral"[TW] OR "myelopathy"[TW]) AND '
                '("decompression"[TW] OR "fusion"[TW] OR "laminectomy"[TW] OR '
                '"artificial disc"[TW])'
            ),
        },
    },
    "bmi": {
        "label": "BMI / BCI",
        "subcats": {
            "device": (
                '("brain-computer interface"[TW] OR "brain machine interface"[TW] OR '
                '"neural interface"[TW] OR "neuroprosthetics"[TW] OR "Neuralink"[TW] OR '
                '"BrainGate"[TW] OR "Stentrode"[TW]) AND '
                '("device"[TW] OR "implant"[TW] OR "electrode"[TW] OR "chip"[TW])'
            ),
            "eeg": (
                '("electroencephalography"[MeSH] OR "EEG"[TW]) AND '
                '("brain-computer interface"[TW] OR "BCI"[TW] OR '
                '"motor imagery"[TW] OR "neural decoding"[TW] OR '
                '"deep learning"[TW] OR "transformer"[TW])'
            ),
            "invasive": (
                '("intracortical"[TW] OR "ECoG"[TW] OR "electrocorticography"[TW] OR '
                '"Utah array"[TW] OR "microelectrode"[TW] OR "cortical implant"[TW]) AND '
                '("brain-computer interface"[TW] OR "neural decoding"[TW] OR '
                '"motor control"[TW] OR "speech decoding"[TW])'
            ),
            "noninvasive": (
                '("non-invasive"[TW] OR "noninvasive"[TW]) AND '
                '("brain-computer interface"[TW] OR "BCI"[TW]) AND '
                '("EEG"[TW] OR "fNIRS"[TW] OR "MEG"[TW] OR "fMRI"[TW] OR '
                '"transcranial"[TW])'
            ),
        },
    },
    "robot": {
        "label": "人型ロボット開発",
        "subcats": {
            "humanoid": (
                '("humanoid robot"[TW] OR "bipedal robot"[TW] OR '
                '"anthropomorphic robot"[TW] OR "Boston Dynamics"[TW] OR '
                '"Figure robot"[TW] OR "Tesla Optimus"[TW]) AND '
                '("locomotion"[TW] OR "manipulation"[TW] OR '
                '"reinforcement learning"[TW] OR "whole-body control"[TW])'
            ),
            "surgical": (
                '("surgical robot"[MeSH] OR "robotic surgery"[MeSH] OR '
                '"robot-assisted surgery"[TW] OR "da Vinci"[TW]) AND '
                '("autonomous"[TW] OR "artificial intelligence"[TW] OR '
                '"machine learning"[TW] OR "neurosurgery"[TW])'
            ),
            "rehab": (
                '("rehabilitation robot"[TW] OR "exoskeleton"[TW] OR '
                '"robotic rehabilitation"[TW] OR "HAL"[TW] OR "Lokomat"[TW]) AND '
                '("stroke"[MeSH] OR "spinal cord injury"[MeSH] OR '
                '"upper limb"[TW] OR "gait"[TW])'
            ),
        },
    },
    "ai": {
        "label": "医療AI",
        "subcats": {
            "imaging": (
                '("deep learning"[TW] OR "convolutional neural network"[TW] OR '
                '"artificial intelligence"[TW]) AND '
                '("radiology"[MeSH] OR "medical imaging"[TW] OR "CT"[TW] OR '
                '"MRI"[TW] OR "pathology"[TW]) AND '
                '("diagnosis"[TW] OR "detection"[TW] OR "segmentation"[TW])'
            ),
            "prediction": (
                '("machine learning"[MeSH] OR "deep learning"[TW] OR '
                '"neural network"[TW]) AND '
                '("prognosis"[MeSH] OR "prediction"[TW] OR "mortality"[TW]) AND '
                '("clinical"[TW] OR "ICU"[TW] OR "hospital"[TW] OR '
                '"neurosurgery"[TW] OR "stroke"[MeSH])'
            ),
            "llm": (
                '("large language model"[TW] OR "GPT"[TW] OR "ChatGPT"[TW] OR '
                '"LLM"[TW] OR "foundation model"[TW] OR "Claude"[TW]) AND '
                '("medical"[TW] OR "clinical"[TW] OR "healthcare"[TW] OR '
                '"neurology"[TW] OR "diagnosis"[TW])'
            ),
            "genomics": (
                '("artificial intelligence"[TW] OR "deep learning"[TW] OR '
                '"graph neural network"[TW]) AND '
                '("genomics"[MeSH] OR "pathology"[MeSH] OR '
                '"whole slide image"[TW] OR "digital pathology"[TW] OR '
                '"brain tumor"[TW] OR "glioma"[MeSH])'
            ),
        },
    },
}

# ─────────────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────────────
def safe_get(url, params=None, headers=None, retries=3, wait=2.0):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=25)
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                print(f"    [Rate limit] waiting {wait*(attempt+2):.0f}s...")
                time.sleep(wait * (attempt + 2))
            elif r.status_code == 404:
                return None
            else:
                print(f"    [HTTP {r.status_code}] {url[:60]}")
                time.sleep(wait)
        except requests.RequestException as e:
            print(f"    [ERR] {e} (attempt {attempt+1}/{retries})")
            time.sleep(wait)
    return None

def today_str():
    return datetime.date.today().isoformat()

def days_ago_str(n):
    return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()

def make_id(field, pmid):
    return f"{field}_{pmid}"

def next_saturday_iso():
    today = datetime.date.today()
    diff = (5 - today.weekday()) % 7 or 7
    ns = today + datetime.timedelta(days=diff)
    return f"{ns.isoformat()}T00:00:00Z"

# ─────────────────────────────────────────────────────
# 1. PubMed
# ─────────────────────────────────────────────────────
def pubmed_search(query, max_results=MAX_PER_QUERY):
    params = {
        "db": "pubmed", "term": query,
        "retmax": max_results, "retmode": "json",
        "sort": "relevance",
        "datetype": "pdat",
        "mindate": days_ago_str(DAYS_BACK),
        "maxdate": today_str(),
    }
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY
    r = safe_get(f"{BASE_PUBMED}/esearch.fcgi", params=params)
    if not r:
        return []
    try:
        return r.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []

def pubmed_fetch(pmids):
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "rettype": "abstract"}
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY
    r = safe_get(f"{BASE_PUBMED}/efetch.fcgi", params=params)
    if not r:
        return []
    results = []
    try:
        root = ET.fromstring(r.text)
    except ET.ParseError as e:
        print(f"    [XML parse error] {e}")
        return []

    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID", "").strip()
            title = (article.findtext(".//ArticleTitle") or "").strip()
            if not title or not pmid:
                continue

            # Abstract
            abstract_parts = []
            for t in article.findall(".//AbstractText"):
                label = t.get("Label", "")
                text  = (t.text or "").strip()
                if label and text:
                    abstract_parts.append(f"[{label}] {text}")
                elif text:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)
            if len(abstract) > 800:
                abstract = abstract[:800] + "…"

            # Authors
            author_els = article.findall(".//Author")
            authors = []
            for auth in author_els[:5]:
                last = auth.findtext("LastName", "")
                fore = auth.findtext("ForeName", "")
                ini  = auth.findtext("Initials", "")
                if last:
                    authors.append(f"{last} {ini or fore[0] if fore else ''}".strip())
            author_str = ", ".join(authors)
            if len(author_els) > 5:
                author_str += ", et al."

            # Journal
            journal = (
                article.findtext(".//Journal/ISOAbbreviation")
                or article.findtext(".//Journal/Title")
                or ""
            ).strip()

            # Year
            year_el = (
                article.find(".//PubDate/Year")
                or article.find(".//ArticleDate/Year")
            )
            year = int(year_el.text) if year_el is not None and year_el.text else datetime.date.today().year

            # DOI
            doi = ""
            for id_el in article.findall(".//ArticleId"):
                if id_el.get("IdType") == "doi" and id_el.text:
                    doi = id_el.text.strip()
                    break

            # Evidence level
            pub_types = [pt.text or "" for pt in article.findall(".//PublicationType")]
            ev_level = estimate_evidence(pub_types, title, abstract)

            results.append({
                "pmid": pmid, "title": title, "abstract": abstract,
                "authors": author_str, "journal": journal, "year": year,
                "doi": doi, "evLevel": ev_level,
            })
        except Exception as e:
            print(f"    [parse warn] {e}")
            continue

    return results

def estimate_evidence(pub_types, title, abstract):
    pt = " ".join(pub_types).lower()
    tx = (title + " " + abstract).lower()
    if "systematic review" in pt or "meta-analysis" in pt:
        return "1a"
    if any(k in tx for k in ["systematic review", "meta-analysis", "meta analysis"]):
        return "1a"
    if "randomized controlled trial" in pt:
        return "1b"
    if any(k in tx for k in ["randomized", "randomised", "double-blind", "placebo-controlled"]):
        return "1b"
    if any(k in tx for k in ["prospective", "cohort study", "multicenter", "multi-center"]):
        return "2"
    return "3"

# ─────────────────────────────────────────────────────
# 2. CrossRef — 被引用数
# ─────────────────────────────────────────────────────
def crossref_citations(doi):
    if not doi:
        return 0
    headers = {"User-Agent": f"NeuroSciHub/1.0 (mailto:{CONTACT_EMAIL})"}
    r = safe_get(f"{BASE_CROSSREF}/{doi}", headers=headers, wait=1.0)
    if not r:
        return 0
    try:
        return r.json().get("message", {}).get("is-referenced-by-count", 0)
    except Exception:
        return 0

# ─────────────────────────────────────────────────────
# 3. Semantic Scholar — 影響度
# ─────────────────────────────────────────────────────
def semantic_scholar(doi="", pmid=""):
    paper_id = f"DOI:{doi}" if doi else (f"PMID:{pmid}" if pmid else "")
    if not paper_id:
        return {}
    headers = {}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY
    fields = "citationCount,influentialCitationCount"
    r = safe_get(f"{BASE_S2}/{paper_id}", params={"fields": fields}, headers=headers, wait=1.0)
    if not r:
        return {}
    try:
        data = r.json()
        return {
            "citations_s2":  data.get("citationCount", 0),
            "influential":   data.get("influentialCitationCount", 0),
        }
    except Exception:
        return {}

# ─────────────────────────────────────────────────────
# 4. Altmetric — ニュース話題度
# ─────────────────────────────────────────────────────
def altmetric(doi="", pmid=""):
    if doi:
        r = safe_get(f"{BASE_ALTMETRIC}/doi/{doi}", wait=1.5)
    elif pmid:
        r = safe_get(f"{BASE_ALTMETRIC}/pmid/{pmid}", wait=1.5)
    else:
        return 0, 0
    if not r:
        return 0, 0
    try:
        data = r.json()
        return float(data.get("score", 0)), int(data.get("cited_by_msm_count", 0))
    except Exception:
        return 0, 0

# ─────────────────────────────────────────────────────
# タグ付与
# ─────────────────────────────────────────────────────
def assign_tags(citations, alt_score, news_count):
    tags = ["new"]
    if alt_score >= POPULAR_MIN_ALTMETRIC or news_count >= 3:
        tags.append("hot")
    if citations >= POPULAR_MIN_CITATIONS:
        tags.append("pop")
    return tags

# ─────────────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────────────
def fetch_all():
    print(f"\n{'='*60}")
    print(f" NeuroSciHub 週次論文収集  {today_str()}")
    print(f"{'='*60}\n")

    # 既存データ読み込み
    existing = {}
    if OUTPUT_PATH.exists():
        try:
            with open(OUTPUT_PATH, encoding="utf-8") as f:
                existing = json.load(f)
            print(f"[OK] 既存データ読み込み完了")
        except Exception as e:
            print(f"[WARN] 既存データ読み込み失敗: {e}")

    new_papers  = {f: {"new": [], "popular": []} for f in SEARCH_QUERIES}
    new_archives = {f: existing.get("archives", {}).get(f, []) for f in SEARCH_QUERIES}

    total_fetched = 0

    for field_key, field_cfg in SEARCH_QUERIES.items():
        print(f"\n── {field_cfg['label']} ──────────────────────────")

        all_articles = []

        for subcat_key, query in field_cfg["subcats"].items():
            print(f"\n  [{subcat_key}] 検索中…")
            pmids = pubmed_search(query)
            print(f"    PubMed: {len(pmids)} 件")
            if not pmids:
                time.sleep(0.8)
                continue

            articles = pubmed_fetch(pmids)
            time.sleep(0.5)

            for art in articles:
                art["subcat"] = subcat_key
                art["field"]  = field_key
                art["id"]     = make_id(field_key, art["pmid"])
                all_articles.append(art)

        # 重複排除（PMID基準）
        seen_pmids = set()
        unique_articles = []
        for art in all_articles:
            if art["pmid"] not in seen_pmids:
                seen_pmids.add(art["pmid"])
                unique_articles.append(art)

        print(f"\n  重複排除後: {len(unique_articles)} 件 → 外部API取得開始")

        enriched = []
        for i, art in enumerate(unique_articles):
            print(f"    [{i+1}/{len(unique_articles)}] {art['pmid']} {art['title'][:45]}…")

            # CrossRef
            citations = crossref_citations(art["doi"])
            time.sleep(0.4)

            # Semantic Scholar
            s2 = semantic_scholar(doi=art["doi"], pmid=art["pmid"])
            citations = max(citations, s2.get("citations_s2", 0))
            influential = s2.get("influential", 0)
            time.sleep(0.4)

            # Altmetric
            alt_score, news_cnt = altmetric(doi=art["doi"], pmid=art["pmid"])
            time.sleep(0.6)

            art["citations"]   = citations
            art["altmetric"]   = round(alt_score, 1)
            art["news_count"]  = news_cnt
            art["influential"] = influential
            art["tags"]        = assign_tags(citations, alt_score, news_cnt)
            art["views"]       = 0
            art["published_date"] = today_str()
            enriched.append(art)
            total_fetched += 1

        # popular と new に振り分け（被引用数 OR Altmetric が高いものは popular）
        for art in enriched:
            if art["citations"] >= POPULAR_MIN_CITATIONS or art["altmetric"] >= POPULAR_MIN_ALTMETRIC:
                new_papers[field_key]["popular"].append(art)
            else:
                new_papers[field_key]["new"].append(art)

        # エビデンスレベル順 → 被引用数降順でソート
        for col in ["new", "popular"]:
            new_papers[field_key][col].sort(
                key=lambda p: (EV_ORDER.get(p.get("evLevel", "3"), 3), -p.get("citations", 0))
            )
            new_papers[field_key][col] = new_papers[field_key][col][:NEW_KEEP if col == "new" else POPULAR_KEEP]

        # アーカイブ更新: 前週の popular をアーカイブへ
        prev_pop = existing.get("papers", {}).get(field_key, {}).get("popular", [])
        for p in prev_pop:
            p["tags"] = [t for t in p.get("tags", []) if t != "new"]
            if not any(a["id"] == p["id"] for a in new_archives[field_key]):
                new_archives[field_key].insert(0, p)
        new_archives[field_key] = new_archives[field_key][:ARCHIVE_KEEP]

        time.sleep(1.0)

    # ─── 出力 ───────────────────────────────────────────
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "next_update":  next_saturday_iso(),
        "papers":       new_papers,
        "archives":     new_archives,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f" 完了: 合計 {total_fetched} 件収集 → data/papers.json に保存")
    print(f"{'='*60}\n")

    # サマリー表示
    for field_key in SEARCH_QUERIES:
        n = len(new_papers[field_key]["new"])
        p = len(new_papers[field_key]["popular"])
        a = len(new_archives[field_key])
        print(f"  {field_key:8s}: new={n}, popular={p}, archive={a}")

if __name__ == "__main__":
    fetch_all()
