import requests, re, urlparse
import url as moz_url
from lxml import etree
from tgrocery import Grocery

whitespace = re.compile('\s+')

def _response_to_features(response):
    features = set()
    tree = etree.HTML(response.text)

    for item in tree.iter(tag=etree.Element):
        features.add("tag-%s" % item.tag)
        
        if 'class' in item.attrib and item.attrib['class'].strip():
            classes = whitespace.split(item.attrib['class'])
            for _c in classes:
                c = _c.strip()
                if c:
                    features.add("class-%s" % c)

        if 'id' in item.attrib:
            features.add("id-%s" % item.attrib['id'])

    # path parts
    u = moz_url.parse(response.url)
    path = u._path.split("/")[1:]
    for idx, part in enumerate(path):
        features.add('path-%s-%s' % (idx, path))

    if u._query:
        for k, vl in urlparse.parse_qs(u._query).iteritems():
            features.add('qse-%s' % k)
            for v in vl:
                features.add('qsv-%s-%s' % (k, v))

    return features

class PageClassifier(Grocery):
    def __init__(self, name):
        super(PageClassifier, self).__init__(name, custom_tokenize=lambda x: x.split(" "))
        self._training_data = []

    def add_page(self, response, label):
        features = _response_to_features(response)
        self._training_data.append({'url': response.url, 'features': features, 'label': label})

    def train(self):
        super(PageClassifier, self).train([(page['label'], " ".join(page['features'])) for page in self._training_data])

    def predict(self, response):
        features = _response_to_features(response)
        return super(PageClassifier, self).predict(" ".join(features))