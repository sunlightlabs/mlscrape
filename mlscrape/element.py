import requests, re, urlparse, uuid, copy, html2text, itertools
import url as moz_url
from lxml import etree
from collections import defaultdict
from tgrocery import Grocery

whitespace = re.compile('\s+')
NONE_LABEL = "__NONE__"

def _element_features(item):
    features = set()
    features.add("tag-%s" % item.tag)
        
    if 'class' in item.attrib and item.attrib['class'].strip():
        classes = whitespace.split(item.attrib['class'])
        for _c in classes:
            c = _c.strip()
            if c:
                features.add("class-%s" % c)

    if 'id' in item.attrib:
        features.add("id-%s" % item.attrib['id'])

    return features

def _walk_down(node, desc_features, page_features):
    node_id = str(uuid.uuid4())
    node.attrib['node-uuid'] = node_id

    features = _element_features(node)
    pos_features = set(['pos-%s' % len(list(node.itersiblings(preceding=True)))])
    
    child_desc_features = set([(1, f) for f in features.union(pos_features)]).union(set((i + 1, f) for i, f in desc_features))

    anc_features = set()
    for child in node.iterchildren(tag=etree.Element):
        child_anc_features = _walk_down(child, child_desc_features, page_features)
        anc_features = anc_features.union(child_anc_features)

    page_features['base'][node_id] = features
    page_features['desc'][node_id] = desc_features
    page_features['anc'][node_id] = anc_features
    page_features['pos'][node_id] = pos_features

    return set([(1, f) for f in features]).union(set((i + 1, f) for i, f in anc_features))

def _features_for_node(node, page_features):
    node_id = node.attrib['node-uuid']
    node_features = list(page_features['base'].get(node_id, [])) +\
        list(page_features['pos'].get(node_id, [])) +\
        ["desc-%s-%s" % (i, f) for i, f in page_features['desc'].get(node_id, [])] +\
        ["anc-%s-%s" % (i, f) for i, f in page_features['anc'].get(node_id, [])]
    return node_features

def _response_to_features(response, xpaths_and_labels=None):
    tree = etree.HTML(response.text)
    
    if xpaths_and_labels:
        for xpath, label in xpaths_and_labels:
            tree.xpath(xpath)[0].attrib['node-label'] = label

    page_features = {
        'base': {},
        'anc': {},
        'desc': {},
        'pos': {},
    }

    _walk_down(tree, set(), page_features)

    out = []
    for node in tree.iter(tag=etree.Element):
        node_out = {'features': _features_for_node(node, page_features), 'node': node, 'url': response.url}
        if xpaths_and_labels:
            node_out['label'] = node.attrib.get('node-label', NONE_LABEL)

        out.append(node_out)

    return out

class ElementClassifier(Grocery):
    def __init__(self, name):
        super(ElementClassifier, self).__init__(name, custom_tokenize=lambda x: x.split(" "))
        self._training_data = []

    def add_page(self, response, xpaths_and_labels):
        features_list = _response_to_features(response, xpaths_and_labels)
        self._training_data += features_list

    def train(self):
        super(ElementClassifier, self).train([(node['label'], " ".join(node['features'])) for node in self._training_data])

    def extract(self, response, format="text"):
        out_data = defaultdict(list)

        features_list = _response_to_features(response)

        for node in features_list:
            prediction = str(self.predict(" ".join(node['features'])))
            if prediction != NONE_LABEL:
                if format == "text":
                    text =  html2text.html2text(etree.tostring(node['node'])).strip()
                else:
                    # strip the stuff we've tacked onto the dom
                    element = copy.deepcopy(node['node'])
                    for child in element.iter(tag=etree.Element):
                        child.attrib.pop('node-label', None)
                        child.attrib.pop('node-uuid', None)

                    # do the equivalent of an innerHTML operation
                    text = stringify_children(element)
                if text:
                    out_data[prediction].append(text)

        return out_data

    # this is a bit of a hack for testing on train
    def test_xpaths(self, response, xpaths_and_labels):
        out_data = []

        features_list = _response_to_features(response, xpaths_and_labels)

        for node in features_list:
            prediction = str(self.predict(" ".join(node['features'])))
            if prediction != NONE_LABEL or node['node'].attrib.get('node-label', NONE_LABEL) != NONE_LABEL:
                text =  html2text.html2text(etree.tostring(node['node'])).strip()
                out_data.append({
                    'url': response.url,
                    'expected_label': node['node'].attrib.get('node-label', None),
                    'got_label': None if prediction == NONE_LABEL else prediction,
                    'element': node['node']
                })

        return out_data

# from http://stackoverflow.com/questions/4624062/get-all-text-inside-a-tag-in-lxml
def stringify_children(node):
    parts = ([node.text] +
            list(itertools.chain(*([c.text, etree.tostring(c), c.tail] for c in node.getchildren()))) +
            [node.tail])
    # filter removes possible Nones in texts and tails
    return ''.join(filter(None, parts))