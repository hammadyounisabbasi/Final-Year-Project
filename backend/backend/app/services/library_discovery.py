"""Live web discovery. Links are retrieved, never invented by the language model."""
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse, parse_qs, quote
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

def safe_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ('https', 'http') and bool(parsed.hostname) and not parsed.username

def fetch(url):
    req = Request(url, headers={'User-Agent': 'UniversityLibrary/1.0 (academic resource discovery)', 'Accept': 'application/json,text/html'})
    with urlopen(req, timeout=12) as response:
        return response.read(2_000_000).decode('utf-8', errors='replace')

class SearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'result__a' in attrs.get('class','').split():
            url = attrs.get('href','')
            url = parse_qs(urlparse(url).query).get('uddg', [url])[0]
            self.current = {'title': '', 'url': url, 'kind': 'Website', 'description': 'Web search result; open the source to review its content.'}
    def handle_data(self, data):
        if self.current is not None:
            self.current['title'] += data
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            if safe_url(self.current['url']):
                self.results.append(self.current)
            self.current = None

def web_results(query):
    parser = SearchParser()
    parser.feed(fetch('https://html.duckduckgo.com/html/?' + urlencode({'q': query})))
    return parser.results[:5]

def article_results(query):
    query = ' '.join(re.sub(r'\b(what|is|are|find|please|related|articles|books|about)\b', ' ', query, flags=re.I).split())
    if 'deep learning' in query.lower() and 'machine' not in query.lower():
        query += ' machine learning neural networks'
    data = json.loads(fetch('https://api.crossref.org/works?' + urlencode({'query':query,'rows':4,'filter':'type:journal-article'})))
    return [{'title': item.get('title',['Untitled article'])[0], 'url': 'https://doi.org/' + quote(item['DOI'], safe='/'),
             'kind':'Article', 'description':'Research publication indexed by Crossref. Publisher access conditions may apply.'}
            for item in data['message']['items'] if item.get('DOI') and item.get('title')]

def openalex_results(query):
    data = json.loads(fetch('https://api.openalex.org/works?' + urlencode({
        'search': query, 'per-page': 4, 'filter': 'type:article|type:review'})))
    results = []
    for item in data.get('results', []):
        title = item.get('title')
        url = item.get('doi') or item.get('primary_location', {}).get('landing_page_url')
        if title and url and safe_url(url):
            results.append({
                'title': title,
                'url': url,
                'kind': 'Research article',
                'description': 'Research publication indexed by OpenAlex. Publisher access conditions may apply.',
            })
    return results

def overview_results(query):
    clean = re.sub(r'\b(what|is|are|find|please|related|articles|books|about)\b', ' ', query, flags=re.I)
    data = json.loads(fetch('https://en.wikipedia.org/w/api.php?' + urlencode({
        'action':'opensearch','search':' '.join(clean.split()),'limit':3,'namespace':0,'format':'json'})))
    return [{'title':title,'url':url,'kind':'Overview','description':'Encyclopedia overview; follow its references for primary research.'}
            for title,url in zip(data[1],data[3]) if safe_url(url)]

def discover(query):
    sources = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(fn, query) for fn in (web_results, overview_results, article_results, openalex_results)]
        for job in jobs:
            try:
                sources.extend(job.result())
            except Exception as error:
                log.warning('Library discovery source unavailable: %s', type(error).__name__)
    unique = {item['url']:item for item in sources if safe_url(item['url'])}
    # Clearly marked search destinations remain useful even during provider outages.
    links = [{'title': title, 'url': base + quote(query), 'kind':'Search link', 'description':desc}
             for title, base, desc in [
                 ('Search Google Scholar','https://scholar.google.com/scholar?q=','Search scholarly literature for this topic.'),
                 ('Search educational videos','https://www.youtube.com/results?search_query=','Search videos and lectures for this topic.'),
                 ('Search ResearchGate','https://www.researchgate.net/search?q=','Search research publications and authors for this topic.'),
                 ('Search Google Books','https://www.google.com/search?tbm=bks&q=','Search books and previews for this topic.')]]
    return {'sources':list(unique.values())[:8], 'search_links':links,
            'search_status':'live' if unique else 'unavailable'}

